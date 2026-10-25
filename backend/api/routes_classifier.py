"""
REST routes for Traffic Classifier (Rule-based vs Random Forest ML Mode).
"""

from typing import Any, Dict
from fastapi import APIRouter
from pydantic import BaseModel

from controller.classifier import TrafficClassifier

router = APIRouter(prefix="/api/classifier", tags=["classifier"])

# Shared global controller classifier reference
classifier_instance = TrafficClassifier()


class ClassifierModeRequest(BaseModel):
    ml_mode: bool


@router.get("/status")
def get_classifier_status() -> Dict[str, Any]:
    """Returns classifier mode, cached flows count, accuracy, and confusion matrix."""
    info = classifier_instance.get_ml_info()
    return {
        "ml_mode": classifier_instance.ml_mode,
        "cached_flows_count": classifier_instance.get_cache_size(),
        "model_info": info,
    }


@router.post("/mode")
def set_classifier_mode(req: ClassifierModeRequest) -> Dict[str, Any]:
    """Toggles classifier mode between Rule-based and Random Forest ML mode."""
    classifier_instance.set_ml_mode(req.ml_mode)
    return {
        "status": "success",
        "ml_mode": classifier_instance.ml_mode,
        "message": f"Traffic classifier switched to {'Random Forest ML' if req.ml_mode else 'Rule-Based'} mode.",
    }
