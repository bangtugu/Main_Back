import easyocr
import numpy as np
from PIL import Image
from io import BytesIO
import re

reader = easyocr.Reader(['ko', 'en'], gpu=False)  # GPU 있으면 gpu=True 가능

def clean_ocr_text(raw_text):
    raw_text = re.sub(r'(?<=[가-힣])\s(?=[가-힣])', '', raw_text)
    raw_text = re.sub(r'\n+', '\n', raw_text)
    raw_text = re.sub(r'[ ]{2,}', ' ', raw_text)
    return raw_text.strip()

def run_ocr(image_bytes):
    img = Image.open(BytesIO(image_bytes)).convert('RGB')
    img_np = np.array(img)
    result = reader.readtext(img_np, detail=0)
    return clean_ocr_text("\n".join(result))
