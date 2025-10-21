import fitz  # pymupdf
from paddleocr import PaddleOCR
from pykospacing import Spacing
import numpy as np
from PIL import Image
from io import BytesIO
import cv2  # NumPy array BGR 변환 위해

# PaddleOCR 초기화
ocr = PaddleOCR(use_angle_cls=True, lang='korean')
spacing = Spacing()

# PaddleOCR 결과 파싱
def paddle_parse(result):
    if not result or not result[0]:
        return ""
    texts = result[0].get('rec_texts', [])
    return "\n".join(texts)

# PDF에서 텍스트와 이미지 추출
def pdf_to_text_with_ocr(pdf_bytes):
    extracted_text = ""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    try:
        for page_index, page in enumerate(doc, start=1):
            page_text = page.get_text()
            if page_text:
                extracted_text += page_text.strip() + "\n"

            images = page.get_images(full=True)
            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                pil_img = Image.open(BytesIO(image_bytes)).convert('RGB')
                img_np = np.array(pil_img)
                img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                
                result = ocr.ocr(img_cv)
                ocr_text = paddle_parse(result)
                if ocr_text:
                    extracted_text += ocr_text + "\n"

            extracted_text += f"\n--- Page {page_index} End ---\n\n"

    finally:
        doc.close()

    # PyKoSpacing 적용
    lines = extracted_text.splitlines()
    corrected_lines = [spacing(line) if line.strip() else "" for line in lines]
    return "\n".join(corrected_lines)