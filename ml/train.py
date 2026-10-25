r"""
QoSBoost ML Classifier Training & Evaluation.

Trains a Random Forest model on statistical flow features:
- packet size (mean, std)
- inter-arrival time (mean, std)
- flow duration
- bytes/sec

Outputs:
1. Serialized model: `ml/model.joblib`
2. Evaluation report: `ml/evaluation_report.json` (Accuracy, Confusion Matrix, Classification Report)
"""

import json
import os
import sys
from typing import Any, Dict

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ml.dataset_generator import DEFAULT_DATASET_PATH, generate_full_dataset

MODEL_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")
REPORT_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "evaluation_report.json")
FEATURE_NAMES = [
    "mean_packet_size",
    "std_packet_size",
    "mean_inter_arrival_time",
    "std_inter_arrival_time",
    "flow_duration",
    "bytes_per_sec",
]
CLASSES = ["voice", "video", "web", "bulk"]


def train_and_evaluate(
    dataset_path: str = DEFAULT_DATASET_PATH,
    model_output: str = MODEL_OUTPUT_PATH,
    report_output: str = REPORT_OUTPUT_PATH,
) -> Dict[str, Any]:
    """Trains a Random Forest classifier and computes accuracy and confusion matrix."""
    if not os.path.exists(dataset_path):
        print("Dataset not found. Generating new dataset...")
        generate_full_dataset(samples_per_class=600, output_path=dataset_path)

    df = pd.read_csv(dataset_path)

    X = df[FEATURE_NAMES]
    y = df["traffic_class"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    cm = confusion_matrix(y_test, y_pred, labels=CLASSES).tolist()
    report_dict = classification_report(y_test, y_pred, labels=CLASSES, output_dict=True)

    # Feature importances
    feature_importances = {
        name: round(float(imp), 4)
        for name, imp in zip(FEATURE_NAMES, clf.feature_importances_)
    }

    # Persist model
    os.makedirs(os.path.dirname(model_output), exist_ok=True)
    joblib.dump(clf, model_output)

    # Persist evaluation report
    report_payload = {
        "model_type": "RandomForestClassifier",
        "n_estimators": 100,
        "features": FEATURE_NAMES,
        "classes": CLASSES,
        "overall_accuracy": round(acc, 4),
        "accuracy_percentage": round(acc * 100.0, 2),
        "test_samples_count": len(y_test),
        "train_samples_count": len(y_train),
        "confusion_matrix": cm,
        "classification_report": report_dict,
        "feature_importances": feature_importances,
    }

    with open(report_output, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2)

    return report_payload


if __name__ == "__main__":
    rep = train_and_evaluate()
    print("=" * 60)
    print("QoSBoost Machine Learning Traffic Classifier — Training Report")
    print("=" * 60)
    print(f"Overall Accuracy: {rep['accuracy_percentage']}%")
    print("\nConfusion Matrix (Classes: voice, video, web, bulk):")
    for row in rep["confusion_matrix"]:
        print(" ", row)
    print("\nFeature Importances:")
    for k, v in rep["feature_importances"].items():
        print(f"  - {k}: {v * 100:.2f}%")
    print(f"\nModel saved to: {MODEL_OUTPUT_PATH}")
    print(f"Report saved to: {REPORT_OUTPUT_PATH}")
