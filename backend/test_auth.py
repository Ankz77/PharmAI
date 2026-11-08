from auth import (
    TOKEN_LIFETIME_SECONDS,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_verifies_only_correct_password():
    encoded_hash = hash_password("a-long-clinician-password")

    assert verify_password("a-long-clinician-password", encoded_hash)
    assert not verify_password("different-password", encoded_hash)
    assert not verify_password("anything", "invalid-hash")


def test_access_token_signature_and_expiry_are_checked():
    user = {
        "_id": "clinician-123",
        "email": "doctor@example.com",
        "name": "Dr. Example",
        "profession": "Doctor",
    }
    token = create_access_token(user, "test-secret-that-is-long-enough", now=1000)

    assert decode_access_token(token, "test-secret-that-is-long-enough", now=1001)["sub"] == "clinician-123"
    assert decode_access_token(token, "wrong-secret", now=1001) is None
    assert decode_access_token(
        token, "test-secret-that-is-long-enough", now=1000 + TOKEN_LIFETIME_SECONDS
    ) is None
