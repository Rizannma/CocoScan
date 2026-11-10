import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.model_integrity import sha256_file, verify_model_integrity


class ModelIntegrityTests(unittest.TestCase):
    def test_matching_digest_is_accepted(self):
        with tempfile.NamedTemporaryFile() as model_file:
            model_file.write(b"trusted model")
            model_file.flush()
            digest = sha256_file(Path(model_file.name))
            with patch.dict(os.environ, {"PEST_MODEL_SHA256": digest}, clear=False):
                verify_model_integrity(Path(model_file.name))

    def test_mismatched_digest_is_rejected(self):
        with tempfile.NamedTemporaryFile() as model_file:
            model_file.write(b"tampered model")
            model_file.flush()
            with patch.dict(
                os.environ,
                {"PEST_MODEL_SHA256": "0" * 64},
                clear=False,
            ):
                with self.assertRaisesRegex(ValueError, "integrity verification failed"):
                    verify_model_integrity(Path(model_file.name))

    def test_production_requires_configured_digest(self):
        with tempfile.NamedTemporaryFile() as model_file:
            with patch.dict(
                os.environ,
                {"FLASK_ENV": "production"},
                clear=False,
            ), patch.dict(os.environ, {}, clear=False):
                os.environ.pop("PEST_MODEL_SHA256", None)
                with self.assertRaisesRegex(RuntimeError, "PEST_MODEL_SHA256"):
                    verify_model_integrity(Path(model_file.name))


if __name__ == "__main__":
    unittest.main()
