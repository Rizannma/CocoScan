import base64
import io
import unittest
import numpy as np
from PIL import Image

from model.inference import (
    PEST_LABELS,
    SEVERITY_LABELS,
    get_pest_model_path,
    get_severity_model_path,
    predict_pest,
    predict_severity,
    predict_pest_from_base64,
    predict_severity_from_base64,
    predict_all_from_base64,
)
from app.inference_pipeline import run_full_inference_pipeline


def _create_synthetic_leaf_image(width: int = 224, height: int = 224) -> Image.Image:
    """Create a synthetic green leaf-like image for testing."""
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    arr[:, :, 0] = 30   # R
    arr[:, :, 1] = 160  # G (strong green)
    arr[:, :, 2] = 40   # B
    return Image.fromarray(arr, "RGB")


def _image_to_base64(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


class TestH5Inference(unittest.TestCase):
    def test_model_paths_exist(self):
        pest_path = get_pest_model_path()
        severity_path = get_severity_model_path()
        self.assertTrue(pest_path.exists(), f"Pest model does not exist at {pest_path}")
        self.assertTrue(severity_path.exists(), f"Severity model does not exist at {severity_path}")
        self.assertTrue(str(pest_path).endswith("pest_classifier_moderate.h5"))
        self.assertTrue(str(severity_path).endswith("severity_classifier_severe_boost.h5"))

    def test_pest_prediction_structure(self):
        img = _create_synthetic_leaf_image()
        result = predict_pest(img)
        self.assertIn("predicted_pest", result)
        self.assertIn("confidence_score", result)
        self.assertIn("probabilities", result)
        self.assertIn(result["predicted_pest"], PEST_LABELS)
        self.assertGreaterEqual(result["confidence_score"], 0.0)
        self.assertLessEqual(result["confidence_score"], 1.0)
        self.assertEqual(len(result["probabilities"]), 4)

    def test_severity_prediction_structure(self):
        img = _create_synthetic_leaf_image()
        result = predict_severity(img)
        self.assertIn("severity", result)
        self.assertIn("confidence_score", result)
        self.assertIn("damage_percentage", result)
        self.assertIn("probabilities", result)
        self.assertIn(result["severity"], SEVERITY_LABELS)
        self.assertIn(result["damage_percentage"], [25, 50, 75])
        self.assertEqual(len(result["probabilities"]), 3)

    def test_base64_predictions(self):
        img = _create_synthetic_leaf_image()
        b64_str = _image_to_base64(img)

        pest_res = predict_pest_from_base64(b64_str)
        self.assertIn("predicted_pest", pest_res)

        sev_res = predict_severity_from_base64(b64_str)
        self.assertIn("severity", sev_res)

        pest_all, sev_all = predict_all_from_base64(b64_str)
        self.assertEqual(pest_all["predicted_pest"], pest_res["predicted_pest"])
        self.assertEqual(sev_all["severity"], sev_res["severity"])

    def test_full_inference_pipeline(self):
        img = _create_synthetic_leaf_image()
        result = run_full_inference_pipeline(img)

        self.assertTrue(result["success"])
        self.assertIn("pest", result)
        self.assertIn(result["pest"], PEST_LABELS)
        self.assertIn("pest_confidence", result)
        self.assertIn("severity", result)
        self.assertIn(result["severity"], SEVERITY_LABELS)
        self.assertIn("severity_confidence", result)
        self.assertIn("damage_percentage", result)
        self.assertIn("recommendations", result)
        self.assertTrue(len(result["recommendations"]) > 0)
        self.assertIn("risk_level", result)
        self.assertIn("urgency", result)

    def test_leaf_image_validation_failures(self):
        # Too small image
        small_img = Image.new("RGB", (16, 16), color=(0, 200, 0))
        with self.assertRaises(ValueError):
            predict_pest(small_img)

        # Non-green / invalid leaf image
        black_img = Image.new("RGB", (100, 100), color=(0, 0, 0))
        with self.assertRaises(ValueError):
            predict_pest(black_img)

        blue_img = Image.new("RGB", (100, 100), color=(10, 10, 240))
        with self.assertRaises(ValueError):
            predict_pest(blue_img)

    def test_farmer_predict_endpoint(self):
        from main import app
        img = _create_synthetic_leaf_image()
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)

        client = app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = 'test-farmer-1'
            sess['user_role'] = 'farmer'
            sess['user_name'] = 'Test Farmer'

        response = client.post(
            '/farmer/predict',
            data={'image_file': (buf, 'leaf.jpg')},
            content_type='multipart/form-data'
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn(data['pest'], PEST_LABELS)
        self.assertIn(data['severity'], SEVERITY_LABELS)
        self.assertGreater(len(data['recommendations']), 0)
        self.assertIn('damage_percentage', data)
        self.assertIn('risk_level', data)
        self.assertIn('urgency', data)


if __name__ == "__main__":
    unittest.main()
