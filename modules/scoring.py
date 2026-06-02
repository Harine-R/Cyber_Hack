def calculate(forensic_results, validation_results, metadata_results, signature_results):
    score = 0

    if forensic_results.get("metadata_mismatch"): score += 20
    if forensic_results.get("font_issue"): score += 10
    if forensic_results.get("compression_anomaly"): score += 10

    if validation_results.get("salary_mismatch"): score += 50
    if validation_results.get("employee_not_found"): score += 100
    if validation_results.get("name_mismatch"): score += 20
    if validation_results.get("aadhaar_missing"):
        score += 40

    if validation_results.get("dob_missing"):
        score += 10

    if validation_results.get("gender_missing"):
        score += 10

    if validation_results.get("uidai_keywords_missing"):
        score += 20

    if signature_results.get("signature_anomaly"): score += 40

    if metadata_results.get("metadata", {}).get("/Producer") == "Microsoft Word":
        score += 20

    score = min(score, 100)

    # Risk level classification
    if score <= 30:
        risk = "Low Risk"
    elif score <= 70:
        risk = "Medium Risk"
    else:
        risk = "High Risk"

    return score, risk
