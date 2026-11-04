# backend/csv_loader.py
import pandas as pd
import os
from symptom_matching import normalize_symptom


def load_disease_symptom_patterns():
    db_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database"))
    dataset_path = os.path.join(db_dir, "dataset.csv")
    dataset = pd.read_csv(dataset_path)

    disease_patterns = {}
    symptom_columns = [column for column in dataset.columns if column.startswith("Symptom_")]

    for _, row in dataset.iterrows():
        disease = str(row["Disease"]).strip()
        symptoms = {
            normalize_symptom(row[column])
            for column in symptom_columns
            if pd.notna(row[column]) and str(row[column]).strip()
        }
        if symptoms:
            disease_patterns.setdefault(disease, []).append(symptoms)

    if not disease_patterns:
        raise ValueError(f"No disease symptom patterns found in {dataset_path}")

    return disease_patterns


def load_disease_medication_references():
    db_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database"))
    mapping_path = os.path.join(db_dir, "disease_medications_mapping.csv")
    mapping = pd.read_csv(mapping_path)

    required_columns = {"Disease", "Category", "Common Medications"}
    missing_columns = required_columns - set(mapping.columns)
    if missing_columns:
        raise ValueError(
            f"{mapping_path} is missing required columns: {', '.join(sorted(missing_columns))}"
        )

    references = {}
    for _, row in mapping.iterrows():
        disease = str(row["Disease"]).strip()
        category = str(row["Category"]).strip()
        medications = str(row["Common Medications"]).strip()
        if not disease or not medications or medications.lower() == "nan":
            continue

        references[disease.casefold()] = {
            "category": category,
            "common_medications": medications,
        }

    # The mapping CSV uses "hemorrhoids" while the training data uses "hemmorhoids".
    if "dimorphic hemorrhoids(piles)" in references:
        references["dimorphic hemmorhoids(piles)"] = references[
            "dimorphic hemorrhoids(piles)"
        ]

    return references


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