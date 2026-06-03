from fastapi import FastAPI, UploadFile, File
import os
import hashlib
from typing import List
from modules import ocr, metadata, forensic, validation, signature, blockchain, scoring, explain
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Users\Vijayashree B\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
)
import pandas as pd


app = FastAPI()
UPLOAD_FOLDER = "data/documents"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.get("/")
def home():
    return {"message": "✅ Document Fraud Detection API is running. Use /upload_and_analyze endpoint."}

# Example records (replace with DB later)
official_records = {
    "E001": {"name": "John Doe", "salary": 50000, "department": "Finance", "phone_number": "9876543210", "date_of_joining": "2020-01-15", "bank_account": "1234567890"},
    "E002": {"name": "Jane Smith", "salary": 60000, "department": "HR", "phone_number": "9123456780", "date_of_joining": "2019-03-10", "bank_account": "9876543210"},
    "E003": {"name": "Harine", "salary": 45000, "department": "IT", "phone_number": "9988776655", "date_of_joining": "2021-07-01", "bank_account": "1122334455"},
    "HR01": {"name": "Alice HR", "signature_hash": "a8735934125fa7bd64dd9549e89914192fdcf56e3c121097bc22c80f09317f23"}
}

# Detect file type
def get_file_type(filename: str):
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        return "pdf"
    elif ext in [".png", ".jpg", ".jpeg"]:
        return "image"
    elif ext in [".xlsx", ".xls"]:
        return "excel"
    else:
        return "unsupported"

# Extract content depending on type (with robust error handling)
def extract_content(filepath: str, file_type: str):
    try:
        if file_type == "pdf":
            # Try direct text extraction first (digital PDF)
            text = ""
            page_count = 0
            try:
                with fitz.open(filepath) as doc:
                    page_count = doc.page_count
                    for page in doc:
                        page_text = page.get_text()
                        if page_text and page_text.strip():
                            text += page_text + "\n"
            except Exception:
                # If PyMuPDF fails for some reason, continue to OCR fallback below
                text = ""

            # If no text found, fall back to OCR (scanned PDF)
            if not text.strip():
                ocr_text = ""
                try:
                    with fitz.open(filepath) as doc:
                        page_count = doc.page_count
                        for page in doc:
                            pix = page.get_pixmap()
                            mode = "RGB" if pix.n < 4 else "RGBA"
                            img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                            ocr_text += pytesseract.image_to_string(img) + "\n"
                except Exception as e:
                    return {"error": f"PDF OCR failed: {str(e)}"}
                return {"text": ocr_text, "pages": page_count, "ocr_used": True}
            # Return extracted text and basic PDF metadata
            try:
                with fitz.open(filepath) as doc:
                    pdf_meta = doc.metadata or {}
            except Exception:
                pdf_meta = {}
            return {"text": text, "pages": page_count, "ocr_used": False, "pdf_metadata": pdf_meta}

        elif file_type == "image":
            try:
                img = Image.open(filepath)

        # Use your custom OCR module
                text = ocr.extract_text(filepath)

                if not text.strip():
                    return {"error": "OCR failed: No readable text found"}

                return {"text": text, "img": img}

            except Exception as e:
                return {"error": f"OCR failed: {str(e)}"}

        elif file_type == "excel":
            try:
                # Read Excel and normalize headers
                xls = pd.ExcelFile(filepath)
                sheet_names = xls.sheet_names
                # Read first sheet by default for analysis; you can extend to multiple sheets
                df = pd.read_excel(xls, sheet_name=0)
                df.columns = df.columns.astype(str).str.strip().str.lower()
                df = df.loc[:, ~df.columns.duplicated()]
                records = df.to_dict(orient="records")
                return {"df": df, "records": records, "sheet_names": sheet_names}
            except Exception as e:
                return {"error": f"Excel parsing failed: {str(e)}"}

        else:
            return {"error": "Unsupported file type"}
    except Exception as e:
        return {"error": f"Content extraction failed: {str(e)}"}

def detect_doc_type(text):
    text = text.lower()

    if (
        "uidai" in text
        or "aadhaar" in text
        or "government of india" in text
        or "date of birth" in text
        or validation.parse_aadhaar(text)
    ):
        return "aadhaar"

    if "salary" in text or "employee" in text:
        return "employee"

    return "unknown"

# Fraud check logic (returns structured analysis for each file)
def run_fraud_checks(content, file_type, filepath: str, official_records: dict):
    # If extraction returned an error dict, propagate as analysis error
    if isinstance(content, dict) and "error" in content:
        return {"fraud_score": 0, "risk_level": "Error", "explanations": [content["error"]], "forensic": {}, "validation": {}, "signature": {}, "metadata": {}}

    # PDF branch
    if file_type == "pdf":
        try:
            # content is expected to be a dict with 'text'
            text = content.get("text", "") if isinstance(content, dict) else str(content)
            forensic_results = forensic.check(filepath)
            metadata_results = metadata.extract(filepath)
            if "date of birth" in text.lower():
                validation_results = validation.verify_aadhaar(text)
            else:
                validation_results = validation.cross_validate(text, official_records)
            signature_results = signature.verify(filepath, official_records)

            fraud_score, risk_level = scoring.calculate(
                forensic_results, validation_results, metadata_results, signature_results
            )

            explanations = explain.generate(fraud_score, forensic_results, validation_results)

            # Add PDF-specific metadata summary
            pdf_meta_summary = {}
            if isinstance(content, dict):
                pdf_meta_summary["pages"] = content.get("pages")
                pdf_meta_summary["ocr_used"] = content.get("ocr_used", False)
                if "pdf_metadata" in content:
                    pdf_meta_summary.update(content.get("pdf_metadata", {}))

            return {
                "fraud_score": fraud_score,
                "risk_level": risk_level,
                "explanations": explanations,
                "forensic": forensic_results,
                "validation": validation_results,
                "signature": signature_results,
                "metadata": {"source": "PDF file", **(metadata_results or {}), **pdf_meta_summary}
            }
        except Exception as e:
            return {"fraud_score": 0, "risk_level": "Error", "explanations": [f"PDF analysis failed: {str(e)}"], "forensic": {}, "validation": {}, "signature": {}, "metadata": {}}

    # Image branch
    elif file_type == "image":
        try:
            text = content.get("text", "") if isinstance(content, dict) else str(content)
            img = content.get("img") if isinstance(content, dict) else None

            doc_type = detect_doc_type(text)

            if doc_type == "aadhaar":
                validation_results = validation.verify_aadhaar(text)
            else:
                validation_results = validation.cross_validate(
                    text,
                    official_records
                )

            fraud_score = 0
            explanations = []

            if validation_results.get("salary_mismatch"):
                fraud_score += 50
                explanations.append("Salary mismatch detected in OCR text")

            if validation_results.get("employee_not_found"):
                fraud_score += 100
                explanations.append("Employee not found in OCR text")

            if validation_results.get("aadhaar_missing"):
                fraud_score += 40
                explanations.append("Aadhaar number missing")

            if validation_results.get("dob_missing"):
                fraud_score += 10
                explanations.append("Date of birth missing")

            if validation_results.get("gender_missing"):
                fraud_score += 10
                explanations.append("Gender missing")

            if validation_results.get("uidai_keywords_missing"):
                fraud_score += 20
                explanations.append("UIDAI keywords missing")

            risk_level = "Low Risk" if fraud_score < 30 else "Medium Risk" if fraud_score < 60 else "High Risk"

            img_meta = {}
            if img:
                try:
                    img_meta = {
                        "format": img.format,
                        "mode": img.mode,
                        "size": img.size,
                        "dpi": img.info.get("dpi", "unknown")
                    }
                except Exception:
                    img_meta = {"format": getattr(img, "format", None), "size": getattr(img, "size", None)}

            return {
                "fraud_score": fraud_score,
                "risk_level": risk_level,
                "explanations": explanations,
                "forensic": {"ocr_text_preview": text[:200]},
                "validation": validation_results,
                "signature": {"signature_optional": True},
                "metadata": {"source": "Image file", **img_meta}
            }
        except Exception as e:
            return {"fraud_score": 0, "risk_level": "Error", "explanations": [f"Image analysis failed: {str(e)}"], "forensic": {}, "validation": {}, "signature": {}, "metadata": {}}

    # Excel branch
    elif file_type == "excel":
        try:
            df = content.get("df")
            records = content.get("records", [])
            sheet_names = content.get("sheet_names", [])
            row_count, col_count = (df.shape if df is not None else (0, 0))

            fraud_score = 0
            explanations = []
            anomalies = []
            mismatch_count = 0
            missing_id_count = 0

            for row in records:
                emp_id = row.get("employeeid") or row.get("employee_id") or row.get("id")
                salary = row.get("salary")
                if salary is not None:
                    try:
                        salary_val = float(salary)
                    except Exception:
                        salary_val = None
                    if salary_val is not None and (salary_val < 10000 or salary_val > 200000):
                        fraud_score += 20
                        explanations.append(f"Salary out of range for {emp_id}")
                        anomalies.append({"row": row, "issue": "Salary out of range"})
                if not emp_id:
                    fraud_score += 10
                    explanations.append("Missing EmployeeID")
                    missing_id_count += 1
                if emp_id and emp_id in official_records:
                    official_salary = official_records[emp_id].get("salary")
                    if salary is not None and official_salary is not None:
                        try:
                            if float(salary) != float(official_salary):
                                fraud_score += 15
                                explanations.append(f"Salary mismatch for {emp_id}")
                                mismatch_count += 1
                        except Exception:
                            # If conversion fails, record as anomaly
                            anomalies.append({"row": row, "issue": "Salary value parse error"})

            risk_level = "Low Risk" if fraud_score < 30 else "Medium Risk" if fraud_score < 60 else "High Risk"

            duplicate_ids = 0
            try:
                if df is not None and "employeeid" in df.columns:
                    duplicate_ids = int(df["employeeid"].duplicated().sum())
            except Exception:
                duplicate_ids = 0

            return {
                "fraud_score": fraud_score,
                "risk_level": risk_level,
                "explanations": explanations,
                "forensic": {"excel_checks": anomalies, "duplicate_ids": duplicate_ids},
                "validation": {"rows_checked": len(records), "salary_mismatches": mismatch_count, "missing_ids": missing_id_count},
                "signature": {"signature_optional": True},
                "metadata": {"source": "Excel file", "sheet_names": sheet_names, "rows": row_count, "columns": col_count}
            }
        except Exception as e:
            return {"fraud_score": 0, "risk_level": "Error", "explanations": [f"Excel analysis failed: {str(e)}"], "forensic": {}, "validation": {}, "signature": {}, "metadata": {}}

    else:
        return {"fraud_score": 0, "risk_level": "Unknown", "explanations": ["Unsupported type"], "forensic": {}, "validation": {}, "signature": {}, "metadata": {}}

# Unified endpoint
@app.post("/upload_and_analyze")
async def upload_and_analyze(files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        # Save uploaded file
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        try:
            with open(filepath, "wb") as f:
                f.write(await file.read())
        except Exception as e:
            results.append({
                "filename": file.filename,
                "hash": None,
                "fraud_score": 0,
                "risk_level": "Error",
                "explanations": [f"Failed to save file: {str(e)}"],
                "forensic": {},
                "validation": {},
                "signature": {},
                "metadata": {}
            })
            continue

        # Compute file hash and log to blockchain (best-effort)
        try:
            with open(filepath, "rb") as fh:
                file_hash = hashlib.sha256(fh.read()).hexdigest()
            try:
                blockchain.log_hash(file_hash)
            except Exception:
                # Non-fatal: continue even if blockchain logging fails
                pass
        except Exception:
            file_hash = None

        file_type = get_file_type(file.filename)

        try:
            content = extract_content(filepath, file_type)
            analysis = run_fraud_checks(content, file_type, filepath, official_records)
        except Exception as e:
            analysis = {"fraud_score": 0, "risk_level": "Error", "explanations": [f"Processing failed: {str(e)}"], "forensic": {}, "validation": {}, "signature": {}, "metadata": {}}

        # Ensure all expected keys exist
        analysis.setdefault("forensic", {})
        analysis.setdefault("validation", {})
        analysis.setdefault("signature", {})
        analysis.setdefault("metadata", {})

        results.append({
            "filename": file.filename,
            "hash": file_hash,
            **analysis
        })

    return {"message": "Upload and analysis successful", "files": results}
