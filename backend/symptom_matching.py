def normalize_symptom(symptom):
    return "_".join(str(symptom).strip().lower().replace("_", " ").split())


def explain_symptom_matches(symptoms, disease_patterns):
    selected = {normalize_symptom(symptom) for symptom in symptoms}
    if not disease_patterns:
        return []

    best_pattern = max(
        disease_patterns,
        key=lambda pattern: (
            len(selected & pattern),
            -len(pattern - selected),
        ),
    )
    return sorted(selected & best_pattern)
