# modules/metadata.py
from PyPDF2 import PdfReader

def extract(filepath):
    """
    Extract metadata from a PDF file and return it as a dictionary.
    Adds basic anomaly checks for creation vs modification date.
    """
    results = {}
    anomalies = {}

    try:
        if filepath.lower().endswith(".pdf"):
            reader = PdfReader(filepath)
            info = reader.metadata or {}

            # Copy metadata fields
            for key, value in info.items():
                results[key] = str(value)

            # Simple anomaly check: CreationDate vs ModDate
            creation = info.get("/CreationDate")
            mod = info.get("/ModDate")
            if creation and mod and creation != mod:
                anomalies["metadata_mismatch"] = True
            else:
                anomalies["metadata_mismatch"] = False

        else:
            results["error"] = "Not a PDF file"

    except Exception as e:
        results["error"] = f"Failed to extract metadata: {str(e)}"
        anomalies["metadata_mismatch"] = False

    return {
        "metadata": results,
        "anomalies": anomalies
    }
