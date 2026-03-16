from fastapi import HTTPException, status

class BaseAPIException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=detail)

class DatabaseError(BaseAPIException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LLMError(BaseAPIException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_502_BAD_GATEWAY)

class ValidationError(BaseAPIException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)

class ResourceNotFoundError(BaseAPIException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)
