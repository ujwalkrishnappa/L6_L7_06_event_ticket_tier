from hypothesis import given, strategies as st
from processor import decode_promo_voucher, calculate_seat_tier_price, parse_attendee_badge

@given(st.text() | st.none())
def test_decode_promo_voucher_no_crash(s):
    #To-Do:Using try and except complete this function.
    pass

@given(st.text() | st.none())
def test_calculate_seat_tier_price_safe(s):
    #To-Do:Using try and except complete this function.
    pass

@given(st.text() | st.none())
def test_parse_attendee_badge_safe(s):
    #To-Do:Using try and except complete this function.
    pass