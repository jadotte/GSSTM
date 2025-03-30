import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plus_code_calculator import encode, decode


def test_encoding():
    """Test the Plus Code encoding with known coordinates"""
    test_cases = [
        # Latitude, Longitude, Expected Plus Code
        (37.4224764, -122.0842499, "849VCWC8+R9"),  # Google HQ
        (-33.8567844, 151.2152967, "4RRH39P3+PF"),  # Sydney Opera House
        (51.5007292, -0.1246254, "9C3W9QCJ+MP"),  # Big Ben
        (90.0, 180.0, "CFX3X2X2+X2"),  # Max boundary
        (-90.0, -180.0, "2222222+22"),  # Min boundary
    ]

    for lat, lng, expected in test_cases:
        result = encode(lat, lng)
        print(
            f"Coordinates: ({lat}, {lng}) -> Generated: {result}, Expected: {expected}"
        )

        # Compare result with expected
        assert result == expected, f"Test failed for {lat}, {lng}"

    print("All tests passed!")


# Additional example: Test the decoding function
def test_decoding():
    """Test decoding Plus Codes back to coordinates"""
    # For the decoding test, we need to adjust our expectations
    # Plus Codes represent areas, and decoding returns the center of that area
    # So we should expect coordinates that are close but not exactly matching the original

    # Define some known codes and their approximate decoded locations
    test_cases = [
        # Plus Code, Expected approximate (latitude, longitude)
        ("849VCWC8+R9", (37.422, -122.084)),  # Google HQ (approximate)
        ("4RRH39P3+PF", (-33.856, 151.215)),  # Sydney Opera House (approximate)
    ]

    for code, expected in test_cases:
        lat, lng = decode(code)
        print(
            f"Plus Code: {code} -> Decoded: ({lat}, {lng}), Expected approx: ({expected[0]}, {expected[1]})"
        )

        # We're expecting approximate matches rather than exact coordinates
        # A tolerance of 0.001 degrees is about 100 meters at the equator
        assert abs(lat - expected[0]) < 0.001, f"Latitude decode test failed for {code}"
        assert abs(lng - expected[1]) < 0.001, (
            f"Longitude decode test failed for {code}"
        )

    print("All decode tests passed!")


if __name__ == "__main__":
    test_encoding()

    # Example: Convert a specific location
    lat, lng = 37.7749, -122.4194  # San Francisco
    plus_code = encode(lat, lng)
    print(f"San Francisco Plus Code: {plus_code}")

    # Test the decode function
    test_decoding()
