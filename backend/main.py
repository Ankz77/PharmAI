from clinical_rules import evaluate_emergency_triage, screen_pregnancy_and_contraindications, evaluate_age_group
import os
import joblib
import numpy as np
from fastapi import FastAPI, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from csv_loader import (
    load_disease_medication_references,
    load_disease_metadata,
    load_disease_symptom_patterns,
)
from medication_safety import has_medical_review
from symptom_matching import normalize_symptom, explain_symptom_matches

from models import PatientIntake, ClinicalResponse, DiseasePredictionMatch

app = FastAPI(title="PharmAI Clinical Decision Support API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://ankz-pharmai.netlify.app",
    ],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "pharm_ai_db"

client = None
db = None
disease_metadata = {}
disease_patterns = {}
medication_references = {}
model = None
label_encoder = None
feature_columns = None

@app.on_event("startup")
async def startup_event():
    global client, db, disease_metadata, disease_patterns, medication_references
    global model, label_encoder, feature_columns
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    model_dir = os.path.join(os.path.dirname(__file__), "trained_models")
    model = joblib.load(os.path.join(model_dir, "xgb_disease_model.joblib"))
    label_encoder = joblib.load(os.path.join(model_dir, "label_encoder.joblib"))
    feature_columns = joblib.load(os.path.join(model_dir, "feature_columns.joblib"))

    disease_patterns = load_disease_symptom_patterns()
    medication_references = load_disease_medication_references()
    disease_metadata = load_disease_metadata()
    print("FastAPI server initialized. XGBoost model and CSV references loaded successfully.")
    
@app.on_event("shutdown")
async def shutdown_event():
    client.close()

@app.post("/predict", response_model=ClinicalResponse)
async def predict_disease(intake: PatientIntake):
    triage = evaluate_emergency_triage(intake.temperature, intake.symptoms)
    if triage["is_emergency"]:
        emergency_match = DiseasePredictionMatch(
            predicted_disease="EMERGENCY REFERRAL REQUIRED",
            description=triage["reason"],
            precautions=["Proceed immediately to the nearest emergency medical facility."],
            pregnancy_warnings=[]
        )
        return ClinicalResponse(
            top_predictions=[emergency_match],
            emergency_triage_alert=triage["reason"]
        )

    severity_docs = await db.symptom_weights.find().to_list(length=200)
    weights_dict = {
        normalize_symptom(doc.get("symptom", doc.get("Symptom", ""))): doc.get("weight", 1)
        for doc in severity_docs
    }

    vector = np.zeros(len(feature_columns))
    symptom_to_idx = {
        normalize_symptom(symptom): index
        for index, symptom in enumerate(feature_columns)
    }

    print("Incoming frontend symptoms:", intake.symptoms)
    matched_features = set()
    for symptom in intake.symptoms:
        clean_symptom = normalize_symptom(symptom)
        idx = symptom_to_idx.get(clean_symptom)
        if idx is not None:
            vector[idx] = weights_dict.get(clean_symptom, 1.0)
            matched_features.add(clean_symptom)
        print(f"Mapping '{symptom}' -> cleaned: '{clean_symptom}' -> Matched?: {idx is not None}")

    if not matched_features:
        raise HTTPException(
            status_code=422,
            detail="None of the selected symptoms are available in the training dataset."
        )

    print(f"Total non-zero features active in vector: {np.count_nonzero(vector)} / {len(feature_columns)}")
    probabilities = model.predict_proba(np.array([vector]))[0]
    top_indices = np.argsort(probabilities)[::-1][:3]
    top_predictions = []

    for pred_idx in top_indices:
        disease_name = label_encoder.inverse_transform([pred_idx])[0]
        csv_meta = disease_metadata.get(disease_name, {})
        db_disease_record = await db.diseases.find_one({"disease": disease_name})
        
        description = csv_meta.get("description") or (db_disease_record.get("description") if db_disease_record else None) or "No detailed description available."
        precautions = csv_meta.get("precautions") or (db_disease_record.get("precautions") if db_disease_record else [])

        medicine_record = await db.medicines.find_one({"disease": disease_name})
        if not has_medical_review(medicine_record):
            medicine_record = None
        medication_reference = medication_references.get(disease_name.casefold())

        warnings = (
            screen_pregnancy_and_contraindications(
                intake.gender, intake.age, intake.is_pregnant, medicine_record
            )
            if medicine_record
            else []
        )

        age_group = evaluate_age_group(intake.age)
        dosage = None
        if medicine_record:
            dosage = medicine_record.get(
                "pediatric_dosage"
                if age_group in ["neonate_infant", "pediatric"]
                else "adult_dosage"
            )
        
        top_predictions.append(DiseasePredictionMatch(
            predicted_disease=disease_name,
            model_score=float(probabilities[pred_idx]),
            matched_symptoms=explain_symptom_matches(
                intake.symptoms,
                disease_patterns.get(disease_name, [])
            ),
            description=description,
            precautions=precautions,
            recommended_medicine=medicine_record.get("recommended_medicine") if medicine_record else None,
            dosage_instruction=dosage,
            medication_source=medicine_record.get("source") if medicine_record else None,
            medication_reviewed_by=medicine_record.get("reviewed_by") if medicine_record else None,
            medication_reviewed_at=medicine_record.get("reviewed_at") if medicine_record else None,
            medication_category=medication_reference.get("category") if medication_reference else None,
            common_medications_reference=(
                medication_reference.get("common_medications")
                if medication_reference
                else None
            ),
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
    if not has_medical_review(medicine_record):
        raise HTTPException(
            status_code=404,
            detail="No medically reviewed medication guidance is available for this disease."
        )

    csv_meta = disease_metadata.get(disease, {})
    db_disease_record = await db.diseases.find_one({"disease": disease})
    
    description = csv_meta.get("description") or (db_disease_record.get("description") if db_disease_record else None)
    
    if not medicine_record:
        raise HTTPException(status_code=404, detail="Disease medicine record not found")

    age_group = evaluate_age_group(age)
    dosage = medicine_record.get("pediatric_dosage") if age_group in ["neonate_infant", "pediatric"] else medicine_record.get("adult_dosage")
    
    return {
        "disease": disease,
        "description": description,
        "recommended_medicine": medicine_record.get("recommended_medicine"),
        "dosage_instructions": dosage,
        "contraindications": medicine_record.get("contraindications", []),
        "source": medicine_record["source"],
        "reviewed_by": medicine_record["reviewed_by"],
        "reviewed_at": medicine_record["reviewed_at"]
    }

@app.get("/symptoms/all")
async def get_all_symptoms():
    symptoms = {
        symptom
        for patterns in disease_patterns.values()
        for pattern in patterns
        for symptom in pattern
    }
    return {"symptoms": sorted(symptoms)}

@app.get("/history")
async def get_prediction_history(limit: int = 10):
    logs = await db.prediction_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(length=limit)
    return {"history": logs}