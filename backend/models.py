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
    confidence_score: float
    description: str
    precautions: List[str]
    recommended_medicine: str
    dosage_instruction: str
    physical_unit_breakdown: str
    pregnancy_warnings: List[str]

class ClinicalResponse(BaseModel):
    top_predictions: List[DiseasePredictionMatch]
    emergency_triage_alert: Optional[str] = None