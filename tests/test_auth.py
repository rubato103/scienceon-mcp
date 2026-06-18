"""토큰 암호화(AES256) 단위 테스트 — 라이브 호출 없음."""
import base64
import json
import re

import pytest
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from scienceon_mcp.auth import _IV, encrypt_accounts


def test_encrypt_accounts_roundtrip():
    key = "f" * 32  # 32바이트 키
    enc = encrypt_accounts(key, "AA-BB-CC-DD-EE-FF")
    # urlsafe base64 → AES-256-CBC(고정 IV) 복호화 → JSON 평문
    ct = base64.urlsafe_b64decode(enc)
    pt = unpad(AES.new(key.encode("utf-8"), AES.MODE_CBC, _IV).decrypt(ct), 16).decode("utf-8")
    data = json.loads(pt)
    assert data["mac_address"] == "AA-BB-CC-DD-EE-FF"
    assert re.fullmatch(r"\d{14}", data["datetime"])  # YYYYMMDDHHMMSS


def test_encrypt_accounts_requires_32byte_key():
    with pytest.raises(ValueError):
        encrypt_accounts("too-short", "AA-BB-CC-DD-EE-FF")
