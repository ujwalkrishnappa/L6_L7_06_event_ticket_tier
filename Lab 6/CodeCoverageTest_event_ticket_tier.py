import pytest
from event_ticket_tier import process_ticket_manifest, monitor_gate_flow


def make(tier="general", qty=1, promo="", lounge=False, confirmed=True):
    return {
        "is_confirmed": confirmed,
        "tier": tier,
        "exclusive_lounge": lounge,
        "orders": [{"qty": qty, "promo": promo}],
    }


def test_single_general_order():
    result = process_ticket_manifest([make("general", 2)], 0.1)
    assert result["total_revenue"] == 99.0
    assert result["status"] == "COMPLETED"


def test_invalid_manifests_not_list():
    with pytest.raises(ValueError):
        process_ticket_manifest("not a list", 0.1)


def test_negative_tax_rate():
    with pytest.raises(ValueError):
        process_ticket_manifest([], -0.1)


def test_unconfirmed_manifest_skipped():
    result = process_ticket_manifest([make(confirmed=False)], 0.1)
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_vip_tier_price():
    result = process_ticket_manifest([make("vip", 1)], 0.0)
    assert result["total_revenue"] == 150.0


def test_premium_tier_price():
    result = process_ticket_manifest([make("premium", 1)], 0.0)
    assert result["total_revenue"] == 90.0


def test_unknown_tier_rejected():
    result = process_ticket_manifest([make("balcony", 1)], 0.0)
    assert result["status"] == "ZERO_SALES"


def test_zero_qty_rejected():
    result = process_ticket_manifest([make("general", 0)], 0.0)
    assert result["status"] == "ZERO_SALES"


def test_fraud_risk_vip_zeroes_manifest():
    result = process_ticket_manifest([make("vip", 2, "FRAUD_RISK")], 0.0)
    assert result["status"] == "ZERO_SALES"


def test_fraud_risk_non_vip_still_billed():
    result = process_ticket_manifest([make("general", 2, "FRAUD_RISK")], 0.0)
    assert result["total_revenue"] == 90.0
    assert result["status"] == "COMPLETED"


def test_earlybird_discount():
    result = process_ticket_manifest([make("premium", 2, "EARLYBIRD")], 0.0)
    assert result["total_revenue"] == pytest.approx(144.0)


def test_bulk_discount_qty_5():
    result = process_ticket_manifest([make("general", 5)], 0.0)
    assert result["total_revenue"] == 205.0


def test_exclusive_lounge_surcharge():
    result = process_ticket_manifest([make("general", 1, lounge=True)], 0.0)
    assert result["total_revenue"] == 120.0


def test_audit_rejected_over_four_rejections():
    manifests = [make("balcony")] * 5
    result = process_ticket_manifest(manifests, 0.0)
    assert result["status"] == "AUDIT_REJECTED"



def test_gate_no_data():
    assert monitor_gate_flow([]) == "NO_DATA"


def test_gate_overflow():
    assert monitor_gate_flow([[10, 60, 70]]) == "OVERFLOW"


def test_gate_flow_normal():
    assert monitor_gate_flow([[10, 20, 30]]) == "FLOW_NORMAL"
