# Automated database backups

CocoScan creates a full PostgreSQL backup every Sunday at 12:00 AM Asia/Manila
(Saturday at 4:00 PM UTC). The scheduled workflow is in
`.github/workflows/weekly-backup.yml`; it can also be started manually from the
GitHub Actions tab. GitHub may delay scheduled workflows during periods of high
load.

Each run uses `pg_dump` custom format, validates the dump with `pg_restore`,
encrypts it with [age](https://age-encryption.org/), uploads it to a private
Supabase Storage bucket, verifies the uploaded object size, and keeps the 12
newest weekly archives. A run status manifest is stored in the same bucket and
shown on the admin **Storage & Backups** page.

## Configure GitHub Actions

Create these repository Actions secrets:

| Secret | Value |
| --- | --- |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service-role key; grants private bucket management to the workflow |
| `SUPABASE_DB_URL` | PostgreSQL connection URI for a database role allowed to dump the full database |
| `BACKUP_AGE_RECIPIENT` | age public recipient generated from the private identity below |

Use the PostgreSQL connection URI from the Supabase project **Connect** dialog.
Prefer the Session Pooler URI for GitHub-hosted runners if the direct database
host is not reachable over IPv4. The database role must be able to read all
schemas and tables that should be backed up. Keep all secrets out of the
repository and workflow logs.

Generate and preserve an age identity **outside GitHub**:

```sh
age-keygen -o cocoscan-backups-identity.txt
age-keygen -y cocoscan-backups-identity.txt
```

Add the second command's output (the `age1...` public recipient) as
`BACKUP_AGE_RECIPIENT`. Store the identity file in a secure, access-controlled
offline location and maintain a recovery copy. The private identity is required
to decrypt backups; losing it makes the archives unrecoverable. Do not upload
the identity to GitHub or Supabase.

The workflow creates the `cocoscan-database-backups` bucket if it does not
exist, and refuses to use it if it is public. To use a different bucket, update
`SUPABASE_BACKUP_BUCKET` in the workflow and set the same environment variable
on the web application.
Ensure the Supabase project and Storage upload-size limits can accommodate the
encrypted database dump. Oversized uploads are recorded as failed runs and
visible in the admin status panel when Supabase Storage remains reachable.

## Configure the web application

Set `SUPABASE_BACKUP_SERVICE_ROLE_KEY` in the deployed application's secret
environment to the Supabase service-role key. The admin page uses this
server-side key to list, download through short-lived signed URLs, and delete
private archives. The key is used only by admin-protected routes and must never
be exposed to browser JavaScript. Optionally set `SUPABASE_BACKUP_BUCKET` if
using a non-default bucket.

## Restore a backup

Download an encrypted `.dump.age` archive from **Storage & Backups**, then
decrypt it with the preserved identity and restore it into a suitable test or
recovery PostgreSQL database:

```sh
age --decrypt --identity cocoscan-backups-identity.txt \
  --output database.dump cocoscan_db_weekly_YYYYMMDDTHHMMSSZ.dump.age
pg_restore --verbose --no-owner --no-acl --dbname="$RESTORE_DATABASE_URL" database.dump
```

Test restores periodically in a separate database before relying on backups for
disaster recovery. These archives cover PostgreSQL; they do not include
Supabase project settings or files stored separately in Supabase Storage. A
copy stored in the same Supabase project also does not protect against loss of
that entire project. Scheduled GitHub workflows run from the repository's
default branch; keep Actions enabled for the repository and verify the first
scheduled run in the Actions tab.
