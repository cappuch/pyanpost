class AnPostError(Exception):
    pass


class AnPostHTTPError(AnPostError):
    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self.body = body
        super().__init__(f"HTTP {status_code}: {body}")


class AnPostParseError(AnPostError):
    pass
