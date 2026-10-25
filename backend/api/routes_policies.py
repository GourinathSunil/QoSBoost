"""
REST routes for QoS Policies and Profiles.
"""

import os
import time
from typing import Any, Dict

import yaml
from fastapi import APIRouter, HTTPException

import asyncio

from backend.database import save_event, save_policy_config
from backend.models.schemas import EventRecordDB, PolicyConfigDB, PolicyUpdateRequest
from backend.services.controller_client import controller_client
from backend.services.telemetry_service import telemetry_service

router = APIRouter(prefix="/api/policies", tags=["policies"])

POLICY_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "config", "policies.yaml")


def load_yaml_policies() -> Dict[str, Any]:
    with open(POLICY_CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_yaml_policies(data: Dict[str, Any]):
    with open(POLICY_CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)


@router.get("")
def get_policies() -> Dict[str, Any]:
    """Returns active policy profiles and master QoS toggle state."""
    data = load_yaml_policies()
    data["qos_enabled"] = telemetry_service.qos_enabled
    return data


@router.put("")
async def update_policies(req: PolicyUpdateRequest) -> Dict[str, Any]:
    """Updates active profile or modifies QoS parameters live."""
    data = load_yaml_policies()

    if req.active_profile not in data.get("profiles", {}):
        raise HTTPException(
            status_code=400, detail=f"Profile '{req.active_profile}' does not exist."
        )

    before_profile = data.get("active_profile")
    data["active_profile"] = req.active_profile

    if req.qos_enabled is not None:
        telemetry_service.set_qos_enabled(req.qos_enabled)
        data["qos_enabled"] = req.qos_enabled

    if req.profiles:
        # Update custom class rate definitions if provided
        for p_name, p_val in req.profiles.items():
            if p_name in data["profiles"]:
                data["profiles"][p_name] = p_val.model_dump()

    # 1. Save to YAML
    save_yaml_policies(data)

    # 2. Persist to SQLite
    now = time.time()
    save_policy_config(
        PolicyConfigDB(
            timestamp=now,
            active_profile=req.active_profile,
            qos_enabled=telemetry_service.qos_enabled,
            raw_yaml=yaml.dump(data),
        )
    )

    # 3. Push to Ryu controller (non-blocking)
    asyncio.create_task(controller_client.push_policy_to_controller(data))

    # 4. Log audit event
    save_event(
        EventRecordDB(
            timestamp=now,
            event_type="POLICY_UPDATE",
            message=f"QoS Policy updated: Profile set to '{req.active_profile}', QoS Master={telemetry_service.qos_enabled}",
            reason="User modification via Dashboard",
            before_value=f"Profile: {before_profile}",
            after_value=f"Profile: {req.active_profile}",
        )
    )

    return data


@router.post("/preset/{preset_name}")
async def switch_preset(preset_name: str) -> Dict[str, Any]:
    """Instant one-click preset profile switcher."""
    data = load_yaml_policies()
    if preset_name not in data.get("profiles", {}):
        raise HTTPException(status_code=404, detail=f"Preset '{preset_name}' not found.")

    data["active_profile"] = preset_name
    save_yaml_policies(data)

    now = time.time()
    save_policy_config(
        PolicyConfigDB(
            timestamp=now,
            active_profile=preset_name,
            qos_enabled=telemetry_service.qos_enabled,
            raw_yaml=yaml.dump(data),
        )
    )

    # Push to Ryu
    asyncio.create_task(controller_client.push_policy_to_controller(data))

    save_event(
        EventRecordDB(
            timestamp=now,
            event_type="PRESET_SWITCH",
            message=f"Active QoS preset switched to '{preset_name}'",
            reason="Quick preset selection",
        )
    )

    data["qos_enabled"] = telemetry_service.qos_enabled
    return data
