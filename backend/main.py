from clinical_rules import evaluate_emergency_triage, screen_pregnancy_and_contraindications, evaluate_age_group
import os
import re
import joblib
import numpy as np
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from auth import create_access_token, decode_access_token, hash_password, verify_password
from csv_loader import (
    load_disease_medication_references,
    load_disease_metadata,
    load_disease_symptom_patterns,
)
from medication_safety import has_medical_review
from symptom_matching import normalize_symptom, explain_symptom_matches

from models import (
    ClinicalResponse,
    DiseasePredictionMatch,
    LoginRequest,
    PatientIntake,
    ProfileUpdateRequest,
    RegisterRequest,
)

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
AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
bearer_scheme = HTTPBearer(auto_error=False)

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
    if not AUTH_SECRET_KEY or len(AUTH_SECRET_KEY) < 32:
        raise RuntimeError("Set AUTH_SECRET_KEY to a random value of at least 32 characters.")

    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    await db.users.create_index("email", unique=True)

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
    if client:
        client.close()


def public_user(user):
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "profession": user["profession"],
    }


def auth_response(user):
    return {
        "access_token": create_access_token(user, AUTH_SECRET_KEY),
        "token_type": "bearer",
        "user": public_user(user),
    }


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    if not credentials or not AUTH_SECRET_KEY:
        raise HTTPException(
            status_code=401,
            detail="Please sign in to continue.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_data = decode_access_token(credentials.credentials, AUTH_SECRET_KEY)
    if not token_data:
        raise HTTPException(
            status_code=401,
            detail="Your session is invalid or has expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = ObjectId(token_data["sub"])
    except InvalidId:
        user_id = None
    user = await db.users.find_one({"_id": user_id}) if user_id else None
    if not user:
        raise HTTPException(status_code=401, detail="Account not found. Please sign in again.")
    return user


@app.post("/auth/register")
async def register(request: RegisterRequest):
    email = request.email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")
    name = request.name.strip()
    if len(name) < 2:
        raise HTTPException(status_code=422, detail="Enter your full name.")

    user = {
        "name": name,
        "email": email,
        "profession": request.profession,
        "password_hash": hash_password(request.password),
        "created_at": datetime.utcnow(),
    }
    try:
        await db.users.insert_one(user)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    return auth_response(user)


@app.post("/auth/login")
async def login(request: LoginRequest):
    email = request.email.strip().lower()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(request.password, user.get("password_hash")):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_response(user)


@app.get("/auth/me")
async def get_account(current_user=Depends(get_current_user)):
    return {"user": public_user(current_user)}


@app.patch("/auth/me")
async def update_account(
    request: ProfileUpdateRequest,
    current_user=Depends(get_current_user),
):
    name = request.name.strip()
    if len(name) < 2:
        raise HTTPException(status_code=422, detail="Enter your full name.")

    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"name": name, "profession": request.profession, "updated_at": datetime.utcnow()}},
    )
    updated_user = await db.users.find_one({"_id": current_user["_id"]})
    if not updated_user:
        raise HTTPException(status_code=404, detail="Account not found.")
    return {"user": public_user(updated_user)}


@app.post("/predict", response_model=ClinicalResponse)
async def predict_disease(intake: PatientIntake, current_user=Depends(get_current_user)):
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
        "user_id": str(current_user["_id"]),
        "intake": intake.dict(),
        "top_predictions": [p.dict() for p in top_predictions]
    }
    await db.prediction_logs.insert_one(log_document)
    
    return ClinicalResponse(
        top_predictions=top_predictions,
        emergency_triage_alert=None
    )

@app.get("/treatment-summary")
async def get_treatment_summary(
    disease: str = Query(...),
    weight_kg: float = Query(70.0),
    age: int = Query(25),
    current_user=Depends(get_current_user),
):
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
async def get_all_symptoms(current_user=Depends(get_current_user)):
    symptoms = {
        symptom
        for patterns in disease_patterns.values()
        for pattern in patterns
        for symptom in pattern
    }
    return {"symptoms": sorted(symptoms)}

@app.get("/history")
async def get_prediction_history(
    limit: int = Query(10, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    logs = await db.prediction_logs.find(
        {"user_id": str(current_user["_id"])}, {"_id": 0, "user_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(length=limit)
    return {"history": logs}