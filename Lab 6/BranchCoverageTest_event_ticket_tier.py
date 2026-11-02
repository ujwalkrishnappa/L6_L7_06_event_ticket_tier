import pytest
from event_ticket_tier import process_ticket_manifest, monitor_gate_flow


def make(tier="general", orders=None, lounge=False, confirmed=True):
    return {
        "is_confirmed": confirmed,
        "tier": tier,
        "exclusive_lounge": lounge,
        "orders": orders if orders is not None else [{"qty": 1, "promo": ""}],
    }


def order(qty=1, promo=""):
    return {"qty": qty, "promo": promo}



def test_single_general_order():
    result = process_ticket_manifest([make("general", [order(2)])], 0.1)
    assert result["total_revenue"] == 99.0
    assert result["status"] == "COMPLETED"


def test_manifests_not_a_list():
    with pytest.raises(ValueError):
        process_ticket_manifest("not a list", 0.1)


def test_negative_tax_rate():
    with pytest.raises(ValueError):
        process_ticket_manifest([], -0.1)


def test_zero_tax_rate_is_valid():
    result = process_ticket_manifest([make("general", [order(1)])], 0)
    assert result["total_revenue"] == 45.0


def test_empty_manifest_list():
    assert process_ticket_manifest([], 0.1) == {"total_revenue": 0.0, "status": "ZERO_SALES"}



def test_unconfirmed_manifest_skipped():
    result = process_ticket_manifest([make(confirmed=False)], 0.1)
    assert result["status"] == "ZERO_SALES"


def test_missing_confirmation_key_defaults_to_unconfirmed():
    result = process_ticket_manifest([{"tier": "vip", "orders": [order(1)]}], 0.0)
    assert result["status"] == "ZERO_SALES"


def test_missing_tier_defaults_to_general():
    result = process_ticket_manifest(
        [{"is_confirmed": True, "orders": [order(1)]}], 0.0)
    assert result["total_revenue"] == 45.0


def test_missing_orders_key_gives_no_sales():
    result = process_ticket_manifest([{"is_confirmed": True, "tier": "vip"}], 0.0)
    assert result["status"] == "ZERO_SALES"



def test_vip_tier_price():
    assert process_ticket_manifest([make("vip", [order(1)])], 0.0)["total_revenue"] == 150.0


def test_premium_tier_price():
    assert process_ticket_manifest([make("premium", [order(1)])], 0.0)["total_revenue"] == 90.0


def test_general_tier_price():
    assert process_ticket_manifest([make("general", [order(1)])], 0.0)["total_revenue"] == 45.0


def test_unknown_tier_rejected():
    result = process_ticket_manifest([make("balcony", [order(1)])], 0.0)
    assert result["status"] == "ZERO_SALES"



def test_zero_qty_rejected():
    result = process_ticket_manifest([make("general", [order(0)])], 0.0)
    assert result["status"] == "ZERO_SALES"


def test_negative_qty_rejected():
    result = process_ticket_manifest([make("general", [order(-3)])], 0.0)
    assert result["status"] == "ZERO_SALES"


def test_missing_qty_defaults_to_zero():
    result = process_ticket_manifest([make("general", [{"promo": ""}])], 0.0)
    assert result["status"] == "ZERO_SALES"



def test_fraud_risk_vip_zeroes_manifest_and_breaks():
    # first order is added, second is FRAUD_RISK -> total reset, third never processed
    orders = [order(1), order(1, "FRAUD_RISK"), order(1)]
    result = process_ticket_manifest([make("vip", orders)], 0.0)
    assert result["status"] == "ZERO_SALES"


def test_fraud_risk_vip_with_lounge_only_lounge_remains():
    result = process_ticket_manifest(
        [make("vip", [order(2, "FRAUD_RISK")], lounge=True)], 0.0)
    assert result["total_revenue"] == 75.0
    assert result["status"] == "COMPLETED"


def test_fraud_risk_non_vip_still_billed():
    result = process_ticket_manifest([make("general", [order(2, "FRAUD_RISK")])], 0.0)
    assert result["total_revenue"] == 90.0
    assert result["status"] == "COMPLETED"


def test_earlybird_discount():
    result = process_ticket_manifest([make("premium", [order(2, "EARLYBIRD")])], 0.0)
    assert result["total_revenue"] == pytest.approx(144.0)


def test_earlybird_gets_no_bulk_discount():
    result = process_ticket_manifest([make("general", [order(5, "EARLYBIRD")])], 0.0)
    assert result["total_revenue"] == pytest.approx(180.0)


def test_bulk_discount_at_boundary_qty_5():
    assert process_ticket_manifest([make("general", [order(5)])], 0.0)["total_revenue"] == 205.0


def test_no_bulk_discount_at_qty_4():
    assert process_ticket_manifest([make("general", [order(4)])], 0.0)["total_revenue"] == 180.0


def test_unknown_promo_code_treated_as_no_promo():
    result = process_ticket_manifest([make("general", [order(5, "SUMMER")])], 0.0)
    assert result["total_revenue"] == 205.0



def test_exclusive_lounge_surcharge():
    result = process_ticket_manifest([make("general", [order(1)], lounge=True)], 0.0)
    assert result["total_revenue"] == 120.0


def test_no_lounge_surcharge():
    result = process_ticket_manifest([make("general", [order(1)], lounge=False)], 0.0)
    assert result["total_revenue"] == 45.0


def test_audit_rejected_over_four_rejections():
    result = process_ticket_manifest([make("balcony")] * 5, 0.0)
    assert result["status"] == "AUDIT_REJECTED"


def test_exactly_four_rejections_not_audit_rejected():
    manifests = [make("balcony")] * 4 + [make("general", [order(1)])]
    result = process_ticket_manifest(manifests, 0.0)
    assert result["status"] == "COMPLETED"


def test_audit_rejected_with_revenue_includes_tax():
    manifests = [make("general", [order(1)])] + [make("balcony")] * 5
    result = process_ticket_manifest(manifests, 0.1)
    assert result == {"total_revenue": 49.5, "status": "AUDIT_REJECTED"}


def test_zero_sales_status():
    result = process_ticket_manifest([make("general", [order(0)])], 0.2)
    assert result == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_gate_no_data_empty_list():
    assert monitor_gate_flow([]) == "NO_DATA"


def test_gate_no_data_none():
    assert monitor_gate_flow(None) == "NO_DATA"


def test_gate_overflow_two_consecutive():
    assert monitor_gate_flow([[10, 60, 70]]) == "OVERFLOW"


def test_gate_streak_reset_no_overflow():
    assert monitor_gate_flow([[60, 10, 60, 10]]) == "FLOW_NORMAL"


def test_gate_rate_exactly_50_not_congested():
    assert monitor_gate_flow([[50, 50, 50]]) == "FLOW_NORMAL"


def test_gate_overflow_in_second_stream():
    assert monitor_gate_flow([[10, 20], [60, 60]]) == "OVERFLOW"


def test_gate_streak_does_not_carry_across_streams():
    assert monitor_gate_flow([[10, 60], [60, 10]]) == "FLOW_NORMAL"


def test_gate_empty_stream():
    assert monitor_gate_flow([[]]) == "FLOW_NORMAL"
