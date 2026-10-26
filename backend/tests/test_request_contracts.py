"""Milestone 2: schema validation and REST OpenAPI contract checks.

Run from backend/: python -m pytest -q
"""
from datetime import date, timedelta
import pytest
from pydantic import ValidationError
from schemas.request import RequestCreate, RequestUpdate, RequestRead


def valid_input():
    return {
        "date": (date.today() + timedelta(days=2)).isoformat(),
        "grade_level": "3a",
        "subject_id": 1,
        "time_slot": "08:00-10:00",
        "note": "German class",
    }


def test_create_schema_accepts_valid_json():
    payload = RequestCreate.model_validate(valid_input())
    assert payload.grade_level == "3a"
    assert payload.time_slot == "08:00-10:00"


@pytest.mark.parametrize("change", [
    {"grade_level": "99z"},
    {"subject_id": 0},
    {"time_slot": "14:00-08:00"},
    {"time_slot": "invalid"},
    {"date": "2020-01-01"},
    {"note": "x" * 1001},
])
def test_create_schema_rejects_invalid_json(change):
    data = valid_input()
    data.update(change)
    with pytest.raises(ValidationError):
        RequestCreate.model_validate(data)


def test_partial_update_allows_one_field():
    change = RequestUpdate.model_validate({"note": "Updated"})
    assert change.model_dump(exclude_unset=True) == {"note": "Updated"}


def test_openapi_contains_crud_endpoints():
    from main import app
    spec = app.openapi()
    base = "/api/v1/requests"
    assert "get" in spec["paths"][base + "/"]
    assert "post" in spec["paths"][base + "/"]
    assert "get" in spec["paths"][base + "/{request_id}"]
    assert "patch" in spec["paths"][base + "/{request_id}"]
    assert "delete" in spec["paths"][base + "/{request_id}"]
    operation = spec["paths"][base + "/"]["post"]
    assert "requestBody" in operation
    assert "201" in operation["responses"]
    assert "422" in operation["responses"]
