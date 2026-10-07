"""RFC4226 vectors and narrow replay-resistant RFC6238 validation."""

import base64

import pytest

from app.mfa import hotp, valid_counter

SECRET = base64.b32encode(b"12345678901234567890").decode()


@pytest.mark.parametrize(
    "counter,code",
    list(
        enumerate(
            [
                "755224",
                "287082",
                "359152",
                "969429",
                "338314",
                "254676",
                "287922",
                "162583",
                "399871",
                "520489",
            ]
        )
    ),
)
def test_hotp_rfc4226_vectors(counter, code):
    assert hotp(SECRET, counter) == code


@pytest.mark.parametrize(
    "instant,code",
    [
        (59, "287082"),
        (1111111109, "081804"),
        (1111111111, "050471"),
        (1234567890, "005924"),
        (2000000000, "279037"),
        (20000000000, "353130"),
    ],
)
def test_totp_rfc6238_sha1_six_digit_vectors(instant, code):
    assert valid_counter(SECRET, code, instant) == instant // 30
    assert valid_counter(SECRET, code, instant, last=instant // 30) is None


@pytest.mark.parametrize("code", ["", "12345", "1234567", "abcdef", "１２３４５６", "000000"])
def test_invalid_format_and_nonmatching_code(code):
    assert valid_counter(SECRET, code, 0) is None


def test_skew_window_and_negative_counter_boundary():
    assert valid_counter(SECRET, hotp(SECRET, 0), 0) == 0
    assert valid_counter(SECRET, hotp(SECRET, 9), 300) == 9
    assert valid_counter(SECRET, hotp(SECRET, 11), 300) == 11
    assert valid_counter(SECRET, hotp(SECRET, 8), 300) is None
