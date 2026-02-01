from typing import Any

class Request:
    method: str
    url: str

class Response:
    status_code: int
    content: bytes
    text: str
    request: Request

    def raise_for_status(self) -> None: ...
    def json(self) -> Any: ...

class HTTPError(Exception):
    response: Response | None
    request: Request

class RequestException(Exception):
    response: Response | None
    request: Request

class exceptions:
    HTTPError = HTTPError
    RequestException = RequestException

def request(method: str, url: str, **kwargs: Any) -> Response: ...
