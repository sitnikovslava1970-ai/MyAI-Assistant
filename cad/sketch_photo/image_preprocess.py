"""Deterministic raster normalization for sketch/photo inputs."""
from io import BytesIO
from PIL import Image, ImageFilter, ImageOps, UnidentifiedImageError

MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_IMAGE_PIXELS = 24_000_000


def load_grayscale_image(data: bytes) -> Image.Image:
    if not data:
        raise ValueError("Image payload is empty")
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Image exceeds the 15 MB upload limit")
    try:
        image = Image.open(BytesIO(data))
        if image.width * image.height > MAX_IMAGE_PIXELS:
            raise ValueError("Image exceeds the 24 megapixel processing limit")
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Unsupported or corrupted image; use PNG, JPEG or TIFF") from exc
    image = ImageOps.exif_transpose(image).convert("L")
    return ImageOps.autocontrast(image)


def edge_map(image: Image.Image, threshold: int = 48) -> Image.Image:
    if not 1 <= threshold <= 254:
        raise ValueError("threshold must be between 1 and 254")
    edges = image.filter(ImageFilter.FIND_EDGES)
    binary = edges.point(lambda value: 255 if value >= threshold else 0, mode="L")
    # FIND_EDGES treats the image boundary as an edge even for a uniform image.
    # Suppress that artificial frame so it cannot become a false CAD feature.
    width, height = binary.size
    if width and height:
        binary.paste(0, (0, 0, width, 1))
        binary.paste(0, (0, height - 1, width, height))
        binary.paste(0, (0, 0, 1, height))
        binary.paste(0, (width - 1, 0, width, height))
    return binary.convert("1")
