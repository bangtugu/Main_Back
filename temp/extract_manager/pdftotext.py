import fitz  # PyMuPDF
import easyocr
import numpy as np
from pykospacing import Spacing
from PIL import Image
from io import BytesIO

reader = easyocr.Reader(['ko', 'en'], gpu=True)  # GPU 있으면 gpu=True 가능
spacing = Spacing()

def clean_ocr_text(raw_text):
    import re
    raw_text = re.sub(r'(?<=[가-힣])\s(?=[가-힣])', '', raw_text)  # 한글 띄어쓰기 제거
    raw_text = re.sub(r'\n+', '\n', raw_text)
    raw_text = re.sub(r'[ ]{2,}', ' ', raw_text)
    return raw_text.strip()


def run_ocr(image_bytes):
    img = Image.open(BytesIO(image_bytes)).convert('RGB')
    img_np = np.array(img)
    result = reader.readtext(img_np, detail=0)
    return "\n".join(result)


def get_image_at_block(page, bbox = []):
    dpi_set = 500
    if not bbox:
        pix = page.get_pixmap(dpi=dpi_set)
    else:
        rect = fitz.Rect(bbox)
        pix = page.get_pixmap(clip=rect, dpi=dpi_set)
    return pix.tobytes(output="png")


def pdf_to_text_with_ocr(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        page_dict = page.get_text("dict")
        blocks = page_dict["blocks"]

        # 이미지 블록이 없는 경우 → PyMuPDF 텍스트만
        has_image_block = any(b['type'] == 1 for b in blocks)
        if not has_image_block:
            text = page.get_text("text")
            full_text.append(clean_ocr_text(text))
            continue  # 바로 다음 페이지로
        
        current_y = None
        line_buffer = []

        blocks.sort(key=lambda b: (b['bbox'][1], b['bbox'][0]))
        for b in blocks:
            if b['type'] == 0:  # 텍스트
                for line in b['lines']:
                    line_text = ''.join([span['text'] for span in line['spans']])
                    y0 = line['bbox'][1]  # line 상단 Y 좌표

                    if current_y is None:
                        current_y = y0

                    if abs(y0 - current_y) <= 2:
                        # 같은 행이면 이어붙이기
                        line_buffer.append(line_text)
                    else:
                        # 새 행이면 이전 행을 합쳐서 추가
                        if line_buffer: full_text.append(' '.join(line_buffer))
                        line_buffer = [line_text]
                        current_y = y0

            elif b['type'] == 1:  # 이미지
                img_bytes = get_image_at_block(page, bbox=b['bbox'])
                if line_buffer:
                    full_text.append(' '.join(line_buffer))
                    line_buffer = []
                full_text.append(run_ocr(img_bytes))
                current_y = None
    
        if line_buffer:
            full_text.append(' '.join(line_buffer))

    doc.close()
    full_text = [clean_ocr_text(t) for t in full_text]
    full_text = [spacing(line) for line in full_text]
    return "\n\n".join(full_text)
