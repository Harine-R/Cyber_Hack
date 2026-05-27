# modules/forensic.py
from PyPDF2 import PdfReader

def check(filepath):
    results = {
        "metadata_mismatch": False,
        "compression_anomaly": False,
        "font_issue": False
    }

    try:
        reader = PdfReader(filepath)
        info = reader.metadata

        # Example anomaly: creation vs modification date mismatch
        if info.get("/CreationDate") and info.get("/ModDate"):
            if info["/CreationDate"] != info["/ModDate"]:
                results["metadata_mismatch"] = True

        # Example anomaly: font issues (placeholder logic)
        # You can expand this with real font checks
        if "TimesNewRoman" not in str(reader.pages[0].extract_text()):
            results["font_issue"] = True

    except Exception:
        # If PDF parsing fails, mark compression anomaly
        results["compression_anomaly"] = True

    return results
