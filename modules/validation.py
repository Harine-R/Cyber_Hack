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
    results = {}
    name = parse_name(text)
    salary = parse_salary(text)
    emp_id = parse_emp_id(text)

    if emp_id and emp_id in official_records:
        record = official_records[emp_id]
        results["employee_id_match"] = True

        # Salary range validation (±5%)
        if salary and abs(salary - record["salary"]) <= 0.05 * record["salary"]:
            results["salary_within_range"] = True
        else:
            results["salary_mismatch"] = True

        # Name typo vs mismatch
        if name:
            similarity = difflib.SequenceMatcher(None, name.lower(), record["name"].lower()).ratio()
            if similarity >= 0.85:
                results["name_typo"] = True
            else:
                results["name_mismatch"] = True

    else:
        # No ID → try name-based validation
        matches = [rec for rec in official_records.values() if rec.get("name") == name]

        if not matches:
            results["employee_not_found"] = True
        elif len(matches) > 1:
            # Ambiguous name → require ID
            results["employee_not_found"] = True
        else:
            record = matches[0]
            # Salary range validation (±5%)
            if salary and abs(salary - record["salary"]) <= 0.05 * record["salary"]:
                results["salary_within_range"] = True
            else:
                results["salary_mismatch"] = True

    return results

def parse_aadhaar(text):
    aadhaar_pattern = r"\b\d{4}\s?\d{4}\s?\d{4}\b"
    match = re.search(aadhaar_pattern, text)
    return match.group(0) if match else None


def verify_aadhaar(text):
    results = {}

    aadhaar = parse_aadhaar(text)

    if not aadhaar:
        results["aadhaar_missing"] = True

    if "date of birth" not in text.lower():
        results["dob_missing"] = True

    if "male" not in text.lower() and "female" not in text.lower():
        results["gender_missing"] = True

    if (
        "uidai" not in text.lower()
        and "aadhaar" not in text.lower()
        and "government of india" not in text.lower()
    ):
        results["uidai_keywords_missing"] = True

    return results
