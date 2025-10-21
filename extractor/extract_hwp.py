from .image_ocr import run_ocr, clean_ocr_text

def extract_hwp_text(hwp_file_path):
    """
    HWP 파일 텍스트 + 이미지 순서 유지
    - pyhwp 같은 라이브러리 필요
    - 실제 내부 이미지 블록 위치를 확인해서 OCR 수행
    """
    full_text = []

    # TODO: pyhwp로 문단/이미지 블록 추출
    # 예시 pseudo-code
    blocks = get_hwp_blocks(hwp_file_path)  # 텍스트/이미지 섞인 블록 리스트

    line_buffer = []
    for b in blocks:
        if b['type'] == 'text':
            # 행 단위 합치기
            line_buffer.append(b['content'])
        elif b['type'] == 'image':
            if line_buffer:
                full_text.append(' '.join(line_buffer))
                line_buffer = []
            full_text.append(run_ocr(b['bytes']))

    if line_buffer:
        full_text.append(' '.join(line_buffer))

    return "\n\n".join([clean_ocr_text(t) for t in full_text])
