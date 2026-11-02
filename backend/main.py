# backend/main.py
from clinical_rules import evaluate_emergency_triage, screen_pregnancy_and_contraindications, evaluate_age_group
import os
import joblib
import numpy as np
from fastapi import FastAPI, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from csv_loader import load_disease_metadata

from models import PatientIntake, ClinicalResponse, DiseasePredictionMatch

app = FastAPI(title="PharmAI Clinical Decision Support API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "pharm_ai_db"

client = None
db = None
model = None
label_encoder = None
feature_columns = None
disease_metadata = {}

@app.on_event("startup")
async def startup_event():
    global client, db, model, label_encoder, feature_columns, disease_metadata
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    
    model_dir = "trained_models"
    model = joblib.load(os.path.join(model_dir, "xgb_disease_model.joblib"))
    label_encoder = joblib.load(os.path.join(model_dir, "label_encoder.joblib"))
    feature_columns = joblib.load(os.path.join(model_dir, "feature_columns.joblib"))
    
    disease_metadata = load_disease_metadata()
    print("FastAPI server initialized. Model artifacts and CSV metadata loaded successfully.")
    
@app.on_event("shutdown")
async def shutdown_event():
    client.close()

def compute_physical_dosage_units(weight_kg: float, age: int, disease: str) -> str:
    age_group = evaluate_age_group(age)
    if age_group in ["neonate_infant", "pediatric"]:
        ml_amount = round(weight_kg * 0.5, 1)
        return f"{ml_amount} milliliters of oral suspension per dose administered twice daily"
    else:
        if "cream" in disease.lower() or "infection" in disease.lower():
            return "Topical application twice daily"
        return "2 capsules daily taken with meals"

@app.post("/predict", response_model=ClinicalResponse)
async def predict_disease(intake: PatientIntake):
    triage = evaluate_emergency_triage(intake.temperature, intake.symptoms)
    if triage["is_emergency"]:
        emergency_match = DiseasePredictionMatch(
            predicted_disease="EMERGENCY REFERRAL REQUIRED",
            confidence_score=1.0,
            description=triage["reason"],
            precautions=["Proceed immediately to the nearest emergency medical facility."],
            recommended_medicine="None. Emergency clinical evaluation required.",
            dosage_instruction="Not applicable",
            physical_unit_breakdown="Not applicable",
            pregnancy_warnings=[]
        )
        return ClinicalResponse(
            top_predictions=[emergency_match],
            emergency_triage_alert=triage["reason"]
        )
    
    severity_docs = await db.symptom_weights.find().to_list(length=200)
    weights_dict = {
        str(doc.get("symptom", doc.get("Symptom"))).strip().lower(): doc.get("weight", 1) 
        for doc in severity_docs
    }
    
    vector = np.zeros(len(feature_columns))
    symptom_to_idx = {str(s).strip().lower(): i for i, s in enumerate(feature_columns)}
    
    print("Incoming frontend symptoms:", intake.symptoms)
    for symptom in intake.symptoms:
        clean_symptom = str(symptom).strip().lower().replace(" ", "_")
        is_matched = clean_symptom in symptom_to_idx
        print(f"Mapping '{symptom}' -> cleaned: '{clean_symptom}' -> Matched?: {is_matched}")
        if is_matched:
            idx = symptom_to_idx[clean_symptom]
            weight = weights_dict.get(clean_symptom, 1.0)
            vector[idx] = weight
            
    print(f"Total non-zero features active in vector: {np.count_nonzero(vector)} / {len(feature_columns)}")

    X_input = np.array([vector])
    probabilities = model.predict_proba(X_input)[0]
    
    top_indices = np.argsort(probabilities)[::-1][:3]
    top_predictions = []
    
    for pred_idx in top_indices:
        confidence = float(probabilities[pred_idx])
        disease_name = label_encoder.inverse_transform([pred_idx])[0]
        
        csv_meta = disease_metadata.get(disease_name, {})
        db_disease_record = await db.diseases.find_one({"disease": disease_name})
        
        description = csv_meta.get("description") or (db_disease_record.get("description") if db_disease_record else None) or "No detailed description available."
        precautions = csv_meta.get("precautions") or (db_disease_record.get("precautions") if db_disease_record else [])

        medicine_record = await db.medicines.find_one({"disease": disease_name})
        if not medicine_record:
            medicine_record = {
                "recommended_medicine": "Standard supportive care",
                "adult_dosage": "Consult physician for dosage",
                "pediatric_dosage": "Consult pediatrician for dosage",
                "contraindications": []
            }
            
        warnings = screen_pregnancy_and_contraindications(intake.gender, intake.age, intake.is_pregnant, medicine_record)
        
        age_group = evaluate_age_group(intake.age)
        dosage = medicine_record.get("pediatric_dosage") if age_group in ["neonate_infant", "pediatric"] else medicine_record.get("adult_dosage")
        unit_breakdown = compute_physical_dosage_units(intake.weight_kg, intake.age, disease_name)
        
        top_predictions.append(DiseasePredictionMatch(
            predicted_disease=disease_name,
            confidence_score=confidence,
            description=description,
            precautions=precautions,
            recommended_medicine=medicine_record.get("recommended_medicine"),
            dosage_instruction=dosage,
            physical_unit_breakdown=unit_breakdown,
            pregnancy_warnings=warnings
        ))
    
    log_document = {
        "timestamp": datetime.utcnow(),
        "intake": intake.dict(),
        "top_predictions": [p.dict() for p in top_predictions]
    }
    await db.prediction_logs.insert_one(log_document)
    
    return ClinicalResponse(
        top_predictions=top_predictions,
        emergency_triage_alert=None
    )

@app.get("/treatment-summary")
async def get_treatment_summary(disease: str = Query(...), weight_kg: float = Query(70.0), age: int = Query(25)):
    medicine_record = await db.medicines.find_one({"disease": disease})
    csv_meta = disease_metadata.get(disease, {})
    db_disease_record = await db.diseases.find_one({"disease": disease})
    
    description = csv_meta.get("description") or (db_disease_record.get("description") if db_disease_record else None)
    
    if not medicine_record:
        raise HTTPException(status_code=404, detail="Disease medicine record not found")
        
    unit_breakdown = compute_physical_dosage_units(weight_kg, age, disease)
    age_group = evaluate_age_group(age)
    dosage = medicine_record.get("pediatric_dosage") if age_group in ["neonate_infant", "pediatric"] else medicine_record.get("adult_dosage")
    
    return {
        "disease": disease,
        "description": description,
        "recommended_medicine": medicine_record.get("recommended_medicine"),
        "dosage_instructions": dosage,
        "exact_unit_breakdown": unit_breakdown,
        "contraindications": medicine_record.get("contraindications", [])
    }

@app.get("/symptoms/all")
async def get_all_symptoms():
    severity_docs = await db.symptom_weights.find({}, {"_id": 0}).to_list(length=200)
    if not severity_docs:
        return {"symptoms": feature_columns}
    return {"symptoms": [doc.get("symptom", doc.get("Symptom")) for doc in severity_docs]}

@app.get("/history")
async def get_prediction_history(limit: int = 10):
    logs = await db.prediction_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(length=limit)
    return {"history": logs}