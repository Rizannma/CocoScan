import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import security_service


class AuditIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.previous_db_path = security_service.DB_PATH
        self.test_db = tempfile.NamedTemporaryFile(delete=False).name
        security_service.DB_PATH = self.test_db
        security_service._db_initialized = False
        security_service.init_security_db()

    def tearDown(self):
        security_service.DB_PATH = self.previous_db_path
        security_service._db_initialized = False
        os.unlink(self.test_db)

    def test_audit_chain_detects_tampering(self):
        security_service.log_audit(
            "integrity@example.com", "admin", "INTEGRITY_TEST", "Original", "127.0.0.1"
        )
        with security_service._get_db() as conn:
            row = conn.execute(
                "SELECT id FROM audit_logs WHERE action = ? ORDER BY id DESC LIMIT 1",
                ("INTEGRITY_TEST",),
            ).fetchone()
            conn.execute("UPDATE audit_logs SET details = ? WHERE id = ?", ("Changed", row["id"]))
            conn.commit()

        with patch("app.security_service._emit_audit_integrity_alert") as alert:
            result = security_service.verify_audit_log_integrity()

        self.assertFalse(result["valid"])
        alert.assert_called_once()
        with security_service._get_db() as conn:
            conn.execute("DELETE FROM audit_logs WHERE id = ?", (row["id"],))
            conn.commit()


if __name__ == "__main__":
    unittest.main()
