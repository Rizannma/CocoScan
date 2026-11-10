import os
import tempfile
import unittest

from app.model_paths import (
    DEFAULT_PEST_MODEL,
    resolve_model_path,
)


class ModelPathTests(unittest.TestCase):
    def test_resolve_model_path_prefers_existing_local_pest_model(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = os.path.join(tmpdir, 'model')
            os.makedirs(model_dir, exist_ok=True)
            target = os.path.join(model_dir, 'pest_classifier.tflite')
            with open(target, 'w', encoding='utf-8') as f:
                f.write('model')

            resolved = resolve_model_path('PEST_MODEL_PATH', 'pest_classifier.tflite', model_dir=model_dir, env_value='custom/models/pest_classifier.tflite')

            self.assertEqual(os.path.realpath(resolved), os.path.realpath(target))

    def test_default_pest_model_constant(self):
        self.assertEqual(DEFAULT_PEST_MODEL, 'pest_classifier.tflite')

    def test_h5_model_is_rejected(self):
        from model.inference import get_pest_model_path

        with tempfile.NamedTemporaryFile(suffix=".h5") as model_file:
            with self.assertRaises(ValueError):
                get_pest_model_path(model_file.name)


if __name__ == "__main__":
    unittest.main()
