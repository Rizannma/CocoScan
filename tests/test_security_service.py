import unittest
import os
import sys
import sqlite3
import time
import gc
from unittest.mock import patch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import security_service

class TestSecurityService(unittest.TestCase):
    def setUp(self):
        # Create a clean temporary test database in scratch/tmp location
        self.test_db = os.path.join(os.path.dirname(__file__), f"test_security_{time.time_ns()}.db")
        security_service.DB_PATH = self.test_db
        security_service.init_security_db()

    def tearDown(self):
        gc.collect()
        if os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except Exception:
                pass

    def test_account_lockout(self):
        email = "test@example.com"
        # Attempt 1
        cnt, locked, msg = security_service.record_login_failure(email, "127.0.0.1")
        self.assertEqual(cnt, 1)
        self.assertIsNone(locked)

        # Attempt 2
        cnt, locked, msg = security_service.record_login_failure(email, "127.0.0.1")
        self.assertEqual(cnt, 2)

        # Attempt 3 - should lock for 15 minutes
        cnt, locked, msg = security_service.record_login_failure(email, "127.0.0.1")
        self.assertEqual(cnt, 3)
        self.assertIsNotNone(locked)
        self.assertIn("15 minutes", msg)

        # Check lockout
        is_locked, rem, reason = security_service.check_account_lockout(email)
        self.assertTrue(is_locked)
        self.assertGreater(rem, 800)

        # Reset failures
        security_service.reset_login_failures(email)
        is_locked, rem, reason = security_service.check_account_lockout(email)
        self.assertFalse(is_locked)

    def test_2fa_requirement(self):
        email = "admin@example.com"
        # Should require 2fa initially
        self.assertTrue(security_service.requires_2fa(email, days=7))
        
        # Record verification
        security_service.record_2fa_verification(email)
        self.assertFalse(security_service.requires_2fa(email, days=7))

    def test_generate_and_send_otp_uses_90_second_expiry(self):
        email = "otp@example.com"
        security_service.generate_and_send_otp(email, purpose="Password Reset")

        with security_service._get_db() as conn:
            row = conn.execute(
                "SELECT created_at, expires_at FROM otp_codes WHERE email = ? AND purpose = ? ORDER BY id DESC LIMIT 1",
                (email, "Password Reset")
            ).fetchone()

        self.assertIsNotNone(row)
        self.assertAlmostEqual(row["expires_at"] - row["created_at"], 90, delta=1)

    def test_generate_and_send_otp_reports_delivery_failure_without_crashing(self):
        result = security_service.generate_and_send_otp("otp-fallback@example.com", purpose="2FA Verification")
        self.assertIn("sent", result)
        self.assertIn("delivery_available", result)
        self.assertIn("delivery_message", result)
        self.assertIsInstance(result["delivery_available"], bool)
        self.assertFalse(result["fallback_allowed"])
        self.assertNotIn("code", result)

    @patch('app.security_service._send_email_brevo', return_value=True)
    def test_otp_requests_are_limited_to_three_per_hour(self, _mock_send):
        email = "otp-limit@example.com"
        with patch('app.security_service.time.time', return_value=1000):
            for _ in range(3):
                result = security_service.generate_and_send_otp(email, "Password Reset")
                self.assertTrue(result["sent"])

            limited = security_service.generate_and_send_otp(email, "Password Reset")
            self.assertTrue(limited["rate_limited"])
            self.assertEqual(limited["retry_after_seconds"], 3600)

        with patch('app.security_service.time.time', return_value=4600):
            allowed = security_service.generate_and_send_otp(email, "Password Reset")
            self.assertTrue(allowed["sent"])

    @patch('app.security_service._send_email_brevo', return_value=True)
    @patch('app.security_service.secrets.randbelow', return_value=123456)
    def test_three_incorrect_otp_entries_lock_verification_for_one_hour(self, _mock_random, _mock_send):
        email = "otp-verify-limit@example.com"
        purpose = "Password Reset"
        with patch('app.security_service.time.time', return_value=1000):
            security_service.generate_and_send_otp(email, purpose)
            with security_service._get_db() as conn:
                stored_code = conn.execute(
                    "SELECT code FROM otp_codes WHERE email = ? AND purpose = ? ORDER BY id DESC LIMIT 1",
                    (email, purpose)
                ).fetchone()["code"]

            self.assertNotEqual(stored_code, "123456")
            wrong_code = "000000"
            for _ in range(3):
                success, message = security_service.verify_otp(email, wrong_code, purpose)
                self.assertFalse(success)

            self.assertIn("60 minutes", message)
            success, message = security_service.verify_otp(email, "123456", purpose)
            self.assertFalse(success)
            self.assertIn("try again", message)

        with patch('app.security_service.time.time', return_value=4601):
            security_service.generate_and_send_otp(email, purpose)
            success, _message = security_service.verify_otp(email, "123456", purpose)
            self.assertTrue(success)

    @patch('app.security_service._send_email_brevo', return_value=True)
    @patch('app.security_service.secrets.randbelow', return_value=123456)
    def test_correct_otp_is_single_use_and_not_returned(self, _mock_random, _mock_send):
        email = "otp-single-use@example.com"
        result = security_service.generate_and_send_otp(email, "2FA Verification")

        self.assertNotIn("code", result)
        with security_service._get_db() as conn:
            stored_code = conn.execute(
                "SELECT code FROM otp_codes WHERE email = ? AND purpose = ? ORDER BY id DESC LIMIT 1",
                (email, "2FA Verification")
            ).fetchone()["code"]
        self.assertNotEqual(stored_code, "123456")
        success, _message = security_service.verify_otp(email, "123456", "2FA Verification")
        self.assertTrue(success)
        success, message = security_service.verify_otp(email, "123456", "2FA Verification")
        self.assertFalse(success)
        self.assertIn("No active verification code", message)

    def test_audit_logs(self):
        security_service.log_audit("admin@example.com", "admin", "LOGIN", "Test audit log", "127.0.0.1")
        logs_data = security_service.get_audit_logs(page=1, per_page=10)
        self.assertGreaterEqual(logs_data['total'], 1)
        self.assertEqual(logs_data['logs'][0]['action'], "LOGIN")

if __name__ == '__main__':
    unittest.main()
