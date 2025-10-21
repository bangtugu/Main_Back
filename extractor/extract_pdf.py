import fitz  # PyMuPDF
from .image_ocr import run_ocr, clean_ocr_text

def get_image_at_block(page, bbox=[]):
    dpi_set = 500
    if not bbox:
        pix = page.get_pixmap(dpi=dpi_set)
    else:
        rect = fitz.Rect(bbox)
        pix = page.get_pixmap(clip=rect, dpi=dpi_set)
    return pix.tobytes(output="png")

def extract_pdf_text(pdf_bytes):
    """
    PDF 페이지 블록 순서 유지
    - 텍스트 블록: 줄 단위로 합침
    - 이미지 블록: OCR 수행
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        page_dict = page.get_text("dict")
        blocks = page_dict["blocks"]

        # 블록 정렬 (Y 좌표 기준)
        blocks.sort(key=lambda b: (b['bbox'][1], b['bbox'][0]))

        line_buffer = []
        current_y = None

        for b in blocks:
            if b['type'] == 0:  # 텍스트
                for line in b['lines']:
                    line_text = ''.join([span['text'] for span in line['spans']])
                    y0 = line['bbox'][1]

                    if current_y is None:
                        current_y = y0

                    if abs(y0 - current_y) <= 2:
                        line_buffer.append(line_text)
                    else:
                        if line_buffer:
                            full_text.append(' '.join(line_buffer))
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
    # 마지막 정리
    full_text = [clean_ocr_text(t) for t in full_text]
    return "\n\n".join(full_text)
