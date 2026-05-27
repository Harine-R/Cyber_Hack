import hashlib
import fitz  # PyMuPDF

def verify(filepath, official_records):
    results = {"signature_anomaly": False, "signature_optional": False}

    # Open the PDF
    doc = fitz.open(filepath)
    page = doc[-1]  # assume signature is on the last page

    # Define the region to crop (adjust coordinates for your slip layout)
    rect = fitz.Rect(100, 700, 400, 800)
    pix = page.get_pixmap(clip=rect)
    image_bytes = pix.tobytes()

    # If region is empty or too small, mark as optional
    if not image_bytes or len(image_bytes) < 1000:
        results["signature_optional"] = True
    else:
        # Compute hash of cropped region
        signature_hash = hashlib.sha256(image_bytes).hexdigest()
        hr_signature_hash = official_records.get("HR01", {}).get("signature_hash")

        # Compare with HR reference
        if hr_signature_hash and signature_hash != hr_signature_hash:
            results["signature_anomaly"] = True

    return results
