"""Smoke tests for the pydantic models.

These check that the models validate and serialise as consumers
(rctab-api, rctab-functions) expect, so that dependency updates
which change pydantic's behaviour are caught in CI.
"""

import datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from rctab_models import models

SUB_ID = "00000000-0000-0000-0000-000000000001"


def test_usage_round_trip() -> None:
    """A Usage survives a JSON round trip."""
    usage = models.Usage(
        id="usage-1",
        subscription_id=UUID(SUB_ID),
        date=datetime.date(2024, 1, 1),
        total_cost=1.5,
        tags={"project": "rctab"},
    )
    all_usage = models.AllUsage(
        usage_list=[usage],
        start_date=datetime.date(2024, 1, 1),
        end_date=datetime.date(2024, 1, 31),
    )

    restored = models.AllUsage.model_validate_json(all_usage.model_dump_json())

    assert restored == all_usage


def test_usage_is_hashable() -> None:
    """Equal HashBaseModel instances have equal hashes."""
    kwargs = {
        "subscription_id": SUB_ID,
        "start_datetime": "2024-01-01",
        "end_datetime": "2024-01-31",
        "cost": 1.0,
        "billing_currency": "GBP",
    }

    assert hash(models.CMUsage.model_validate(kwargs)) == hash(
        models.CMUsage.model_validate(kwargs)
    )


def test_cm_usage_rejects_negative_cost() -> None:
    """CMUsage cost must be non-negative."""
    with pytest.raises(ValidationError):
        models.CMUsage.model_validate(
            {
                "subscription_id": SUB_ID,
                "start_datetime": "2024-01-01",
                "end_datetime": "2024-01-31",
                "cost": -1.0,
                "billing_currency": "GBP",
            }
        )


def test_subscription_status_round_trip() -> None:
    """A SubscriptionStatus with role assignments survives a JSON round trip."""
    status = models.AllSubscriptionStatus(
        status_list=[
            models.SubscriptionStatus(
                subscription_id=UUID(SUB_ID),
                display_name="My subscription",
                state=models.SubscriptionState.ENABLED,
                role_assignments=(
                    models.RoleAssignment(
                        role_definition_id="role-1",
                        role_name="Owner",
                        principal_id="principal-1",
                        display_name="A User",
                    ),
                ),
            )
        ]
    )

    restored = models.AllSubscriptionStatus.model_validate_json(
        status.model_dump_json()
    )

    assert restored == status


def test_enums_serialise_to_values() -> None:
    """String enums serialise to their values, which the API relies on."""
    desired = models.DesiredState(
        subscription_id=UUID(SUB_ID),
        desired_state=models.SubscriptionState.DISABLED,
    )

    assert desired.model_dump(mode="json")["desired_state"] == "Disabled"


def test_default_currency() -> None:
    """Allocations default to GBP."""
    allocation = models.Allocation(sub_id=UUID(SUB_ID), ticket="T1", amount=10)

    assert allocation.currency == models.DEFAULT_CURRENCY == "GBP"
