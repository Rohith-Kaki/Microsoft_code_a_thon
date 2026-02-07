import fitz  # PyMuPDF


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = []
        for page in doc:
            text.append(page.get_text())
        return "\n".join(text)
    except Exception:
        return pdf_bytes.decode(errors="ignore")


def extract_text_from_file(file) -> str:
    content = file.read()
    return extract_text_from_pdf_bytes(content)
