"""
Integrated inference pipeline for CocoScan using the two Keras H5 models:
- pest_classifier_moderate.h5
- severity_classifier_severe_boost.h5

Handles: image preparation -> single-pass dual model inference -> dynamic recommendations -> aggressive memory cleanup.
"""

import base64
import io
import logging
from typing import Dict, Optional, Union

import numpy as np
from PIL import Image

from model.inference import (
    clear_inference_memory,
    predict_both,
    predict_pest,
    predict_pest_from_base64,
    predict_severity,
    predict_severity_from_base64,
)

logger = logging.getLogger(__name__)

PEST_LABELS = ["Brontispa", "Healthy Coconut Leaf", "Rhinoceros Beetle", "Not a Coconut Leaf Image"]
SEVERITY_LABELS = ["Mild", "Moderate", "Severe"]


def _to_pil_image(image_source: Union[str, np.ndarray, Image.Image]) -> Image.Image:
    """Normalize and downscale various image source inputs into a safe PIL Image."""
    from app.image_utils import (
        process_and_compress_image,
        InvalidImageFormatError,
        INVALID_IMAGE_ERROR_MESSAGE,
    )

    if isinstance(image_source, Image.Image):
        return process_and_compress_image(image_source, max_dimension=1024)
    if isinstance(image_source, np.ndarray):
        pil_img = Image.fromarray(image_source.astype("uint8"), "RGB")
        return process_and_compress_image(pil_img, max_dimension=1024)
    if isinstance(image_source, str):
        # Base64 string or file path
        if image_source.startswith("data:") or "," in image_source or len(image_source) > 500:
            if "," in image_source:
                image_source = image_source.split(",", 1)[1]
            try:
                image_bytes = base64.b64decode(image_source)
            except Exception as b64_err:
                raise InvalidImageFormatError(INVALID_IMAGE_ERROR_MESSAGE) from b64_err
            return process_and_compress_image(image_bytes, max_dimension=1024)
        try:
            with open(image_source, "rb") as f:
                return process_and_compress_image(f.read(), max_dimension=1024)
        except InvalidImageFormatError:
            raise
        except Exception as file_err:
            raise InvalidImageFormatError(INVALID_IMAGE_ERROR_MESSAGE) from file_err
    raise InvalidImageFormatError(INVALID_IMAGE_ERROR_MESSAGE)


def run_full_inference_pipeline(
    image_source: Union[str, np.ndarray, Image.Image],
    yolo_model_path: Optional[str] = None,
    pest_model_path: Optional[str] = None,
    severity_model_path: Optional[str] = None,
    use_lite_size: bool = False,
) -> Dict:
    """
    Execute the dual-model inference pipeline:
    1. Prepare and downscale the input image once.
    2. Run both pest and severity classification in a single optimized pass.
    3. Generate recommendations dynamically tailored to the detected pest and severity.
    4. Aggressively clear memory and GPU caches.
    """
    try:
        logger.info("Starting dual H5 model inference pipeline (pest + severity)")

        image = _to_pil_image(image_source)

        # Single-pass dual model inference (preprocessed & validated once)
        pest_result, severity_result = predict_both(
            image,
            pest_model_path=pest_model_path,
            severity_model_path=severity_model_path,
        )
        predicted_pest = pest_result["predicted_pest"]
        predicted_severity = severity_result["severity"]

        # Dynamic Recommendations based on both pest and severity
        from app.recommendations import recommend_actions

        recommendations_result = recommend_actions(
            pest=predicted_pest,
            severity=predicted_severity,
        )

        final_result = {
            "success": True,
            "pest": predicted_pest,
            "pest_confidence": pest_result["confidence_score"],
            "pest_probabilities": pest_result["probabilities"],
            "severity": predicted_severity,
            "damage_percentage": severity_result["damage_percentage"],
            "severity_confidence": severity_result["confidence_score"],
            "severity_probabilities": severity_result["probabilities"],
            "recommendations": recommendations_result["recommendation"],
            "risk_level": recommendations_result["risk"],
            "urgency": recommendations_result["urgency"],
            "risk_factors": recommendations_result["risk_factors"],
        }

        logger.info(
            f"Pipeline complete: Pest='{predicted_pest}' ({pest_result['confidence_score']:.1%}), "
            f"Severity='{predicted_severity}' ({severity_result['confidence_score']:.1%})"
        )
        return final_result

    except Exception as exc:
        logger.error(f"Full inference pipeline error: {str(exc)}")
        return {
            "success": False,
            "error": str(exc),
            "pest": "Unknown",
            "severity": "Not available",
            "confidence": 0.0,
            "recommendations": [],
        }
    finally:
        clear_inference_memory()
