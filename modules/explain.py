# modules/explain.py
def generate(fraud_score: int, forensic_results: dict, validation_results: dict):
    explanations = []

    if forensic_results.get("metadata_mismatch"):
        explanations.append("Metadata shows modification after issue date.")

    if forensic_results.get("font_issue"):
        explanations.append("Unusual font usage detected.")

    if forensic_results.get("compression_anomaly"):
        explanations.append("Compression anomaly detected.")

    if validation_results.get("salary_mismatch"):
        explanations.append("Salary mismatch with HR records.")

    if validation_results.get("employee_not_found"):
        explanations.append("Employee not found in official records.")

    if not explanations:
        explanations.append("No anomalies detected.")

    return explanations
