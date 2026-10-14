import os
import unittest
from unittest.mock import patch

from main import app, send_status_email

class TestEmailStatusLink(unittest.TestCase):
    @patch("main.requests.post")
    def test_default_fallback_login_link(self, mock_post):
        mock_post.return_value.status_code = 200
        with patch.dict(os.environ, {"BREVO_API_KEY": "fake_key"}, clear=True):
            send_status_email("user@example.com", "Test User", "Approved")
            
            self.assertTrue(mock_post.called)
            payload = mock_post.call_args[1]["json"]
            html_content = payload["htmlContent"]
            self.assertIn('href="https://cocoscan-ai.up.railway.app/login"', html_content)
            self.assertIn("Log In To Dashboard", html_content)

    @patch("main.requests.post")
    def test_env_app_base_url_with_or_without_scheme(self, mock_post):
        mock_post.return_value.status_code = 200
        # Test without https:// prefix
        with patch.dict(os.environ, {"BREVO_API_KEY": "fake_key", "APP_BASE_URL": "cocoscan-ai.up.railway.app"}, clear=True):
            send_status_email("user@example.com", "Test User", "Approved")
            
            self.assertTrue(mock_post.called)
            payload = mock_post.call_args[1]["json"]
            html_content = payload["htmlContent"]
            self.assertIn('href="https://cocoscan-ai.up.railway.app/login"', html_content)

    @patch("main.requests.post")
    def test_request_context_login_link(self, mock_post):
        mock_post.return_value.status_code = 200
        with patch.dict(os.environ, {"BREVO_API_KEY": "fake_key"}, clear=True):
            with app.test_request_context(base_url="https://app.cocoscan.org"):
                send_status_email("user@example.com", "Test User", "Approved")
                
                self.assertTrue(mock_post.called)
                payload = mock_post.call_args[1]["json"]
                html_content = payload["htmlContent"]
                self.assertIn('href="https://app.cocoscan.org/login"', html_content)

if __name__ == "__main__":
    unittest.main()
