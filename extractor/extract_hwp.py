import os
import io
from PIL import Image
import olefile
import pyhwp
from .image_ocr import run_ocr


def extract(file_path: str) -> str:
    """
    HWP 파일에서 텍스트와 이미지(OCR) 추출
    """
    text_blocks = []

    # 1️⃣ 텍스트 추출 (pyhwp)
    try:
        with pyhwp.HWPReader(file_path) as hwp:
            for para in hwp.paragraphs():
                if para.text.strip():
                    text_blocks.append(para.text)
    except Exception as e:
        print(f"[WARN] Failed to extract text from {file_path}: {e}")

    # 2️⃣ 이미지 추출 (OLE 구조 접근)
    try:
        if olefile.isOleFile(file_path):
            ole = olefile.OleFileIO(file_path)
            for stream_name in ole.listdir():
                # HWP 내부 이미지 스트림은 보통 BinData/ 안에 있음
                if "BinData" in stream_name[-1]:
                    try:
                        data = ole.openstream(stream_name).read()
                        img = Image.open(io.BytesIO(data))
                        ocr_text = run_ocr(img)
                        text_blocks.append(f"\n[IMAGE_OCR:{stream_name}]\n{ocr_text}")
                    except Exception as e:
                        print(f"[WARN] Failed to OCR image in {file_path}: {e}")
                        continue
            ole.close()
    except Exception as e:
        print(f"[WARN] Failed to extract images from {file_path}: {e}")

    # 3️⃣ 결과 반환
    if not text_blocks:
        text_blocks.append("[EMPTY] No extractable content found.")
    return "\n".join(text_blocks)
