import io
import logging
from typing import Any, Optional, Set, Union
from PIL import Image, ImageFile, ImageOps, UnidentifiedImageError

setattr(ImageFile, "LOAD_TRUNCATED_IMAGES", True)

logger = logging.getLogger(__name__)

# Safely register pillow_heif for HEIC/HEIF decoding if installed
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception as _heif_init_err:
    logger.warning(f"pillow_heif opener registration failed (HEIC support unavailable): {_heif_init_err}")

SAFE_MAX_DIMENSION = 1024
DEFAULT_JPEG_QUALITY = 85

INVALID_IMAGE_ERROR_MESSAGE = (
    "Invalid image file format. Please upload a valid JPG, JPEG, PNG, or HEIC image."
)
STORAGE_LIMIT_ERROR_MESSAGE = (
    "Storage limit reached. Unable to save the image at this time. Please contact the administrator."
)
ALLOWED_IMAGE_FORMATS: Set[str] = {"JPEG", "JPG", "PNG", "HEIC", "HEIF"}


class InvalidImageFormatError(ValueError):
    """Raised when an uploaded file cannot be decoded or is not a valid JPG, JPEG, or PNG image."""

    def __init__(self, message: str = INVALID_IMAGE_ERROR_MESSAGE):
        super().__init__(message)
        self.message = message


class StorageLimitExceededError(Exception):
    """Raised when Supabase Storage capacity limits / quotas are exceeded."""

    def __init__(self, message: str = STORAGE_LIMIT_ERROR_MESSAGE):
        super().__init__(message)
        self.message = message


def is_storage_limit_error(error_val: Any) -> bool:
    """
    Detect if an error response or exception indicates Supabase storage bucket full / quota exceeded.
    Checks HTTP status codes (413, 507) and error message texts.
    """
    if not error_val:
        return False

    # Check status codes
    status_code = None
    if isinstance(error_val, dict):
        status_code = (
            error_val.get("statusCode")
            or error_val.get("status_code")
            or error_val.get("code")
            or error_val.get("status")
        )
    else:
        status_code = (
            getattr(error_val, "status_code", None)
            or getattr(error_val, "statusCode", None)
            or getattr(error_val, "code", None)
            or getattr(error_val, "status", None)
        )

    if status_code in (413, 507, "413", "507"):
        return True

    # Extract all text from error object / dict / exception
    error_parts = []
    if isinstance(error_val, dict):
        for k in ("error", "message", "msg", "details", "description", "hint"):
            val = error_val.get(k)
            if val:
                error_parts.append(str(val))
    else:
        if hasattr(error_val, "message"):
            error_parts.append(str(error_val.message))
        if hasattr(error_val, "args"):
            error_parts.extend(str(a) for a in error_val.args)
        error_parts.append(str(error_val))

    full_text = " ".join(error_parts).lower()

    direct_keywords = [
        "quota",
        "exceeded",
        "storage limit",
        "limit reached",
        "payload too large",
        "insufficient storage",
        "capacity",
        "bucket full",
        "storage full",
        "out of space",
        "quota_exceeded",
        "entity too large",
        "resource limit",
        "507",
        "413",
    ]

    for kw in direct_keywords:
        if kw in full_text:
            return True

    if "limit" in full_text and any(
        w in full_text for w in ("storage", "reached", "quota", "exceed", "capacity")
    ):
        return True

    return False


def process_and_compress_image(
    image_input: Union[bytes, bytearray, io.BytesIO, Image.Image],
    max_dimension: int = SAFE_MAX_DIMENSION,
    quality: int = DEFAULT_JPEG_QUALITY,
    allowed_formats: Optional[Union[set, list, tuple]] = None,
) -> Image.Image:
    """
    Safely open, orient, downscale, and compress an incoming image right upon receipt.
    1. Validates and decodes image stream (catches invalid/corrupted files and unsupported formats).
    2. Fixes EXIF orientation (e.g. from mobile phone cameras).
    3. Converts to standard 3-channel RGB.
    4. Proportionally downscales large photos to max_dimension (e.g., max 1024px width/height)
       to prevent memory spikes and eliminate OOM SIGKILL crashes.
    """
    if allowed_formats is None:
        valid_formats = ALLOWED_IMAGE_FORMATS
    else:
        valid_formats = {f.upper() for f in allowed_formats}

    if isinstance(image_input, Image.Image):
        img = image_input
        try:
            img.load()
        except Exception as e:
            raise InvalidImageFormatError(INVALID_IMAGE_ERROR_MESSAGE) from e
    else:
        try:
            if isinstance(image_input, (bytes, bytearray)):
                if not image_input:
                    raise InvalidImageFormatError(INVALID_IMAGE_ERROR_MESSAGE)
                stream = io.BytesIO(image_input)
                img = Image.open(stream)
            elif hasattr(image_input, "read"):
                stream_content = image_input.read()
                if not stream_content:
                    raise InvalidImageFormatError(INVALID_IMAGE_ERROR_MESSAGE)
                if hasattr(image_input, "seek"):
                    try:
                        image_input.seek(0)
                    except Exception:
                        pass
                img = Image.open(io.BytesIO(stream_content))
            else:
                raise InvalidImageFormatError(INVALID_IMAGE_ERROR_MESSAGE)

            # Format validation
            detected_format = (img.format or "").upper()
            if detected_format and valid_formats:
                if detected_format not in valid_formats:
                    raise InvalidImageFormatError(INVALID_IMAGE_ERROR_MESSAGE)

            # Force load image data to detect truncation or stream corruption early
            img.load()
        except InvalidImageFormatError:
            raise
        except (UnidentifiedImageError, OSError, IOError, ValueError, SyntaxError, Exception) as e:
            logger.warning(f"Failed to decode image input: {e}")
            raise InvalidImageFormatError(INVALID_IMAGE_ERROR_MESSAGE) from e

    # Correct EXIF orientation tag if present
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    # Ensure RGB color mode
    try:
        if img.mode != "RGB":
            img = img.convert("RGB")
    except Exception as e:
        raise InvalidImageFormatError(INVALID_IMAGE_ERROR_MESSAGE) from e

    # Downscale large uploaded photos (e.g., 4000x3000 down to max 1024x768)
    w, h = img.size
    if w > max_dimension or h > max_dimension:
        scale = min(max_dimension / w, max_dimension / h)
        new_w = max(1, round(w * scale))
        new_h = max(1, round(h * scale))
        logger.info(f"Downscaling uploaded photo from {w}x{h} to {new_w}x{new_h} (max {max_dimension}px).")
        img = img.resize((new_w, new_h), Image.Resampling.BILINEAR)

    return img


def compress_image_to_bytes(
    image: Image.Image,
    max_dimension: int = SAFE_MAX_DIMENSION,
    quality: int = DEFAULT_JPEG_QUALITY,
    format: str = "JPEG",
) -> bytes:
    """Compress a PIL Image to JPEG bytes with dimension capping and quality optimization."""
    processed = process_and_compress_image(image, max_dimension=max_dimension, quality=quality)
    buffer = io.BytesIO()
    processed.save(buffer, format=format, quality=quality, optimize=True)
    return buffer.getvalue()

