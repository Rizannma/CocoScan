import io
import os
import sys
import pytest
from unittest.mock import MagicMock
from PIL import Image
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from app.image_utils import (
    process_and_compress_image,
    compress_image_to_bytes,
    is_storage_limit_error,
    InvalidImageFormatError,
    StorageLimitExceededError,
    INVALID_IMAGE_ERROR_MESSAGE,
    STORAGE_LIMIT_ERROR_MESSAGE,
)


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key-for-image-tests'
    with app.test_client() as client:
        yield client


def _create_test_image_bytes(format="JPEG", width=100, height=100, color=(30, 160, 40)):
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


class TestImageDecodingAndValidation:
    """Test backend error handling for invalid/corrupted image uploads."""

    def test_valid_jpeg_decodes_cleanly(self):
        jpeg_bytes = _create_test_image_bytes("JPEG")
        processed = process_and_compress_image(jpeg_bytes)
        assert isinstance(processed, Image.Image)
        assert processed.mode == "RGB"

    def test_valid_png_decodes_cleanly(self):
        png_bytes = _create_test_image_bytes("PNG")
        processed = process_and_compress_image(png_bytes)
        assert isinstance(processed, Image.Image)
        assert processed.mode == "RGB"

    def test_corrupted_image_bytes_raises_invalid_format_error(self):
        corrupted_bytes = b"corrupted_header_not_a_valid_image_12345"
        with pytest.raises(InvalidImageFormatError) as exc_info:
            process_and_compress_image(corrupted_bytes)
        assert exc_info.value.message == INVALID_IMAGE_ERROR_MESSAGE

    def test_empty_bytes_raises_invalid_format_error(self):
        with pytest.raises(InvalidImageFormatError) as exc_info:
            process_and_compress_image(b"")
        assert exc_info.value.message == INVALID_IMAGE_ERROR_MESSAGE

    def test_unsupported_format_raises_invalid_format_error(self):
        # Create a GIF image
        img = Image.new("RGB", (50, 50), color=(255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="GIF")
        gif_bytes = buf.getvalue()

        with pytest.raises(InvalidImageFormatError) as exc_info:
            process_and_compress_image(gif_bytes)
        assert exc_info.value.message == INVALID_IMAGE_ERROR_MESSAGE

    def test_truncated_image_stream_raises_invalid_format_error(self):
        jpeg_bytes = _create_test_image_bytes("JPEG")
        # Truncate halfway through
        truncated_bytes = jpeg_bytes[:20]
        with pytest.raises(InvalidImageFormatError) as exc_info:
            process_and_compress_image(truncated_bytes)
        assert exc_info.value.message == INVALID_IMAGE_ERROR_MESSAGE


class TestStorageLimitDetection:
    """Test Supabase storage bucket full / quota exceeded detection."""

    def test_status_code_507_detected(self):
        assert is_storage_limit_error({"statusCode": 507, "error": "Insufficient Storage"}) is True
        assert is_storage_limit_error({"status_code": 507}) is True

    def test_status_code_413_detected(self):
        assert is_storage_limit_error({"statusCode": 413, "error": "Payload Too Large"}) is True
        assert is_storage_limit_error({"status_code": 413}) is True

    def test_quota_exceeded_message_detected(self):
        assert is_storage_limit_error({"message": "storage quota exceeded"}) is True
        assert is_storage_limit_error(Exception("Storage limit reached")) is True
        assert is_storage_limit_error(Exception("Supabase bucket full")) is True
        assert is_storage_limit_error("The project storage limit has been reached.") is True

    def test_unrelated_errors_not_flagged_as_storage_limits(self):
        assert is_storage_limit_error({"error": "Unauthorized", "statusCode": 401}) is False
        assert is_storage_limit_error({"message": "Row not found", "statusCode": 404}) is False
        assert is_storage_limit_error(Exception("Network timeout connecting to database")) is False


class TestFarmerPredictRouteErrorHandling:
    """Test error handling in /farmer/predict endpoint."""

    def test_predict_rejects_corrupted_image_with_400(self, client):
        with client.session_transaction() as sess:
            sess['user_id'] = 'farmer-test-123'
            sess['user_role'] = 'farmer'

        data = {
            'image_file': (io.BytesIO(b'bad_corrupted_image_data_here'), 'bad.jpg')
        }
        resp = client.post('/farmer/predict', data=data, content_type='multipart/form-data')
        assert resp.status_code == 400
        res_json = resp.get_json()
        assert res_json.get('error') == INVALID_IMAGE_ERROR_MESSAGE

    def test_predict_rejects_non_image_file_with_400(self, client):
        with client.session_transaction() as sess:
            sess['user_id'] = 'farmer-test-123'
            sess['user_role'] = 'farmer'

        data = {
            'image_file': (io.BytesIO(b'%PDF-1.4 Fake PDF content'), 'document.pdf')
        }
        resp = client.post('/farmer/predict', data=data, content_type='multipart/form-data')
        assert resp.status_code == 400
        res_json = resp.get_json()
        assert res_json.get('error') == INVALID_IMAGE_ERROR_MESSAGE

    def test_predict_valid_image_succeeds(self, client, monkeypatch):
        with client.session_transaction() as sess:
            sess['user_id'] = 'farmer-test-123'
            sess['user_role'] = 'farmer'

        jpeg_bytes = _create_test_image_bytes("JPEG", 224, 224)
        data = {
            'image_file': (io.BytesIO(jpeg_bytes), 'leaf.jpg')
        }

        # Mock inference pipeline to verify clean response path
        import app.inference_pipeline
        monkeypatch.setattr(
            app.inference_pipeline,
            'run_full_inference_pipeline',
            lambda *args, **kwargs: {
                'success': True,
                'pest': 'Healthy Coconut Leaf',
                'severity': 'Mild',
                'pest_confidence': 0.95,
                'severity_confidence': 0.90,
                'damage_percentage': 25,
                'recommendations': ['Maintain regular irrigation'],
                'risk_level': 'Low',
                'urgency': 'Low',
                'risk_factors': ['Optimal conditions'],
            }
        )

        resp = client.post('/farmer/predict', data=data, content_type='multipart/form-data')
        assert resp.status_code == 200
        res_json = resp.get_json()
        assert res_json.get('success') is True
        assert res_json.get('pest') == 'Healthy Coconut Leaf'


class TestSupabaseStorageLimitAndUploadErrors:
    """Test Supabase Storage upload quota limits in upload_image_to_supabase and /farmer/submit-report."""

    def test_upload_image_to_supabase_raises_storage_limit_on_quota_error(self, monkeypatch):
        import main
        mock_storage = MagicMock()
        mock_storage.upload.return_value = {
            "statusCode": 507,
            "error": "Storage limit reached. Unable to save the image at this time."
        }
        mock_client = MagicMock()
        mock_client.storage.from_.return_value = mock_storage
        monkeypatch.setattr(main, 'supabase', mock_client)

        with pytest.raises(StorageLimitExceededError) as exc_info:
            main.upload_image_to_supabase(b"dummy_bytes", "test.jpg")
        assert exc_info.value.message == STORAGE_LIMIT_ERROR_MESSAGE

    def test_upload_image_to_supabase_raises_storage_limit_on_413_payload_too_large(self, monkeypatch):
        import main
        mock_storage = MagicMock()
        mock_storage.upload.return_value = {
            "statusCode": 413,
            "error": "Payload too large: storage quota exceeded"
        }
        mock_client = MagicMock()
        mock_client.storage.from_.return_value = mock_storage
        monkeypatch.setattr(main, 'supabase', mock_client)

        with pytest.raises(StorageLimitExceededError) as exc_info:
            main.upload_image_to_supabase(b"dummy_bytes", "test.jpg")
        assert exc_info.value.message == STORAGE_LIMIT_ERROR_MESSAGE

    def test_submit_report_returns_507_when_storage_quota_exceeded(self, client, monkeypatch):
        with client.session_transaction() as sess:
            sess['user_id'] = 'farmer-test-123'
            sess['user_role'] = 'farmer'

        import main
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_insert.execute.return_value = MagicMock(data=[{'id': 'report-123'}], error=None)
        mock_select = MagicMock()
        mock_select.eq.return_value.execute.return_value = MagicMock(data=[{'first_name': 'Juan', 'last_name': 'Farmer'}])
        mock_table.insert.return_value = mock_insert
        mock_table.select.return_value = mock_select

        mock_supabase = MagicMock()
        mock_supabase.table.return_value = mock_table
        monkeypatch.setattr(main, 'supabase', mock_supabase)

        # Mock upload_image_to_supabase to raise StorageLimitExceededError
        monkeypatch.setattr(
            main,
            'upload_image_to_supabase',
            MagicMock(side_effect=StorageLimitExceededError(STORAGE_LIMIT_ERROR_MESSAGE))
        )

        jpeg_bytes = _create_test_image_bytes("JPEG", 100, 100)
        report_data = {
            'pest_type': 'Brontispa',
            'farmer_notes': 'Heavy infestation observed',
            'confidence': '90',
            'image_file': (io.BytesIO(jpeg_bytes), 'leaf.jpg')
        }

        resp = client.post('/farmer/submit-report', data=report_data, content_type='multipart/form-data')
        assert resp.status_code == 507
        res_json = resp.get_json()
        assert res_json.get('error') == STORAGE_LIMIT_ERROR_MESSAGE

    def test_submit_report_returns_400_on_corrupted_image(self, client, monkeypatch):
        with client.session_transaction() as sess:
            sess['user_id'] = 'farmer-test-123'
            sess['user_role'] = 'farmer'

        report_data = {
            'pest_type': 'Brontispa',
            'farmer_notes': 'Test report notes',
            'confidence': '90',
            'image_file': (io.BytesIO(b'corrupted_image_payload'), 'corrupt.jpg')
        }

        resp = client.post('/farmer/submit-report', data=report_data, content_type='multipart/form-data')
        assert resp.status_code == 400
        res_json = resp.get_json()
        assert res_json.get('error') == INVALID_IMAGE_ERROR_MESSAGE

    def test_submit_report_returns_400_on_corrupted_supporting_image(self, client, monkeypatch):
        with client.session_transaction() as sess:
            sess['user_id'] = 'farmer-test-123'
            sess['user_role'] = 'farmer'

        report_data = {
            'pest_type': 'Brontispa',
            'farmer_notes': 'Test report notes',
            'confidence': '90',
            'supporting_images': [(io.BytesIO(b'corrupted_support_image'), 'corrupt_sup.jpg')]
        }

        resp = client.post('/farmer/submit-report', data=report_data, content_type='multipart/form-data')
        assert resp.status_code == 400
        res_json = resp.get_json()
        assert res_json.get('error') == INVALID_IMAGE_ERROR_MESSAGE

    def test_agriculturist_complete_visit_returns_400_on_corrupted_image(self, client, monkeypatch):
        with client.session_transaction() as sess:
            sess['user_id'] = 'agri-test-123'
            sess['user_role'] = 'agri_expert'

        import main
        monkeypatch.setattr(main, '_update_report_workflow', lambda *args, **kwargs: MagicMock(error=None))

        visit_data = {
            'report_id': '10',
            'visit_summary': 'Conducted tree assessment',
            'visit_images': [(io.BytesIO(b'corrupted_visit_bytes'), 'visit_corrupt.jpg')]
        }

        resp = client.post('/agriculturist/complete-visit', data=visit_data, content_type='multipart/form-data')
        assert resp.status_code == 400
        res_json = resp.get_json()
        assert res_json.get('error') == INVALID_IMAGE_ERROR_MESSAGE

    def test_agriculturist_complete_visit_returns_507_on_storage_limit(self, client, monkeypatch):
        with client.session_transaction() as sess:
            sess['user_id'] = 'agri-test-123'
            sess['user_role'] = 'agri_expert'

        import main
        monkeypatch.setattr(main, '_update_report_workflow', lambda *args, **kwargs: MagicMock(error=None))
        monkeypatch.setattr(
            main,
            'upload_image_to_supabase',
            MagicMock(side_effect=StorageLimitExceededError(STORAGE_LIMIT_ERROR_MESSAGE))
        )

        jpeg_bytes = _create_test_image_bytes("JPEG", 100, 100)
        visit_data = {
            'report_id': '10',
            'visit_summary': 'Conducted tree assessment',
            'visit_images': [(io.BytesIO(jpeg_bytes), 'visit.jpg')]
        }

        resp = client.post('/agriculturist/complete-visit', data=visit_data, content_type='multipart/form-data')
        assert resp.status_code == 507
        res_json = resp.get_json()
        assert res_json.get('error') == STORAGE_LIMIT_ERROR_MESSAGE

