import pytesseract
from PIL import Image
import fitz  # PyMuPDF

def extract_text(filepath):
    if filepath.lower().endswith(".pdf"):
        # Use PyMuPDF for PDFs
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    else:
        # Use Tesseract for images
        return pytesseract.image_to_string(Image.open(filepath))
