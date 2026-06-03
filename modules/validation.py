import re, difflib

def parse_name(text: str) -> str:
    match = re.search(r"(Name|Employee)[:\-]?\s*([A-Za-z ]+)", text)
    return match.group(2).strip() if match else None

def parse_salary(text: str) -> int:
    match = re.search(r"Salary[:\-]?\s*(\d+)", text)
    return int(match.group(1)) if match else None

def parse_emp_id(text: str) -> str:
    match = re.search(r"(ID|Employee ID)[:\-]?\s*(\w+)", text)
    return match.group(2).strip() if match else None

def cross_validate(text: str, official_records: dict) -> dict:
    results = {
        "employee_id_match": False,
        "salary_within_range": False,
        "salary_mismatch": False,
        "name_typo": False,
        "name_mismatch": False,
        "employee_not_found": False
    }

    name = parse_name(text)
    salary = parse_salary(text)
    emp_id = parse_emp_id(text)

    if emp_id and emp_id in official_records:
        record = official_records[emp_id]
        results["employee_id_match"] = True

        if salary and abs(salary - record["salary"]) <= 0.05 * record["salary"]:
            results["salary_within_range"] = True
        else:
            results["salary_mismatch"] = True

        if name:
            similarity = difflib.SequenceMatcher(
                None, name.lower(), record["name"].lower()
            ).ratio()

            if similarity >= 0.85:
                results["name_typo"] = True
            else:
                results["name_mismatch"] = True

    else:
        results["employee_not_found"] = True

    return results

def parse_aadhaar(text):
    aadhaar_pattern = r"\b\d{4}\s?\d{4}\s?\d{4}\b"
    match = re.search(aadhaar_pattern, text)
    return match.group(0) if match else None


def verify_aadhaar(text):
    results = {
        "aadhaar_missing": False,
        "dob_missing": False,
        "gender_missing": False,
        "uidai_keywords_missing": False
    }

    aadhaar = parse_aadhaar(text)
    results["aadhaar_missing"] = aadhaar is None

    results["dob_missing"] = "date of birth" not in text.lower()

    results["gender_missing"] = not (
        "male" in text.lower() or "female" in text.lower()
    )

    results["uidai_keywords_missing"] = not (
        "uidai" in text.lower()
        or "government of india" in text.lower()
    )

    return results

def generate_validation_results(text, official_records=None):
    results = {}

    # Aadhaar validation
    aadhaar_result = parse_aadhaar(text)
    results["aadhaar_missing"] = aadhaar_result is None

    results["dob_missing"] = "date of birth" not in text.lower()
    results["gender_missing"] = not (
        "male" in text.lower() or "female" in text.lower()
    )
    results["uidai_keywords_missing"] = not (
        "uidai" in text.lower()
        or "government of india" in text.lower()
    )

    # Employee validation (if records exist)
    if official_records:
        emp_results = cross_validate(text, official_records)

        # merge results safely
        results.update(emp_results)

    return results
