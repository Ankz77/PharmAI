# seed_database.py
import asyncio
import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_DETAILS = "mongodb://localhost:27017"

async def seed_database():
    client = AsyncIOMotorClient(MONGO_DETAILS)
    db = client["pharm_ai_db"]
    
    print("Connected to MongoDB. Starting data ingestion...")

    # 1. Seed Symptom Severities
    severity_df = pd.read_csv("Symptom-severity.csv")
    severity_df["Symptom"] = severity_df["Symptom"].str.strip().str.lower()
    severity_docs = severity_df.to_dict(orient="records")
    
    await db.symptom_weights.delete_many({})
    await db.symptom_weights.insert_many(severity_docs)
    print(f"Seeded {len(severity_docs)} records into 'symptom_weights'.")

    # 2. Merge and Seed Diseases (Descriptions & Precautions)
    desc_df = pd.read_csv("symptom_Description.csv")
    prec_df = pd.read_csv("symptom_precaution.csv")
    
    desc_df["Disease"] = desc_df["Disease"].str.strip()
    prec_df["Disease"] = prec_df["Disease"].str.strip()
    
    disease_info = pd.merge(desc_df, prec_df, on="Disease", how="outer")
    
    disease_docs = []
    for _, row in disease_info.iterrows():
        precautions = [
            row.get("Precaution_1"),
            row.get("Precaution_2"),
            row.get("Precaution_3"),
            row.get("Precaution_4")
        ]
        cleaned_precautions = [str(p).strip() for p in precautions if pd.notna(p)]
        
        doc = {
            "disease": row["Disease"],
            "description": str(row["Description"]).strip(),
            "precautions": cleaned_precautions
        }
        disease_docs.append(doc)

    await db.diseases.delete_many({})
    await db.diseases.insert_many(disease_docs)
    print(f"Seeded {len(disease_docs)} records into 'diseases'.")

    # 3. Seed Training Dataset Samples
    train_df = pd.read_csv("dataset.csv")
    train_docs = []
    
    for _, row in train_df.iterrows():
        symptoms = []
        for col in train_df.columns:
            if col.startswith("Symptom") and pd.notna(row[col]):
                val = str(row[col]).strip().lower()
                if val:
                    symptoms.append(val)
        
        train_docs.append({
            "disease": str(row["Disease"]).strip(),
            "symptoms": symptoms
        })

    await db.training_samples.delete_many({})
    await db.training_samples.insert_many(train_docs)
    print(f"Seeded {len(train_docs)} records into 'training_samples'.")

    # 4. Seed Initial Reference Medicines Mapping (Sample structure)
    # You can expand this collection with specific pharmaceuticals for each disease
    sample_medicines = [
        {
            "disease": "Fungal infection",
            "recommended_medicine": "Clotrimazole Topical Cream 1%",
            "adult_dosage": "Apply thin layer twice daily for 2 weeks",
            "pediatric_dosage": "Apply thin layer twice daily for 2 weeks",
            "contraindications": ["Hypersensitivity to azole antifungals"]
        },
        {
            "disease": "Malaria",
            "recommended_medicine": "Coartem (Artemether/Lumefantrine)",
            "adult_dosage": "4 tablets twice daily for 3 days",
            "pediatric_dosage": "Weight-based dosing (e.g., 5-14kg: 1 tablet twice daily)",
            "contraindications": ["First trimester pregnancy", "Severe hepatic impairment"]
        }
    ]
    
    await db.medicines.delete_many({})
    await db.medicines.insert_many(sample_medicines)
    print(f"Seeded initial sample records into 'medicines'.")

    print("Phase 1 Database Ingestion Complete Successfully.")

if __name__ == "__main__":
    asyncio.run(seed_database())