"""
Integrated inference pipeline for CocoScan using the Keras H5 pest classification model:
- pest_classifier_moderate.h5

Handles: image preparation -> pest model inference -> safe initial recommendations -> aggressive memory cleanup.
"""

import base64
import io
import logging
from typing import Dict, Optional, Union

import numpy as np
from PIL import Image

from model.inference import (
    clear_inference_memory,
    predict_pest,
    predict_pest_from_base64,
)

logger = logging.getLogger(__name__)

PEST_LABELS = ["Brontispa", "Healthy Coconut Leaf", "Rhinoceros Beetle", "Not a Coconut Leaf Image"]


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
    Execute the single-model pest inference pipeline:
    1. Prepare and downscale the input image safely.
    2. Run pest classification using pest_classifier_moderate.h5.
    3. Generate safe, non-invasive initial recommendations tailored to the detected pest.
    4. Aggressively clear memory and GPU caches.
    """
    try:
        logger.info("Starting pest classifier H5 inference pipeline")

        image = _to_pil_image(image_source)

        # Single pest model inference
        pest_result = predict_pest(
            image,
            model_path=pest_model_path,
        )
        predicted_pest = pest_result["predicted_pest"]
        confidence_score = pest_result["confidence_score"]

        # Safe Precautionary Initial Recommendations
        from app.recommendations import recommend_actions

        recommendations_result = recommend_actions(
            pest=predicted_pest,
        )

        final_result = {
            "success": True,
            "pest": predicted_pest,
            "possible_pest_title": f"Possible Pest: {predicted_pest}",
            "pest_confidence": confidence_score,
            "pest_probabilities": pest_result["probabilities"],
            "recommendations": recommendations_result["recommendation"],
            "precautionary_note": recommendations_result.get("precautionary_note", ""),
            "risk_level": recommendations_result.get("risk", "Low"),
            "urgency": recommendations_result.get("urgency", "Low"),
            "risk_factors": recommendations_result.get("risk_factors", []),
        }

        logger.info(
            f"Pipeline complete: Possible Pest='{predicted_pest}' ({confidence_score:.1%})"
        )
        return final_result

    except Exception as exc:
        logger.error(f"Full inference pipeline error: {str(exc)}")
        return {
            "success": False,
            "error": str(exc),
            "pest": "Unknown",
            "confidence": 0.0,
            "recommendations": [],
        }
    finally:
        clear_inference_memory()

