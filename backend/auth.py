import base64
import hashlib
import hmac
import json
import secrets
import time


PASSWORD_HASH_ITERATIONS = 600_000
MAX_PASSWORD_HASH_ITERATIONS = 2_000_000
TOKEN_LIFETIME_SECONDS = 8 * 60 * 60


def _encode_segment(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode_segment(value):
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    )
    return "pbkdf2_sha256${}${}${}".format(
        PASSWORD_HASH_ITERATIONS, _encode_segment(salt), _encode_segment(digest)
    )


def verify_password(password, encoded_hash):
    try:
        algorithm, iterations, salt, expected_digest = encoded_hash.split("$")
        iterations = int(iterations)
        if algorithm != "pbkdf2_sha256" or not 1 <= iterations <= MAX_PASSWORD_HASH_ITERATIONS:
            return False
        actual_digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), _decode_segment(salt), iterations
        )
        return hmac.compare_digest(actual_digest, _decode_segment(expected_digest))
    except (AttributeError, ValueError, TypeError):
        return False


def create_access_token(user, secret, now=None):
    issued_at = int(time.time() if now is None else now)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user["_id"]),
        "email": user["email"],
        "name": user["name"],
        "profession": user["profession"],
        "iat": issued_at,
        "exp": issued_at + TOKEN_LIFETIME_SECONDS,
        "iss": "pharmai",
    }
    signing_input = "{}.{}".format(
        _encode_segment(json.dumps(header, separators=(",", ":")).encode("utf-8")),
        _encode_segment(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
    )
    signature = hmac.new(secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return "{}.{}".format(signing_input, _encode_segment(signature))


def decode_access_token(token, secret, now=None):
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
        signing_input = "{}.{}".format(header_segment, payload_segment)
        expected_signature = hmac.new(
            secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(expected_signature, _decode_segment(signature_segment)):
            return None

        header = json.loads(_decode_segment(header_segment))
        payload = json.loads(_decode_segment(payload_segment))
        current_time = int(time.time() if now is None else now)
        if (
            header.get("alg") != "HS256"
            or payload.get("iss") != "pharmai"
            or not isinstance(payload.get("sub"), str)
            or not payload["sub"]
            or not isinstance(payload.get("exp"), int)
            or payload["exp"] <= current_time
        ):
            return None
        return payload
    except (AttributeError, ValueError, TypeError, json.JSONDecodeError):
        return None
