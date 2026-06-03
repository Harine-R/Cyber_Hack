import requests

url = "http://127.0.0.1:8000/upload_and_analyze"

# Multiple files
files = [
    ("files", open(r"C:\Users\Vijayashree B\Downloads\Sample Salary Slip2.pdf", "rb")),
    ("files", open(r"C:\Users\Vijayashree B\Downloads\Sample Salary Slip2.png", "rb")),
    ("files", open(r"C:\Users\Vijayashree B\Downloads\aadhar1.png", "rb")),
    ("files", open(r"C:\Users\Vijayashree B\Downloads\mock_identity_document_v3 (1).pdf", "rb")),
    ("files", open(r"C:\Users\Vijayashree B\Downloads\aadhar2.png", "rb"))
]

response = requests.post(url, files=files)
data = response.json()

print("Message:", data["message"])
for file in data["files"]:
    print("\n--- File Analysis ---")
    print("Filename:", file["filename"])
    print("Hash:", file["hash"])
    print("Fraud Score:", file["fraud_score"])
    print("Risk Level:", file["risk_level"])
    print("Explanations:", ", ".join(file["explanations"]))

    print("Forensic Checks:")
    for k, v in file.get("forensic", {}).items():
        print(f"  {k}: {v}")

    print("Validation Results:")
    for k, v in file.get("validation", {}).items():
        print(f"  {k}: {v}")

    print("Signature Checks:")
    for k, v in file.get("signature", {}).items():
        print(f"  {k}: {v}")

    print("Metadata:")
    metadata = file.get("metadata", {})
    # PDFs have nested metadata dict
    if "metadata" in metadata:
        for k, v in metadata["metadata"].items():
            print(f"  {k}: {v}")
        print("Metadata Anomalies:")
        for k, v in metadata.get("anomalies", {}).items():
            print(f"  {k}: {v}")
    else:
        # Images/Excel just have a source field
        for k, v in metadata.items():
            print(f"  {k}: {v}")
