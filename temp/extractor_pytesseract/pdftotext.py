import fitz  # PyMuPDF
from PIL import Image
from pykospacing import Spacing
import pytesseract
import io

pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'
spacing = Spacing()

def clean_ocr_text(raw_text):
    import re
    raw_text = re.sub(r'(?<=[가-힣])\s(?=[가-힣])', '', raw_text)
    raw_text = re.sub(r'\n+', '\n', raw_text)
    raw_text = re.sub(r'[ ]{2,}', ' ', raw_text)
    return raw_text.strip()

def get_image_from_block(page, bbox):
    rect = fitz.Rect(bbox)
    pix = page.get_pixmap(clip=rect, dpi=300)
    return pix.tobytes(output="png")

def pdf_to_text_with_ocr(pdf_bytes, lang='eng+kor', y_threshold=2):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        page_dict = page.get_text("dict")
        blocks = page_dict["blocks"]

        has_image_block = any(b['type'] == 1 for b in blocks)
        if not has_image_block:
            text = page.get_text("text")
            full_text.append(clean_ocr_text(text))
            continue

        # y좌표 기준 정렬, y 같으면 x좌표 기준
        blocks.sort(key=lambda b: (b['bbox'][1], b['bbox'][0]))

        prev_y = None
        line_accum = ""

        for b in blocks:
            if b['type'] == 0:  # 텍스트
                for line in b['lines']:
                    line_text = ''.join([span['text'] for span in line['spans']]).strip()
                    y = line['bbox'][1]

                    if prev_y is None:
                        line_accum = line_text
                        prev_y = y
                    elif abs(y - prev_y) <= y_threshold:
                        line_accum += " " + line_text
                    else:
                        full_text.append(line_accum)
                        line_accum = line_text
                        prev_y = y

            elif b['type'] == 1:  # 이미지
                if line_accum:
                    full_text.append(line_accum)
                    line_accum = ""
                    prev_y = None

                img_bytes = get_image_from_block(page, b['bbox'])
                pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                ocr_text = pytesseract.image_to_string(pil_img, lang=lang)
                full_text.append(ocr_text.strip())

        if line_accum:
            full_text.append(line_accum)

    doc.close()
    full_text = [clean_ocr_text(t) for t in full_text]
    full_text = [spacing(line) for line in full_text]
    return "\n\n".join(full_text)
