class AppError(Exception):
    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.status = "fail" if 400 <= status_code < 500 else "error"
