# backend/clinical_rules.py

def evaluate_emergency_triage(temperature: float, symptoms: list) -> dict:
    critical_symptoms = {"chest pain", "difficulty breathing", "severe shortness of breath", "loss of consciousness"}
    user_symptoms = {s.lower().strip() for s in symptoms}
    
    if temperature and temperature > 39.5:
        return {
            "is_emergency": True,
            "reason": "High grade fever threshold exceeded (> 39.5°C). Immediate medical referral required."
        }
    
    intersection = critical_symptoms.intersection(user_symptoms)
    if intersection:
        return {
            "is_emergency": True,
            "reason": f"Critical symptom detected: {list(intersection)[0]}. Seek immediate emergency care."
        }
        
    return {"is_emergency": False, "reason": None}

def evaluate_age_group(age: int) -> str:
    if age < 2:
        return "neonate_infant"
    elif 2 <= age < 12:
        return "pediatric"
    elif 12 <= age < 65:
        return "adult"
    else:
            return "geriatric"

def screen_pregnancy_and_contraindications(gender: str, age: int, is_pregnant: bool, medication_record: dict) -> list:
    warnings = []
    
    if gender.lower() == "female" and 12 <= age <= 50:
        if is_pregnant:
            warnings.append("Pregnancy Alert: Patient is pregnant. Verify all medication safety classifications against teratogenic risks.")
            contraindications = medication_record.get("contraindications", [])
            for c in contraindications:
                if "pregnancy" in c.lower():
                    warnings.append(f"Contraindication match blocked: {c}")
                    
    return warnings

def calculate_dosage(weight_kg: float, age: int, base_medication: str) -> str:
    age_group = evaluate_age_group(age)
    
    if age_group in ["neonate_infant", "pediatric"]:
        calculated_mg = round(weight_kg * 10, 2)
        return f"{calculated_mg}mg oral suspension twice daily for 3 days (Pediatric weight-scaled dosage)"
    else:
        if weight_kg < 40:
            return "500mg daily (Low weight adult adjusted dosage)"
        else:
            return "500mg twice daily for 3 days (Standard adult dosage)"