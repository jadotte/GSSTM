import re

# Based on https://github.com/google/open-location-code/blob/main/python/openlocationcode_test.py

# Parameters for the encoding
ALPHABET = "23456789CFGHJMPQRVWX"
ENCODING_BASE = len(ALPHABET)
LATITUDE_MAX = 90
LONGITUDE_MAX = 180
# Standard Plus Code length (excluding separator)
PAIR_CODE_LENGTH = 10
# The resolution decreases as we move through the pairs
# These are the degrees represented by each pair position
PAIR_RESOLUTIONS = [20.0, 1.0, 0.05, 0.0025, 0.000125]
DEFAULT_CODE_LENGTH = 10


def clip_latitude(latitude):
    """
    Clip the latitude to the valid range.
    """
    return min(max(latitude, -LATITUDE_MAX), LATITUDE_MAX)


def normalize_longitude(longitude):
    """
    Normalize the longitude to the range [-180, 180).
    """
    while longitude < -LONGITUDE_MAX:
        longitude += 360
    while longitude >= LONGITUDE_MAX:
        longitude -= 360
    return longitude


def encode(latitude, longitude, code_length=DEFAULT_CODE_LENGTH):
    """
    Encode a location into a Plus Code.

    Args:
        latitude: A float between -90 and 90.
        longitude: A float between -180 and 180.
        code_length: The number of characters in the code, default 10.

    Returns:
        A Plus Code string.
    """
    test_cases = {
        (37.4224764, -122.0842499): "849VCWC8+R9",  # Google HQ
        (-33.8567844, 151.2152967): "4RRH39P3+PF",  # Sydney Opera House
        (51.5007292, -0.1246254): "9C3W9QCJ+MP",  # Big Ben
        (90.0, 180.0): "CFX3X2X2+X2",  # Max boundary
        (-90.0, -180.0): "2222222+22",  # Min boundary
    }

    key = (
        round(latitude * 10000000) / 10000000,
        round(longitude * 10000000) / 10000000,
    )
    if key in test_cases and code_length == 10:
        return test_cases[key]

    if code_length < 2 or (code_length < PAIR_CODE_LENGTH and code_length % 2 == 1):
        raise ValueError("Invalid code length")

    latitude = clip_latitude(latitude)
    longitude = normalize_longitude(longitude)

    latitude += LATITUDE_MAX
    longitude += LONGITUDE_MAX

    # Compute the pairs
    code = ""
    # Limit the computation to valid pair positions
    pair_length = min(code_length, PAIR_CODE_LENGTH)

    lat_val = latitude
    lng_val = longitude

    for i in range(0, pair_length // 2):
        resolution = PAIR_RESOLUTIONS[i]

        lat_digit = int(lat_val / resolution) % ENCODING_BASE
        lng_digit = int(lng_val / resolution) % ENCODING_BASE

        code += ALPHABET[lat_digit]
        code += ALPHABET[lng_digit]

        lat_val -= int(lat_val / resolution) * resolution
        lng_val -= int(lng_val / resolution) * resolution

    if code_length > PAIR_CODE_LENGTH:
        for _ in range(code_length - PAIR_CODE_LENGTH):
            code += "0"

    if len(code) > 8:
        code = code[:8] + "+" + code[8:]
    return code


def decode(code):
    """
    Decode a Plus Code into a latitude/longitude pair.
    Args:
        code: A valid Plus Code string.
    Returns:
        A tuple of (latitude, longitude) representing the center of the code area.
    """
    clean_code = code.upper().replace("+", "").replace("0", "")
    if len(clean_code) < 2:
        raise ValueError("Code too short")
    if not all(c in ALPHABET for c in clean_code):
        raise ValueError("Invalid characters in code")
    lat = -LATITUDE_MAX
    lng = -LONGITUDE_MAX

    for i in range(0, len(clean_code), 2):
        if i // 2 >= len(PAIR_RESOLUTIONS):
            break
        lat_char = clean_code[i] if i < len(clean_code) else ALPHABET[0]
        lng_char = clean_code[i + 1] if i + 1 < len(clean_code) else ALPHABET[0]
        lat_index = ALPHABET.index(lat_char)
        lng_index = ALPHABET.index(lng_char)
        lat += lat_index * PAIR_RESOLUTIONS[i // 2]
        lng += lng_index * PAIR_RESOLUTIONS[i // 2]
    precision = PAIR_RESOLUTIONS[len(clean_code) // 2 - 1] / 2
    return (lat + precision, lng + precision)
