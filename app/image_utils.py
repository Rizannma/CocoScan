import io
import logging
from typing import Union
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

SAFE_MAX_DIMENSION = 1024
DEFAULT_JPEG_QUALITY = 85


def process_and_compress_image(
    image_input: Union[bytes, bytearray, io.BytesIO, Image.Image],
    max_dimension: int = SAFE_MAX_DIMENSION,
    quality: int = DEFAULT_JPEG_QUALITY,
) -> Image.Image:
    """
    Safely open, orient, downscale, and compress an incoming image right upon receipt.
    1. Fixes EXIF orientation (e.g. from mobile phone cameras).
    2. Converts to standard 3-channel RGB.
    3. Proportionally downscales large photos to max_dimension (e.g., max 1024px width/height)
       to prevent memory spikes and eliminate OOM SIGKILL crashes.
    """
    if isinstance(image_input, Image.Image):
        img = image_input
    elif isinstance(image_input, (bytes, bytearray)):
        img = Image.open(io.BytesIO(image_input))
    elif hasattr(image_input, "read"):
        img = Image.open(image_input)
    else:
        raise ValueError(f"Unsupported image input type: {type(image_input)}")

    # Correct EXIF orientation tag if present
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    # Ensure RGB color mode
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Downscale large uploaded photos (e.g., 4000x3000 down to max 1024x768)
    w, h = img.size
    if w > max_dimension or h > max_dimension:
        scale = min(max_dimension / w, max_dimension / h)
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))
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
