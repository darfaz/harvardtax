import pytest
from app.qbo.client import QBOClient


def test_qbo_client_init():
    client = QBOClient(access_token="test", realm_id="123")
    assert client.realm_id == "123"
    assert "Bearer test" in client.headers["Authorization"]
    assert "sandbox" in client.base_url


def test_qbo_base_url_sandbox():
    client = QBOClient(access_token="t", realm_id="1")
    assert "sandbox" in client.base_url
