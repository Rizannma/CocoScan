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
PEST_MODEL_FILE_NAME = "pest_classifier_moderate.h5"
SEVERITY_MODEL_FILE_NAME = "severity_classifier_severe_boost.h5"

# The trained 4-class pest model output order:
# [Brontispa, Healthy Coconut Leaf, Rhinoceros Beetle, Not a Coconut Leaf Image]
PEST_LABELS = ["Brontispa", "Healthy Coconut Leaf", "Rhinoceros Beetle", "Not a Coconut Leaf Image"]

# The trained 3-class severity model output order:
# [Mild, Moderate, Severe]
SEVERITY_LABELS = ["Mild", "Moderate", "Severe"]

# Minimum confidence cutoff for acceptable predictions
MIN_CONFIDENCE_THRESHOLD = 0.25
NOT_COCONUT_LEAF_LABEL = "Not a Coconut Leaf Image"
UNKNOWN_LABEL_BASE = NOT_COCONUT_LEAF_LABEL
MIN_IMAGE_DIMENSION = 32
GREEN_MEAN_THRESHOLD = 20.0
LEAF_GREEN_RATIO_THRESHOLD = 0.05
TARGET_SIZE = (224, 224)

# Caches for loaded Keras models (thread-safe singletons)
_cached_pest_model = None
_cached_pest_path: Optional[Path] = None
_cached_severity_model = None
_cached_severity_path: Optional[Path] = None
_model_lock = threading.Lock()


def get_pest_model_path(model_path: Optional[str] = None) -> Path:
    target_path = Path(model_path) if model_path else MODEL_DIR / PEST_MODEL_FILE_NAME
    if not target_path.exists():
        raise FileNotFoundError(f"Pest H5 model not found: {target_path}")
    return target_path


def get_severity_model_path(model_path: Optional[str] = None) -> Path:
    target_path = Path(model_path) if model_path else MODEL_DIR / SEVERITY_MODEL_FILE_NAME
    if not target_path.exists():
        raise FileNotFoundError(f"Severity H5 model not found: {target_path}")
    return target_path


# Backward compatibility alias
get_model_path = get_pest_model_path


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
                _cached_pest_model = _load_keras_model(resolved_path)
                _cached_pest_path = resolved_path
    return _cached_pest_model


def _get_severity_model(model_path: Optional[str] = None):
    global _cached_severity_model, _cached_severity_path
    resolved_path = get_severity_model_path(model_path)
    if _cached_severity_model is None or _cached_severity_path != resolved_path:
        with _model_lock:
            if _cached_severity_model is None or _cached_severity_path != resolved_path:
                logger.info(f"Loading severity classifier model globally from {resolved_path}")
                _cached_severity_model = _load_keras_model(resolved_path)
                _cached_severity_path = resolved_path
    return _cached_severity_model


def preload_models(
    pest_model_path: Optional[str] = None,
    severity_model_path: Optional[str] = None,
) -> Tuple[Any, Any]:
    """
    Preload both pest and severity models globally once at startup.
    This prevents high latency, memory allocation spikes, and Out Of Memory (OOM) errors during inference requests.
    """
    pest_model = _get_pest_model(pest_model_path)
    severity_model = _get_severity_model(severity_model_path)
    logger.info("Global H5 models successfully preloaded and ready for inference.")
    return pest_model, severity_model


def _softmax(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float32)
    values = values - np.max(values)
    exp_values = np.exp(values)
    return exp_values / np.sum(exp_values)


def _decode_base64_image(image_data: str) -> Image.Image:
    if "," in image_data:
        image_data = image_data.split(",", 1)[1]
    image_bytes = base64.b64decode(image_data)
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


def _validate_leaf_image(image: Image.Image):
    rgb_image = image.convert("RGB") if isinstance(image, Image.Image) else image
    array = np.asarray(rgb_image).astype(np.float32)
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
    """
    if not isinstance(image, Image.Image):
        raise ValueError(f"Expected PIL Image instance, got {type(image)}")

    # Ensure image is in standard 3-channel RGB
    rgb_image = image.convert("RGB")

    # Resize to standard dimensions (224, 224) using bilinear resampling
    resized = rgb_image.resize(TARGET_SIZE, Image.Resampling.BILINEAR)

    # Convert to float32 NumPy array and normalize to [0.0, 1.0]
    array = np.asarray(resized, dtype=np.float32)

    if array.ndim == 2:
        array = np.stack([array] * 3, axis=-1)
    elif array.ndim == 3 and array.shape[-1] > 3:
        array = array[..., :3]
    elif array.ndim == 3 and array.shape[-1] == 1:
        array = np.repeat(array, 3, axis=-1)

    array = array / 255.0

    if array.ndim == 3:
        array = np.expand_dims(array, axis=0)

    # Guarantee contiguous C-order buffer in memory
    array = np.ascontiguousarray(array, dtype=np.float32)

    # If PyTorch is available, convert to contiguous torch.Tensor for PyTorch backend
    try:
        import torch
        tensor = torch.from_numpy(array).contiguous().float()
        return tensor
    except Exception:
        return array


def _run_model_forward(model, input_tensor: Union[np.ndarray, Any]) -> np.ndarray:
    """
    Execute model prediction and return 1D numpy array of probabilities.
    Runs with zero autograd overhead / inference mode and cleans up memory to prevent OOM.
    """
    try:
        import torch
        if hasattr(model, "eval") and callable(getattr(model, "eval")):
            model.eval()

        ctx = torch.inference_mode() if hasattr(torch, "inference_mode") else torch.no_grad()
        with ctx:
            if isinstance(input_tensor, np.ndarray):
                tensor = torch.from_numpy(np.ascontiguousarray(input_tensor, dtype=np.float32)).contiguous().float()
            else:
                tensor = input_tensor

            # If model has parameters on a specific device, match device
            try:
                if hasattr(model, "parameters"):
                    param = next(model.parameters(), None)
                    if param is not None and hasattr(tensor, "device") and tensor.device != param.device:
                        tensor = tensor.to(param.device)
            except Exception:
                pass

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

    # Free references and run garbage collection
    gc.collect()

    return preds.astype(np.float32)


def predict_pest(image: Image.Image, model_path: Optional[str] = None) -> Dict:
    """
    Run pest classification on a PIL Image using pest_classifier_moderate.h5.
    """
    _validate_leaf_image(image)
    model = _get_pest_model(model_path)
    input_tensor = _prepare_input(image)
    probabilities = _run_model_forward(model, input_tensor)

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


def predict_severity(image: Image.Image, model_path: Optional[str] = None) -> Dict:
    """
    Run severity classification on a PIL Image using severity_classifier_severe_boost.h5.
    """
    _validate_leaf_image(image)
    model = _get_severity_model(model_path)
    input_tensor = _prepare_input(image)
    probabilities = _run_model_forward(model, input_tensor)

    label_index = int(np.argmax(probabilities))
    labels = _get_labels(len(probabilities), SEVERITY_LABELS)
    predicted_severity = labels[label_index]
    confidence = float(probabilities[label_index])

    # Standard damage percentage mapping
    damage_map = {"Mild": 25, "Moderate": 50, "Severe": 75}
    damage_percentage = damage_map.get(predicted_severity, 50)

    return {
        "severity": predicted_severity,
        "damage_percentage": damage_percentage,
        "confidence_score": confidence,
        "probabilities": {labels[idx]: float(probabilities[idx]) for idx in range(len(probabilities))},
    }


def _get_labels(num_classes: int, base_labels: List[str]) -> List[str]:
    if num_classes <= len(base_labels):
        return base_labels[:num_classes]
    extra_labels = [UNKNOWN_LABEL_BASE] * (num_classes - len(base_labels))
    return base_labels + extra_labels


def predict_pest_from_base64(image_data: str, model_path: Optional[str] = None) -> Dict:
    image = _decode_base64_image(image_data)
    return predict_pest(image, model_path=model_path)


def predict_severity_from_base64(image_data: str, model_path: Optional[str] = None) -> Dict:
    image = _decode_base64_image(image_data)
    return predict_severity(image, model_path=model_path)


def predict_all_from_base64(
    image_data: str,
    pest_model_path: Optional[str] = None,
    severity_model_path: Optional[str] = None,
) -> Tuple[Dict, Dict]:
    """Execute both pest classification and severity classification from base64 image data."""
    image = _decode_base64_image(image_data)
    pest_result = predict_pest(image, model_path=pest_model_path)
    severity_result = predict_severity(image, model_path=severity_model_path)
    return pest_result, severity_result