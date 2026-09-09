"""
HTTPException adapters for Auth domain exceptions.

Rule: Contains ONLY HTTPException subclasses.  No domain logic here.
"""

from fastapi import HTTPException, status


class UserAlreadyExistsHTTPError(HTTPException):
    def __init__(self, detail: str = "Email already registered"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class InvalidCredentialsHTTPError(HTTPException):
    def __init__(self, detail: str = "Invalid email or password"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class InvalidTokenHTTPError(HTTPException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class UserNotFoundHTTPError(HTTPException):
    def __init__(self, detail: str = "User not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)