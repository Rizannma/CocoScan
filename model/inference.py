import base64
import gc
import io
import logging
import os
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from PIL import Image

# Ensure Keras uses the PyTorch backend if TensorFlow is not present
os.environ.setdefault("KERAS_BACKEND", "torch")

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).resolve().parent.parent / "model"
PEST_TFLITE_FILE_NAME = "pest_classifier.tflite"
PEST_H5_FILE_NAME = "pest_classifier.h5"
PEST_MODEL_FILE_NAME = PEST_TFLITE_FILE_NAME

# The trained 4-class pest model output order:
# [Brontispa, Healthy Coconut Leaf, Rhinoceros Beetle, Not a Coconut Leaf Image]
PEST_LABELS = ["Brontispa", "Healthy Coconut Leaf", "Rhinoceros Beetle", "Not a Coconut Leaf Image"]

# Minimum confidence cutoff for acceptable predictions
MIN_CONFIDENCE_THRESHOLD = 0.25
NOT_COCONUT_LEAF_LABEL = "Not a Coconut Leaf Image"
UNKNOWN_LABEL_BASE = NOT_COCONUT_LEAF_LABEL
MIN_IMAGE_DIMENSION = 32
GREEN_MEAN_THRESHOLD = 20.0
LEAF_GREEN_RATIO_THRESHOLD = 0.05
TARGET_SIZE = (224, 224)

# Cache for loaded pest model (thread-safe singleton)
_cached_pest_model = None
_cached_pest_path: Optional[Path] = None
_model_lock = threading.Lock()


class TFLiteModelWrapper:
    """Lightweight, thread-safe wrapper for TFLite Interpreter providing a standard callable interface."""

    def __init__(self, model_path: Union[str, Path]):
        self.model_path = Path(model_path)
        self._lock = threading.Lock()

        interpreter_cls = None
        try:
            from ai_edge_litert.interpreter import Interpreter
            interpreter_cls = Interpreter
        except ImportError:
            try:
                from tflite_runtime.interpreter import Interpreter
                interpreter_cls = Interpreter
            except ImportError:
                try:
                    from tensorflow.lite import Interpreter
                    interpreter_cls = Interpreter
                except ImportError:
                    pass

        if interpreter_cls is None:
            raise RuntimeError(
                "No TFLite runtime found. Please install ai-edge-litert or tflite-runtime."
            )

        self.interpreter = interpreter_cls(model_path=str(self.model_path))
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.input_index = self.input_details[0]["index"]
        self.output_index = self.output_details[0]["index"]
        logger.info(f"Initialized TFLite interpreter from {self.model_path}")

    def __call__(self, input_tensor: Any) -> np.ndarray:
        if isinstance(input_tensor, np.ndarray):
            arr = input_tensor
        elif hasattr(input_tensor, "cpu") and hasattr(input_tensor, "numpy"):
            arr = input_tensor.cpu().numpy()
        elif hasattr(input_tensor, "numpy"):
            arr = input_tensor.numpy()
        else:
            arr = np.asarray(input_tensor, dtype=np.float32)

        if arr.dtype != np.float32:
            arr = arr.astype(np.float32)

        with self._lock:
            self.interpreter.set_tensor(self.input_index, arr)
            self.interpreter.invoke()
            output_data = self.interpreter.get_tensor(self.output_index)

        return np.copy(output_data)

    def predict(self, input_tensor: Any, verbose: int = 0) -> np.ndarray:
        return self(input_tensor)


def clear_inference_memory():
    """
    Aggressively clear GPU/MPS memory caches, temporary tensors, and run garbage collection.
    Ensures zero residual memory remains trapped between rapid successive inference requests.
    """
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            if hasattr(torch.cuda, "ipc_collect"):
                torch.cuda.ipc_collect()
        if hasattr(torch, "mps") and hasattr(torch.mps, "empty_cache"):
            try:
                torch.mps.empty_cache()
            except Exception:
                pass
    except Exception:
        pass
    gc.collect()


def get_pest_model_path(model_path: Optional[str] = None) -> Path:
    if model_path:
        target_path = Path(model_path)
        if not target_path.exists():
            raise FileNotFoundError(f"Pest model not found: {target_path}")
        return target_path

    tflite_path = MODEL_DIR / PEST_TFLITE_FILE_NAME
    if tflite_path.exists():
        return tflite_path

    h5_path = MODEL_DIR / PEST_H5_FILE_NAME
    if h5_path.exists():
        return h5_path

    raise FileNotFoundError(f"Pest model not found in {MODEL_DIR} (checked .tflite and .h5)")


def get_active_model_format(model_path: Optional[str] = None) -> str:
    """Returns 'tflite' or 'h5' for the active pest classification model."""
    path = get_pest_model_path(model_path)
    return "tflite" if path.suffix.lower() == ".tflite" else "h5"


# Backward compatibility alias
get_model_path = get_pest_model_path


def reload_pest_model(model_path: Optional[str] = None):
    """Reset cached pest model singleton and reload fresh weights from disk."""
    global _cached_pest_model, _cached_pest_path
    with _model_lock:
        _cached_pest_model = None
        _cached_pest_path = None
    clear_inference_memory()
    return _get_pest_model(model_path)


def _load_keras_model(model_path: Path):
    try:
        import keras
        model = keras.models.load_model(str(model_path), compile=False)
        if hasattr(model, "eval") and callable(getattr(model, "eval")):
            model.eval()
        return model
    except Exception as exc:
        try:
            import tensorflow as tf
            model = tf.keras.models.load_model(str(model_path), compile=False)
            return model
        except Exception:
            raise RuntimeError(f"Failed to load Keras H5 model from {model_path}: {exc}")


def _get_pest_model(model_path: Optional[str] = None):
    global _cached_pest_model, _cached_pest_path
    resolved_path = get_pest_model_path(model_path)
    if _cached_pest_model is None or _cached_pest_path != resolved_path:
        with _model_lock:
            if _cached_pest_model is None or _cached_pest_path != resolved_path:
                logger.info(f"Loading pest classifier model globally from {resolved_path}")
                if resolved_path.suffix.lower() == ".tflite":
                    _cached_pest_model = TFLiteModelWrapper(resolved_path)
                else:
                    _cached_pest_model = _load_keras_model(resolved_path)
                _cached_pest_path = resolved_path
    return _cached_pest_model


def preload_models(pest_model_path: Optional[str] = None) -> Any:
    """
    Preload and warm up the pest classification model globally once at startup.
    Executes a dummy forward pass to warm up runtime kernels and prevent cold latency spikes.
    """
    pest_model = _get_pest_model(pest_model_path)

    try:
        dummy = np.zeros((1, 224, 224, 3), dtype=np.float32)
        if isinstance(pest_model, TFLiteModelWrapper):
            _ = pest_model(dummy)
            logger.info("Global pest TFLite model successfully preloaded, warmed up, and ready for inference.")
        else:
            try:
                import torch
                dummy_t = torch.zeros((1, 224, 224, 3), dtype=torch.float32).contiguous()
                ctx = torch.inference_mode() if hasattr(torch, "inference_mode") else torch.no_grad()
                with ctx:
                    _ = pest_model(dummy_t)
                del dummy_t
            except Exception:
                _ = pest_model(dummy)
            logger.info("Global pest H5 model successfully preloaded, warmed up, and ready for inference.")
        del dummy
        clear_inference_memory()
    except Exception as warmup_err:
        logger.warning(f"Model warmup notice: {warmup_err}")

    return pest_model


def _softmax(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float32)
    values = values - np.max(values)
    exp_values = np.exp(values)
    return exp_values / np.sum(exp_values)


def _decode_base64_image(image_data: str) -> Image.Image:
    from app.image_utils import (
        process_and_compress_image,
        InvalidImageFormatError,
        INVALID_IMAGE_ERROR_MESSAGE,
    )
    if not image_data or not isinstance(image_data, str):
        raise InvalidImageFormatError(INVALID_IMAGE_ERROR_MESSAGE)
    if "," in image_data:
        image_data = image_data.split(",", 1)[1]
    try:
        image_bytes = base64.b64decode(image_data)
    except Exception as b64_err:
        raise InvalidImageFormatError(INVALID_IMAGE_ERROR_MESSAGE) from b64_err
    return process_and_compress_image(image_bytes, max_dimension=1024)


def _validate_leaf_image(image: Image.Image):
    rgb_image = image if isinstance(image, Image.Image) and image.mode == "RGB" else image.convert("RGB")
    array = np.asarray(rgb_image, dtype=np.float32)
    if array.ndim == 2:
        array = np.stack([array] * 3, axis=-1)

    if array.shape[-1] != 3:
        raise ValueError("Unsupported image format for inference.")

    height, width = array.shape[0], array.shape[1]
    if height < MIN_IMAGE_DIMENSION or width < MIN_IMAGE_DIMENSION:
        raise ValueError("Image is too small for reliable leaf detection.")

    red_mean = np.mean(array[..., 0])
    green_mean = np.mean(array[..., 1])
    blue_mean = np.mean(array[..., 2])
    green_ratio = green_mean / max(red_mean, blue_mean, 1.0)

    if green_mean < GREEN_MEAN_THRESHOLD or green_ratio < LEAF_GREEN_RATIO_THRESHOLD:
        raise ValueError(
            "Image does not appear to be a coconut leaf or plant sample. Please capture a clear photo of a coconut frond or leaf."
        )


def _prepare_input(image: Image.Image) -> Union[np.ndarray, Any]:
    """
    Preprocess PIL image into a normalized float32 tensor of shape (1, 224, 224, 3)
    and convert into a contiguous tensor compatible with the Keras PyTorch backend.
    Optimized for minimal allocations and maximum throughput.
    """
    if not isinstance(image, Image.Image):
        raise ValueError(f"Expected PIL Image instance, got {type(image)}")

    # Fast RGB conversion
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Fast Bilinear resize
    if image.size != TARGET_SIZE:
        image = image.resize(TARGET_SIZE, Image.Resampling.BILINEAR)

    # Convert to float32 NumPy array and scale [0.0, 1.0]
    array = np.asarray(image, dtype=np.float32) * (1.0 / 255.0)

    if array.ndim == 2:
        array = np.stack([array] * 3, axis=-1)
    elif array.ndim == 3 and array.shape[-1] > 3:
        array = array[..., :3]
    elif array.ndim == 3 and array.shape[-1] == 1:
        array = np.repeat(array, 3, axis=-1)

    if array.ndim == 3:
        array = np.expand_dims(array, axis=0)

    # Guarantee contiguous C-order buffer in memory
    array = np.ascontiguousarray(array, dtype=np.float32)

    # Convert to contiguous PyTorch tensor
    try:
        import torch
        tensor = torch.from_numpy(array).contiguous()
        return tensor
    except Exception:
        return array


def _run_model_forward(model, input_tensor: Union[np.ndarray, Any]) -> np.ndarray:
    """
    Execute model prediction and return 1D numpy array of probabilities.
    Directly invokes TFLite interpreter when model is TFLite, avoiding PyTorch runtime overhead.
    """
    if isinstance(model, TFLiteModelWrapper):
        if hasattr(input_tensor, "cpu") and hasattr(input_tensor, "numpy"):
            arr = input_tensor.cpu().numpy()
        elif hasattr(input_tensor, "numpy"):
            arr = input_tensor.numpy()
        else:
            arr = np.asarray(input_tensor, dtype=np.float32)
        preds = model(arr)
        preds = np.squeeze(preds)
        if preds.ndim > 1 and preds.shape[0] == 1:
            preds = preds[0]
        if np.min(preds) < 0.0 or not np.isclose(np.sum(preds), 1.0, atol=1e-2):
            preds = _softmax(preds)
        return preds.astype(np.float32)

    try:
        import torch
        ctx = torch.inference_mode() if hasattr(torch, "inference_mode") else torch.no_grad()
        with ctx:
            if isinstance(input_tensor, np.ndarray):
                tensor = torch.from_numpy(np.ascontiguousarray(input_tensor, dtype=np.float32)).contiguous()
            else:
                tensor = input_tensor

            try:
                preds = model(tensor)
            except Exception:
                preds = model.predict(tensor, verbose=0)

            if hasattr(preds, "detach"):
                preds = preds.detach().cpu().numpy()
            elif hasattr(preds, "cpu"):
                preds = preds.cpu().numpy()
            elif hasattr(preds, "numpy"):
                preds = preds.numpy()
            else:
                preds = np.asarray(preds)

    except ImportError:
        if hasattr(input_tensor, "numpy"):
            input_tensor = input_tensor.numpy()
        preds = model(input_tensor)
        if hasattr(preds, "numpy"):
            preds = preds.numpy()
        else:
            preds = np.asarray(preds)
    except Exception as exc:
        logger.warning(f"Inference primary forward pass failed ({exc}), attempting model.predict fallback...")
        if hasattr(input_tensor, "numpy"):
            input_tensor = input_tensor.numpy()
        elif hasattr(input_tensor, "detach"):
            input_tensor = input_tensor.detach().cpu().numpy()
        preds = model.predict(input_tensor, verbose=0)
        if hasattr(preds, "numpy"):
            preds = preds.numpy()
        else:
            preds = np.asarray(preds)

    preds = np.squeeze(preds)
    if preds.ndim > 1 and preds.shape[0] == 1:
        preds = preds[0]

    # If the output is not normalized (logits), apply softmax
    if np.min(preds) < 0.0 or not np.isclose(np.sum(preds), 1.0, atol=1e-2):
        preds = _softmax(preds)

    return preds.astype(np.float32)


def _get_labels(num_classes: int, base_labels: List[str] = PEST_LABELS) -> List[str]:
    if num_classes <= len(base_labels):
        return base_labels[:num_classes]
    extra_labels = [UNKNOWN_LABEL_BASE] * (num_classes - len(base_labels))
    return base_labels + extra_labels


def predict_pest(image: Image.Image, model_path: Optional[str] = None) -> Dict:
    """
    Run single-model pest classification on a PIL Image using pest_classifier.h5.
    Returns predicted_pest label, confidence_score, and class probabilities.
    """
    try:
        _validate_leaf_image(image)
        model = _get_pest_model(model_path)
        input_tensor = _prepare_input(image)
        probabilities = _run_model_forward(model, input_tensor)
        del input_tensor

        label_index = int(np.argmax(probabilities))
        labels = _get_labels(len(probabilities), PEST_LABELS)
        predicted_pest = labels[label_index]
        confidence = float(probabilities[label_index])

        if predicted_pest == NOT_COCONUT_LEAF_LABEL:
            raise ValueError(
                "This appears not to be a coconut leaf image. Please upload a proper coconut leaf photo."
            )

        if confidence < MIN_CONFIDENCE_THRESHOLD:
            raise ValueError("Prediction confidence is too low. Please upload a clearer leaf image.")

        return {
            "predicted_pest": predicted_pest,
            "confidence_score": confidence,
            "probabilities": {labels[idx]: float(probabilities[idx]) for idx in range(len(probabilities))},
        }
    finally:
        clear_inference_memory()


def predict_pest_from_base64(image_data: str, model_path: Optional[str] = None) -> Dict:
    """Run pest classification on base64 encoded image data."""
    image = _decode_base64_image(image_data)
    return predict_pest(image, model_path=model_path)