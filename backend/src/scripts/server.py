import numpy as np #type: ignore
from PIL import Image #type: ignore
import io
from mcp.types import ImageContent

@mcp.tool() #type: ignore
def generate_noise_image(
    width: int = 50,
    height: int = 50
):
    """
    Generate a noise image and return it as ImageContent.
    """
    # Create RGB noise
    noise = np.random.randint(
        0, 256, (height, width, 3), dtype=np.uint8
    )

    img = Image.fromarray(noise, "RGB")

    # Encode as PNG
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    return ImageContent(
        type="image",
        data=str(buf.getvalue()),
        mimeType="image/png"
    )