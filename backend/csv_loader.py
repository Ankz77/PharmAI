# backend/csv_loader.py
import pandas as pd
import os

def load_disease_metadata():
    metadata = {}
    
    # Path to database folder from backend directory
    db_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database"))
    
    # Load descriptions from symptom_Description.csv
    desc_path = os.path.join(db_dir, "symptom_Description.csv")
    if os.path.exists(desc_path):
        desc_df = pd.read_csv(desc_path)
        for _, row in desc_df.iterrows():
            disease = str(row.iloc[0]).strip()
            description = str(row.iloc[1]).strip()
            if disease not in metadata:
                metadata[disease] = {}
            metadata[disease]["description"] = description
    else:
        print(f"Warning: {desc_path} not found.")

    # Load precautions from symptom_precaution.csv
    prec_path = os.path.join(db_dir, "symptom_precaution.csv")
    if os.path.exists(prec_path):
        prec_df = pd.read_csv(prec_path)
        for _, row in prec_df.iterrows():
            disease = str(row.iloc[0]).strip()
            precautions = [str(row[col]).strip() for col in prec_df.columns[1:] if pd.notna(row[col])]
            if disease not in metadata:
                metadata[disease] = {}
            metadata[disease]["precautions"] = precautions
    else:
        print(f"Warning: {prec_path} not found.")

    print(f"Loaded CSV metadata for {len(metadata)} diseases successfully from database folder.")
    return metadata