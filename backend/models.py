# backend/models.py
from pydantic import BaseModel, Field
from typing import List, Optional

class PatientIntake(BaseModel):
    age: int = Field(..., ge=0, le=120)
    gender: str = Field(..., description="Biological sex")
    weight_kg: float = Field(..., gt=0, description="Weight in kilograms")
    temperature: Optional[float] = Field(None, description="Body temperature in Celsius")
    symptom_duration_days: int = Field(..., ge=0)
    allergies: List[str] = Field(default=[])
    chronic_conditions: List[str] = Field(default=[])
    is_pregnant: bool = Field(False)
    symptoms: List[str] = Field(..., description="List of reported symptoms")

class DiseasePredictionMatch(BaseModel):
    predicted_disease: str
    model_score: Optional[float] = None
    matched_symptoms: List[str] = Field(default_factory=list)
    description: str
    precautions: List[str]
    recommended_medicine: Optional[str] = None
    dosage_instruction: Optional[str] = None
    medication_source: Optional[str] = None
    medication_reviewed_by: Optional[str] = None
    medication_reviewed_at: Optional[str] = None
    medication_category: Optional[str] = None
    common_medications_reference: Optional[str] = None
    pregnancy_warnings: List[str] = Field(default_factory=list)

class ClinicalResponse(BaseModel):
    top_predictions: List[DiseasePredictionMatch]
    emergency_triage_alert: Optional[str] = None