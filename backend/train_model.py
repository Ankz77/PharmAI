# backend/train_model.py
import os
import joblib
import numpy as np
import pandas as pd
from pymongo import MongoClient
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "pharm_ai_db"

def parse_dataset_csv():
    """Robustly parses dataset.csv from the root database folder handling uneven columns."""
    possible_paths = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "database")),
        "/database"
    ]
    
    filepath = None
    for path in possible_paths:
        test_path = os.path.join(path, "dataset.csv")
        if os.path.exists(test_path):
            filepath = test_path
            break
            
    if not filepath:
        print("Warning: dataset.csv could not be located in any target database directory.")
        return []

    df = pd.read_csv(filepath)
    symptom_cols = [col for col in df.columns if col.startswith("Symptom_")]
    training_samples = []
    
    for _, row in df.iterrows():
        disease = str(row["Disease"]).strip()
        symptoms = []
        for col in symptom_cols:
            val = row[col]
            if pd.notna(val):
                clean_val = str(val).strip().lower()
                if clean_val and clean_val != "nan":
                    symptoms.append(clean_val)
                    
        symptoms = list(set(symptoms))
        if symptoms:
            training_samples.append({
                "disease": disease,
                "symptoms": symptoms
            })
            
    print(f"Parsed {len(training_samples)} samples from database folder handling uneven columns.")
    return training_samples

def load_data_from_mongo():
    uri = MONGO_URI
    client = None
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
    except Exception:
        uri = "mongodb://mongo:27017"
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            client.admin.command('ping')
        except Exception:
            client = None

    training_samples = []
    symptom_weights_docs = []

    if client:
        db = client[DB_NAME]
        print("Fetching training samples and symptom weights from MongoDB...")
        try:
            training_samples = list(db.training_samples.find({}, {"_id": 0}))
            symptom_weights_docs = list(db.symptom_weights.find({}, {"_id": 0}))
        except Exception as e:
            print(f"Error querying MongoDB: {e}")
        client.close()
    
    if not training_samples:
        print("MongoDB training samples empty or unavailable. Falling back to database/dataset.csv parsing...")
        training_samples = parse_dataset_csv()

    weights_dict = {
        str(doc.get("symptom", doc.get("Symptom"))).strip().lower(): doc.get("weight", 1) 
        for doc in symptom_weights_docs
    }
    
    return training_samples, weights_dict

def train_and_save_model():
    samples, weights_dict = load_data_from_mongo()
    
    if not samples:
        print("Error: No training samples found. Please check your database or CSV files.")
        return

    extracted_symptoms = set()
    for sample in samples:
        for s in sample["symptoms"]:
            extracted_symptoms.add(str(s).strip().lower())
            
    all_symptoms = sorted(list(set(list(weights_dict.keys()) + list(extracted_symptoms))))
    symptom_to_idx = {symptom: idx for idx, symptom in enumerate(all_symptoms)}
    
    print(f"Loaded {len(samples)} samples across {len(all_symptoms)} unique features.")

    X = []
    y = []
    
    for sample in samples:
        vector = np.zeros(len(all_symptoms))
        disease = sample["disease"]
        for symptom in sample["symptoms"]:
            clean_symptom = str(symptom).strip().lower()
            if clean_symptom in symptom_to_idx:
                idx = symptom_to_idx[clean_symptom]
                weight = weights_dict.get(clean_symptom, 1)
                vector[idx] = weight
        X.append(vector)
        y.append(disease)

    X = np.array(X)
    
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

    print("Training XGBoost classifier with optimized parameters...")
    model = XGBClassifier(
        n_estimators=150,
        learning_rate=0.05,
        max_depth=6,
        eval_metric="mlogloss",
        random_state=42
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Model Training Complete. Test Accuracy: {acc * 100:.2f}%")

    os.makedirs("trained_models", exist_ok=True)
    
    joblib.dump(model, "trained_models/xgb_disease_model.joblib")
    joblib.dump(label_encoder, "trained_models/label_encoder.joblib")
    joblib.dump(all_symptoms, "trained_models/feature_columns.joblib")
    print("Successfully exported model artifacts to 'trained_models/'.")

if __name__ == "__main__":
    train_and_save_model()