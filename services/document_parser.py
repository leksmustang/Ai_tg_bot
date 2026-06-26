import io
import PyPDF2
import docx

def extract_text_from_pdf(data: bytes) -> str:
    reader = PyPDF2.PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def extract_text_from_docx(data: bytes) -> str:
    doc = docx.Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs)

def extract_text_from_txt(data: bytes) -> str:
    return data.decode("utf-8", errors="ignore")