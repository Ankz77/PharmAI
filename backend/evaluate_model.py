import os
import warnings

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, top_k_accuracy_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

warnings.filterwarnings("ignore", category=UserWarning)

DATABASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database"))
DATASET_PATH = os.path.join(DATABASE_DIR, "dataset.csv")
SEVERITY_PATH = os.path.join(DATABASE_DIR, "Symptom-severity.csv")
N_SPLITS = 5


def load_evaluation_data():
    dataset = pd.read_csv(DATASET_PATH)
    severity = pd.read_csv(SEVERITY_PATH)
    symptom_columns = [column for column in dataset.columns if column.startswith("Symptom_")]
    weights = {
        str(row["Symptom"]).strip().lower(): float(row["weight"])
        for _, row in severity.iterrows()
    }

    samples = []
    for _, row in dataset.iterrows():
        symptoms = {
            str(row[column]).strip().lower()
            for column in symptom_columns
            if pd.notna(row[column]) and str(row[column]).strip()
        }
        if symptoms:
            samples.append((str(row["Disease"]).strip(), symptoms))

    features = sorted(set(weights).union(*(symptoms for _, symptoms in samples)))
    feature_index = {symptom: index for index, symptom in enumerate(features)}
    matrix = np.zeros((len(samples), len(features)), dtype=np.float32)
    labels = []
    groups = []

    for row_index, (disease, symptoms) in enumerate(samples):
        labels.append(disease)
        groups.append("|".join(sorted(symptoms)))
        for symptom in symptoms:
            matrix[row_index, feature_index[symptom]] = weights.get(symptom, 1.0)

    encoder = LabelEncoder()
    encoded_labels = encoder.fit_transform(labels)
    return matrix, encoded_labels, np.asarray(groups), encoder


def evaluate():
    features, labels, groups, encoder = load_evaluation_data()
    splitter = StratifiedGroupKFold(n_splits=N_SPLITS, shuffle=True, random_state=42)
    out_of_fold_truth = []
    out_of_fold_prediction = []
    fold_macro_f1 = []
    fold_top3 = []
    all_class_indices = np.arange(len(encoder.classes_))
    missing_test_classes = set()

    for fold, (train_indices, test_indices) in enumerate(
        splitter.split(features, labels, groups), start=1
    ):
        model = XGBClassifier(
            n_estimators=150,
            learning_rate=0.05,
            max_depth=6,
            eval_metric="mlogloss",
            random_state=42,
        )
        model.fit(features[train_indices], labels[train_indices])
        predictions = model.predict(features[test_indices])
        probabilities = model.predict_proba(features[test_indices])

        fold_macro_f1.append(
            f1_score(
                labels[test_indices],
                predictions,
                labels=all_class_indices,
                average="macro",
                zero_division=0,
            )
        )
        fold_top3.append(
            top_k_accuracy_score(
                labels[test_indices],
                probabilities,
                k=3,
                labels=all_class_indices,
            )
        )

        out_of_fold_truth.extend(labels[test_indices].tolist())
        out_of_fold_prediction.extend(predictions.tolist())

        for class_index in all_class_indices:
            if not np.any(labels[test_indices] == class_index):
                missing_test_classes.add(encoder.classes_[class_index])

        leaked_groups = set(groups[train_indices]) & set(groups[test_indices])
        if leaked_groups:
            raise RuntimeError(f"Symptom-pattern leakage detected in fold {fold}")

        print(
            f"Fold {fold}: macro-F1={fold_macro_f1[-1]:.3f}, "
            f"top-3 accuracy={fold_top3[-1]:.3f}, "
            f"train={len(train_indices)}, test={len(test_indices)}"
        )

    print(
        f"\nMean across {N_SPLITS} folds: "
        f"macro-F1={np.mean(fold_macro_f1):.3f} "
        f"(SD {np.std(fold_macro_f1):.3f}), "
        f"top-3 accuracy={np.mean(fold_top3):.3f} "
        f"(SD {np.std(fold_top3):.3f})"
    )
    print("\nPer-disease held-out metrics (precision / recall / F1 / support):")

    out_of_fold_truth = np.asarray(out_of_fold_truth)
    out_of_fold_prediction = np.asarray(out_of_fold_prediction)
    for class_index, disease in enumerate(encoder.classes_):
        truth = out_of_fold_truth == class_index
        prediction = out_of_fold_prediction == class_index
        support = int(truth.sum())
        if support == 0:
            print(f"{disease}: not present in any test fold")
            continue
        true_positive = int(np.sum((truth == 1) & (prediction == 1)))
        false_positive = int(np.sum((truth == 0) & (prediction == 1)))
        false_negative = support - true_positive
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0
        recall = true_positive / support
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
        print(f"{disease}: {precision:.3f} / {recall:.3f} / {f1:.3f} / {support}")

    if missing_test_classes:
        print(
            "\nDiseases absent from at least one test fold: "
            + ", ".join(sorted(missing_test_classes))
        )
    print(
        "\nThese metrics measure performance on this dataset only. "
        "They do not establish clinical validity or calibrated probabilities."
    )


if __name__ == "__main__":
    evaluate()
