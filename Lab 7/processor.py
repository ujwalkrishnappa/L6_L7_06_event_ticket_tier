def decode_promo_voucher(voucher_code):
    code = voucher_code.strip()
    prefix, pct_str = code.split('-')
    percentage = int(pct_str)
    return f"Valid {prefix.upper()}: {percentage}% OFF"

def calculate_seat_tier_price(tier_spec):
    parts = tier_spec.split('@')
    tier = parts[0].strip().upper()
    row = int(parts[1])
    tier_rates = {
        "VIP": 150.0,
        "PREMIUM": 90.0,
        "GENERAL": 45.0
    }
    base = tier_rates[tier]
    return base + (row * 2.0)

def parse_attendee_badge(badge_csv):
    tokens = badge_csv.split(',')
    name = tokens[0].strip()
    age = int(tokens[1])
    seat = tokens[2].strip()
    category = "Child" if age < 18 else "Adult"
    return f"{name} [{category}] - Seat {seat}"

def main():
    print("==== Running decode_promo_voucher ====")
    v_input = input("Enter voucher (e.g. EARLY-20): ")
    print("Voucher:", decode_promo_voucher(v_input))

    print("\n==== Running calculate_seat_tier_price ====")
    t_input = input("Enter tier spec (e.g. VIP@4): ")
    print("Seat Price: $", calculate_seat_tier_price(t_input))

    print("\n==== Running parse_attendee_badge ====")
    b_input = input("Enter badge CSV (Name,Age,Seat): ")
    print("Badge:", parse_attendee_badge(b_input))

if __name__ == "__main__":
    main()