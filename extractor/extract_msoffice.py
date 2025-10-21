from .image_ocr import run_ocr, clean_ocr_text
from docx import Document
from pptx import Presentation
from openpyxl import load_workbook
from io import BytesIO

def extract_office_text(file_path):
    ext = file_path.split('.')[-1].lower()
    full_text = []

    if ext == "docx":
        doc = Document(file_path)
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(clean_ocr_text(para.text))
        # TODO: docx 내부 이미지 OCR
        for rel in doc.part._rels:
            rel_obj = doc.part._rels[rel]
            if "image" in rel_obj.target_ref:
                img_bytes = rel_obj.target_part.blob
                full_text.append(run_ocr(img_bytes))

    elif ext == "pptx":
        prs = Presentation(file_path)
        for slide in prs.slides:
            line_buffer = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    line_buffer.append(shape.text)
                elif shape.shape_type == 13:  # Picture
                    if line_buffer:
                        full_text.append(' '.join(line_buffer))
                        line_buffer = []
                    img_stream = BytesIO(shape.image.blob)
                    full_text.append(run_ocr(img_stream.read()))
            if line_buffer:
                full_text.append(' '.join(line_buffer))

    elif ext == "xlsx":
        wb = load_workbook(file_path, data_only=True)
        for sheet in wb.worksheets:
            for row in sheet.iter_rows(values_only=True):
                row_text = ' '.join([str(c) for c in row if c is not None])
                if row_text.strip():
                    full_text.append(clean_ocr_text(row_text))
        # TODO: xlsx 내부 이미지 OCR 필요 시 처리

    return "\n\n".join(full_text)
