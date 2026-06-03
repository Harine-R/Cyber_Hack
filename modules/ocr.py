from email.mime import text

import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import re


def clean_ocr_text(text):
    # Fix common OCR mistakes
    text = re.sub(r'\bChena\b', 'Chennai', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d{2}-\d{2}-)10?98', r'\g<1>1998', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def extract_text(filepath):
    if filepath.lower().endswith(".pdf"):
        # Use PyMuPDF for PDFs
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            text += page.get_text()
    else:
        # Use Tesseract for images
        custom_config = (
            r'--oem 3 --psm 4 '
            r'-c preserve_interword_spaces=1'
        )

        text = pytesseract.image_to_string(
            Image.open(filepath),
            config=custom_config
        )
        print("\nFULL OCR TEXT:")
        print(repr(text))

        aadhaar_match = re.search(r"\d{4}[\s\n]*\d{4}[\s\n]*\d{4}", text)

        if aadhaar_match:
            print("AADHAAR FOUND:", aadhaar_match.group())
        else:
            print("AADHAAR NOT FOUND")

    # ✅ CLEAN OUTPUT HERE (IMPORTANT PART)
    cleaned_text = clean_ocr_text(text)

    return cleaned_text

def extract_fields(text):
    data = {}

    lines = text.split("\n")

    for line in lines:
        if "Name" in line and "Father" not in line:
            data["name"] = line.split(":")[-1].strip()

        elif "Father" in line:
            data["father_name"] = line.split(":")[-1].strip()

        elif "Mother" in line:
            data["mother_name"] = line.split(":")[-1].strip()

        elif "Address" in line:
            data["address"] = line.split(":")[-1].strip()

    # Aadhaar extraction
    aadhaar_match = re.search(
        r'(\d{4})\s*(\d{4})\s*(\d{4})',
        text
    )

    if aadhaar_match:
        data["aadhaar_number"] = (
            f"{aadhaar_match.group(1)} "
            f"{aadhaar_match.group(2)} "
            f"{aadhaar_match.group(3)}"
        )
    # fix known address issue
    if "address" in data:
        data["address"] = data["address"].replace("Chena", "Chennai")

    return data