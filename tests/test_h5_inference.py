import base64
import io
import os
import sys
import unittest
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.inference import (
    PEST_CLASSES,
    PEST_LABELS,
    get_pest_model_path,
    predict_pest,
    predict_pest_from_base64,
    preload_models,
    _prepare_input,
)
from app.inference_pipeline import run_full_inference_pipeline


def _create_synthetic_leaf_image(width: int = 224, height: int = 224) -> Image.Image:
    """Create a synthetic green leaf-like image with natural texture for testing."""
    rng = np.random.RandomState(42)
    base = rng.randint(40, 180, (224, 224, 3), dtype=np.uint8)
    base[:, :, 1] = np.clip(base[:, :, 1].astype(int) + 60, 0, 255).astype(np.uint8)
    img_base = Image.fromarray(base, "RGB")
    if (width, height) != (224, 224):
        return img_base.resize((width, height), Image.Resampling.NEAREST)
    return img_base


def _image_to_base64(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


class TestH5Inference(unittest.TestCase):
    def test_model_paths_exist(self):
        pest_path = get_pest_model_path()
        self.assertTrue(pest_path.exists(), f"Pest model does not exist at {pest_path}")
        self.assertTrue(
            str(pest_path).endswith("pest_classifier.tflite") or str(pest_path).endswith("pest_classifier.h5")
        )

    def test_tflite_model_used_by_default(self):
        from model.inference import get_active_model_format
        self.assertEqual(get_active_model_format(), "tflite")

    def test_global_preload_models(self):
        pest_model = preload_models()
        self.assertIsNotNone(pest_model)

    def test_image_resizing_and_contiguous_tensor_preparation(self):
        # Create non-standard dimension image (e.g. 800x600)
        img = _create_synthetic_leaf_image(width=800, height=600)
        tensor = _prepare_input(img)
        
        # Check shape is normalized (1, 224, 224, 3)
        self.assertEqual(tuple(tensor.shape), (1, 224, 224, 3))
        
        # Check contiguous flag if tensor or numpy
        if hasattr(tensor, "is_contiguous"):
            self.assertTrue(tensor.is_contiguous())
        elif hasattr(tensor, "flags"):
            self.assertTrue(tensor.flags.c_contiguous)

    def test_pest_prediction_structure(self):
        img = _create_synthetic_leaf_image()
        result = predict_pest(img)
        self.assertIn("predicted_pest", result)
        self.assertIn("confidence_score", result)
        self.assertIn("probabilities", result)
        self.assertIn(result["predicted_pest"], PEST_CLASSES)
        self.assertEqual(
            PEST_CLASSES,
            ["Brontispa", "Healthy", "Not Coconut Leaf", "Rhinoceros"],
        )
        self.assertGreaterEqual(result["confidence_score"], 0.0)
        self.assertLessEqual(result["confidence_score"], 1.0)
        self.assertEqual(len(result["probabilities"]), 4)

    def test_base64_predictions(self):
        img = _create_synthetic_leaf_image()
        b64_str = _image_to_base64(img)

        pest_res = predict_pest_from_base64(b64_str)
        self.assertIn("predicted_pest", pest_res)

    def test_full_inference_pipeline(self):
        img = _create_synthetic_leaf_image()
        result = run_full_inference_pipeline(img)

        self.assertTrue(result["success"])
        self.assertIn("pest", result)
        self.assertIn("pest_confidence", result)
        self.assertIn("recommendations", result)
        self.assertTrue(len(result["recommendations"]) > 0)
        self.assertIn("possible_pest_title", result)
        self.assertTrue(result["possible_pest_title"].startswith("Possible Pest: "))

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
        self.assertIn('pest', data)
        self.assertGreater(len(data['recommendations']), 0)
        self.assertIn('possible_pest_title', data)

    def test_image_compression_and_downscale(self):
        from app.image_utils import process_and_compress_image, compress_image_to_bytes
        large_img = _create_synthetic_leaf_image(width=3000, height=2000)
        processed = process_and_compress_image(large_img, max_dimension=1024)
        self.assertLessEqual(processed.size[0], 1024)
        self.assertLessEqual(processed.size[1], 1024)
        self.assertEqual(processed.mode, "RGB")
        
        # Test bytes compression
        jpeg_bytes = compress_image_to_bytes(large_img, max_dimension=1024)
        self.assertTrue(len(jpeg_bytes) > 0)
        self.assertLess(len(jpeg_bytes), 500000)  # Compressed under 500KB

    def test_large_image_upload_endpoint(self):
        from main import app
        # Create a large 2400x1600 synthetic image
        img = _create_synthetic_leaf_image(width=2400, height=1600)
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=95)
        buf.seek(0)

        client = app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = 'test-farmer-1'
            sess['user_role'] = 'farmer'
            sess['user_name'] = 'Test Farmer'

        response = client.post(
            '/farmer/predict',
            data={'image_file': (buf, 'huge_leaf.jpg')},
            content_type='multipart/form-data'
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('pest', data)

    def test_clear_inference_memory(self):
        from model.inference import clear_inference_memory
        # Should execute without errors on any backend/device
        clear_inference_memory()


if __name__ == "__main__":
    unittest.main()
