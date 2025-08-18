from fastapi import APIRouter

auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.post("/login")
async def login(credentials: dict):
    """Login a user.

    Args:
        credentials (dict): The login credentials containing username and password.

    Returns:
        dict: A message indicating the login status and the provided credentials.
    """
    return {"message": "Login successful", "credentials": credentials}