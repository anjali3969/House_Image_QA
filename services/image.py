import io  #bytes into file-like object

from fastapi import HTTPException #for error response
from PIL import Image  # image validation


ALLOWED_TYPES = ["image/jpeg", "image/png", "image/jpg"] #allowed MIME types.

#Function: validate_image (file type, size & integrity)
async def validate_image(file, image_bytes):
    
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Invalid image format")

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty image file")

    try:
        img = Image.open(io.BytesIO(image_bytes)) #Converts raw bytes into image object.
        img.verify()
        return True
    except Exception:
        raise HTTPException(status_code=400, detail="Corrupted image")
