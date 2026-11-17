#!/usr/bin/env python3
"""Create, encrypt, upload, verify, and retain weekly PostgreSQL backups."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any
from urllib.parse import quote, urlsplit

import requests


DEFAULT_BUCKET = "cocoscan-database-backups"
DEFAULT_RETENTION_COUNT = 12
ARCHIVE_PATTERN = re.compile(r"^cocoscan_db_weekly_\d{8}T\d{6}Z\.dump\.age$")


class BackupError(RuntimeError):
    pass


class SupabaseBackupStorage:
    def __init__(self) -> None:
        self.base_url = os.environ["SUPABASE_URL"].rstrip("/")
        self.service_key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        self.bucket = os.getenv("SUPABASE_BACKUP_BUCKET", DEFAULT_BUCKET).strip() or DEFAULT_BUCKET
        self.session = requests.Session()
        self.session.headers.update({
            "apikey": self.service_key,
            "Authorization": "Bearer " + self.service_key,
        })

    def _url(self, path: str) -> str:
        return f"{self.base_url}/storage/v1/{path}"

    def _check(self, response: requests.Response, operation: str) -> requests.Response:
        if not response.ok:
            raise BackupError(f"Supabase Storage {operation} failed (HTTP {response.status_code}).")
        return response

    def ensure_private_bucket(self) -> None:
        bucket_url = self._url(f"bucket/{quote(self.bucket, safe='')}")
        response = self.session.get(bucket_url, timeout=30)
        if response.ok:
            try:
                details = response.json()
            except ValueError as exc:
                raise BackupError("Supabase returned invalid bucket configuration.") from exc
            if details.get("public") is True:
                raise BackupError("The database backup bucket must be private.")
            return
        if response.status_code != 404:
            self._check(response, "bucket lookup")
        response = self.session.post(
            self._url("bucket"),
            json={"id": self.bucket, "name": self.bucket, "public": False},
            timeout=30,
        )
        if response.status_code == 409:
            self.ensure_private_bucket()
            return
        self._check(response, "private bucket creation")

    def upload_bytes(self, object_path: str, payload: bytes, content_type: str) -> None:
        path = quote(object_path, safe="/")
        response = self.session.post(
            self._url(f"object/{quote(self.bucket, safe='')}/{path}"),
            data=payload,
            headers={"Content-Type": content_type, "x-upsert": "true"},
            timeout=120,
        )
        self._check(response, "manifest upload")

    def upload_file(self, object_path: str, filepath: Path) -> None:
        path = quote(object_path, safe="/")
        with filepath.open("rb") as source:
            response = self.session.post(
                self._url(f"object/{quote(self.bucket, safe='')}/{path}"),
                data=source,
                headers={"Content-Type": "application/octet-stream", "x-upsert": "false"},
                timeout=(30, 1800),
            )
        self._check(response, "backup upload")

    def list_objects(self, prefix: str) -> list[dict[str, Any]]:
        objects: list[dict[str, Any]] = []
        offset = 0
        while True:
            response = self.session.post(
                self._url(f"object/list/{quote(self.bucket, safe='')}"),
                json={"prefix": prefix, "limit": 1000, "offset": offset},
                timeout=60,
            )
            self._check(response, "object listing")
            try:
                batch = response.json()
            except ValueError as exc:
                raise BackupError("Supabase returned an invalid object listing.") from exc
            if not isinstance(batch, list):
                raise BackupError("Supabase returned an invalid object listing.")
            objects.extend(item for item in batch if isinstance(item, dict))
            if len(batch) < 1000:
                return objects
            offset += len(batch)

    def delete_objects(self, object_paths: list[str]) -> None:
        if not object_paths:
            return
        response = self.session.delete(
            self._url(f"object/{quote(self.bucket, safe='')}"),
            json={"prefixes": object_paths},
            timeout=120,
        )
        self._check(response, "retention cleanup")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _run(command: list[str], description: str, env: dict[str, str] | None = None) -> None:
    result = subprocess.run(command, capture_output=True, text=True, env=env, check=False)
    if result.returncode:
        details = (result.stderr or "").strip().splitlines()
        detail = details[-1][:500] if details else "command exited unsuccessfully"
        database_url = os.getenv("SUPABASE_DB_URL", "")
        if database_url:
            detail = detail.replace(database_url, "[database URL redacted]")
        raise BackupError(f"{description} failed: {detail}")


def _sha256_file(filepath: Path) -> str:
    digest = hashlib.sha256()
    with filepath.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_status(storage: SupabaseBackupStorage, manifest: dict[str, Any]) -> None:
    storage.upload_bytes(
        "runs/latest.json",
        json.dumps(manifest, separators=(",", ":"), ensure_ascii=True).encode("utf-8"),
        "application/json",
    )


def run_backup() -> None:
    db_url = os.getenv("SUPABASE_DB_URL", "").strip()
    age_recipient = os.getenv("BACKUP_AGE_RECIPIENT", "").strip()
    started_at = _utc_now()
    stamp = started_at.strftime("%Y%m%dT%H%M%SZ")
    filename = f"cocoscan_db_weekly_{stamp}.dump.age"
    storage = SupabaseBackupStorage()
    storage.ensure_private_bucket()

    run_id = os.getenv("GITHUB_RUN_ID", "")
    repository = os.getenv("GITHUB_REPOSITORY", "")
    server_url = os.getenv("GITHUB_SERVER_URL", "https://github.com").rstrip("/")
    run_url = f"{server_url}/{repository}/actions/runs/{run_id}" if repository and run_id else ""
    manifest: dict[str, Any] = {
        "status": "running",
        "started_at": started_at.isoformat(),
        "finished_at": None,
        "archive_name": filename,
        "archive_size_bytes": None,
        "run_url": run_url,
        "error": None,
    }
    _write_status(storage, manifest)

    try:
        if not db_url or urlsplit(db_url).scheme not in {"postgres", "postgresql"}:
            raise BackupError("SUPABASE_DB_URL must be a PostgreSQL connection URI.")
        if not age_recipient.startswith("age1"):
            raise BackupError("BACKUP_AGE_RECIPIENT must be a valid age public recipient.")
        retention_count = int(os.getenv("BACKUP_RETENTION_COUNT", str(DEFAULT_RETENTION_COUNT)))
        if retention_count < 1:
            raise BackupError("BACKUP_RETENTION_COUNT must be at least 1.")

        with tempfile.TemporaryDirectory(prefix="cocoscan-backup-") as temp_dir:
            dump_path = Path(temp_dir) / "database.dump"
            encrypted_path = Path(temp_dir) / filename
            _run(
                [
                    "pg_dump",
                    "--format=custom",
                    "--no-owner",
                    "--no-acl",
                    f"--file={dump_path}",
                    f"--dbname={db_url}",
                ],
                "PostgreSQL dump",
            )
            if not dump_path.is_file() or dump_path.stat().st_size == 0:
                raise BackupError("PostgreSQL dump was empty.")
            _run(["pg_restore", "--list", str(dump_path)], "PostgreSQL dump verification")
            _run(
                [
                    "age",
                    "--encrypt",
                    "--recipient",
                    age_recipient,
                    "--output",
                    str(encrypted_path),
                    str(dump_path),
                ],
                "Backup encryption",
            )
            if not encrypted_path.is_file() or encrypted_path.stat().st_size == 0:
                raise BackupError("Encrypted backup was empty.")

            encrypted_size = encrypted_path.stat().st_size
            sha256 = _sha256_file(encrypted_path)
            object_path = f"weekly/{filename}"
            storage.upload_file(object_path, encrypted_path)

        weekly_objects = [
            item for item in storage.list_objects("weekly")
            if ARCHIVE_PATTERN.fullmatch(str(item.get("name") or ""))
        ]
        uploaded = next((item for item in weekly_objects if item.get("name") == filename), None)
        if uploaded is None:
            raise BackupError("Uploaded backup could not be verified in Supabase Storage.")
        metadata = uploaded.get("metadata") or {}
        stored_size = int(metadata.get("size") or uploaded.get("size") or 0)
        if stored_size != encrypted_size:
            raise BackupError("Uploaded backup size did not match the local encrypted archive.")

        weekly_objects.sort(key=lambda item: str(item.get("name") or ""), reverse=True)
        expired = weekly_objects[retention_count:]
        storage.delete_objects([f"weekly/{item['name']}" for item in expired])

        manifest.update({
            "status": "success",
            "finished_at": _utc_now().isoformat(),
            "archive_size_bytes": encrypted_size,
            "sha256": sha256,
            "retention_count": retention_count,
            "expired_count": len(expired),
            "error": None,
        })
        _write_status(storage, manifest)
        print(
            f"Encrypted PostgreSQL backup uploaded and verified: {filename} "
            f"({encrypted_size} bytes); retained {min(len(weekly_objects), retention_count)} archive(s)."
        )
    except Exception as exc:
        safe_error = str(exc)
        for secret_name in ("SUPABASE_DB_URL", "SUPABASE_SERVICE_ROLE_KEY"):
            secret = os.getenv(secret_name, "")
            if secret:
                safe_error = safe_error.replace(secret, "[redacted]")
        manifest.update({
            "status": "failure",
            "finished_at": _utc_now().isoformat(),
            "error": safe_error[:1000],
        })
        try:
            _write_status(storage, manifest)
        except Exception as status_exc:
            print(f"Could not persist failed backup status: {status_exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    try:
        run_backup()
    except Exception as error:
        print(f"Automated database backup failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
