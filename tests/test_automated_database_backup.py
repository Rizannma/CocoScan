import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts import automated_database_backup as backup_job


class FakeStorage:
    def __init__(self):
        self.manifests = []
        self.archive_name = None
        self.archive_size = 0
        self.deleted = []

    def ensure_private_bucket(self):
        pass

    def upload_bytes(self, object_path, payload, content_type):
        self.manifests.append((object_path, json.loads(payload)))

    def upload_file(self, object_path, filepath):
        self.archive_name = Path(object_path).name
        self.archive_size = filepath.stat().st_size

    def list_objects(self, prefix):
        if prefix == "weekly":
            older = [
                {"name": f"cocoscan_db_weekly_202611{day:02d}T160000Z.dump.age", "metadata": {"size": "100"}}
                for day in range(1, 13)
            ]
            return older + [{
                "name": self.archive_name,
                "metadata": {"size": str(self.archive_size)},
            }]
        return []

    def delete_objects(self, object_paths):
        self.deleted.extend(object_paths)


class AutomatedDatabaseBackupTests(unittest.TestCase):
    def setUp(self):
        self.env_patch = patch.dict(os.environ, {
            "SUPABASE_URL": "https://cocoscan.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "test-service-role-key",
            "SUPABASE_DB_URL": "postgresql://backup:test-password@example.com:5432/cocoscan",
            "BACKUP_AGE_RECIPIENT": "age1testrecipient",
            "BACKUP_RETENTION_COUNT": "12",
            "GITHUB_REPOSITORY": "example/cocoscan",
            "GITHUB_RUN_ID": "12345",
        })
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def test_new_secret_key_is_not_sent_as_bearer(self):
        with patch.dict(os.environ, {"SUPABASE_SERVICE_ROLE_KEY": "sb_secret_test"}):
            storage = backup_job.SupabaseBackupStorage()

        self.assertEqual(storage.session.headers["apikey"], "sb_secret_test")
        self.assertNotIn("Authorization", storage.session.headers)

    def test_storage_url_and_service_role_key_are_trimmed(self):
        with patch.dict(os.environ, {
            "SUPABASE_URL": " \r\nhttps://cocoscan.supabase.co/ \t",
            "SUPABASE_SERVICE_ROLE_KEY": " \nlegacy-jwt\r ",
        }):
            storage = backup_job.SupabaseBackupStorage()

        self.assertEqual(storage.base_url, "https://cocoscan.supabase.co")
        self.assertEqual(storage.service_key, "legacy-jwt")

    def test_legacy_service_role_key_is_sent_as_bearer(self):
        with patch.dict(os.environ, {"SUPABASE_SERVICE_ROLE_KEY": "legacy-jwt"}):
            storage = backup_job.SupabaseBackupStorage()

        self.assertEqual(storage.session.headers["apikey"], "legacy-jwt")
        self.assertEqual(storage.session.headers["Authorization"], "Bearer legacy-jwt")

    def test_database_url_is_trimmed_before_dump(self):
        storage = FakeStorage()
        db_url = "postgresql://backup:test-password@example.com:5432/cocoscan"
        with (
            patch.dict(os.environ, {"SUPABASE_DB_URL": f" \r\n{db_url} \t"}),
            patch.object(backup_job, "SupabaseBackupStorage", return_value=storage),
            patch.object(backup_job, "_run", side_effect=self._fake_command) as run,
        ):
            backup_job.run_backup()

        dump_command = run.call_args_list[0].args[0]
        self.assertIn(f"--dbname={db_url}", dump_command)

    def _fake_command(self, command, description, env=None):
        if command[0] == "pg_dump":
            dump_path = Path(next(arg.split("=", 1)[1] for arg in command if arg.startswith("--file=")))
            dump_path.write_bytes(b"valid postgres dump")
        elif command[0] == "age":
            encrypted_path = Path(command[command.index("--output") + 1])
            encrypted_path.write_bytes(b"encrypted-backup")

    def test_backup_is_verified_uploaded_and_retained(self):
        storage = FakeStorage()
        with (
            patch.object(backup_job, "SupabaseBackupStorage", return_value=storage),
            patch.object(backup_job, "_run", side_effect=self._fake_command),
        ):
            backup_job.run_backup()

        self.assertTrue(storage.archive_name.startswith("cocoscan_db_weekly_"))
        self.assertEqual(storage.deleted, ["weekly/cocoscan_db_weekly_20261101T160000Z.dump.age"])
        self.assertEqual([manifest["status"] for _, manifest in storage.manifests], ["running", "success"])
        self.assertEqual(storage.manifests[-1][1]["retention_count"], 12)

    def test_failed_dump_is_recorded_as_failure(self):
        storage = FakeStorage()
        with (
            patch.object(backup_job, "SupabaseBackupStorage", return_value=storage),
            patch.object(backup_job, "_run", side_effect=backup_job.BackupError("dump failed")),
            self.assertRaises(backup_job.BackupError),
        ):
            backup_job.run_backup()

        self.assertEqual(storage.manifests[-1][1]["status"], "failure")
        self.assertIn("dump failed", storage.manifests[-1][1]["error"])
        self.assertIsNone(storage.archive_name)


if __name__ == "__main__":
    unittest.main()
