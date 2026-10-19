# resources\tests\test_auth_refresh_classification.py

import requests
from backend.interfaces import TransientAuthError
from backend.services.auth.auth_service import BaseOAuthManager


def _http_error(status: int) -> requests.exceptions.HTTPError:
    response = requests.Response()
    response.status_code = status
    return requests.exceptions.HTTPError(response=response)

def test_invalid_refresh_is_classified_as_invalid():
    assert BaseOAuthManager._classify_refresh_error(_http_error(400)) == "invalid"
    assert BaseOAuthManager._classify_refresh_error(_http_error(401)) == "invalid"

def test_server_and_network_errors_are_transient():
    assert BaseOAuthManager._classify_refresh_error(_http_error(500)) == "transient"
    assert BaseOAuthManager._classify_refresh_error(_http_error(503)) == "transient"
    assert BaseOAuthManager._classify_refresh_error(requests.exceptions.ConnectionError("net")) == "transient"
    assert BaseOAuthManager._classify_refresh_error(requests.exceptions.Timeout("t")) == "transient"

def test_transient_auth_error_is_an_exception():
    assert issubclass(TransientAuthError, Exception)
