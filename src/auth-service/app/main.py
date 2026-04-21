from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import httpx

from .config import settings
from .auth import hash_password, verify_password, create_access_token, decode_token

# --- FastAPI Setup ---
app = FastAPI(
    title="Remailder Auth Service",
    description="Microserviciu de autentificare și autorizare",
    version="1.0.0"
)

security = HTTPBearer()


# --- Schemas ---
class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str


# --- Dependency: Get Current User from JWT ---
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Extract and validate the user from the Bearer token."""
    token = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token invalid sau expirat")
    return payload


# --- Routes ---

@app.get("/health")
async def health():
    return {"status": "ok", "service": "auth-service"}


@app.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest):
    """
    Register a new user.
    1. Hash the password
    2. Send the user data to io-service for DB persistence
    3. Return a JWT token for immediate login
    """
    password_hash = hash_password(payload.password)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.IO_SERVICE_URL}/users",
                json={
                    "email": payload.email,
                    "password_hash": password_hash
                },
                timeout=10.0
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Serviciul de date (io-service) nu este disponibil"
            )

    if response.status_code == 400:
        raise HTTPException(status_code=400, detail="Email-ul este deja înregistrat")
    elif response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=f"Eroare la crearea contului: {response.text}"
        )

    user_data = response.json()
    access_token = create_access_token({
        "sub": str(user_data["id"]),
        "email": user_data["email"]
    })

    return TokenResponse(
        access_token=access_token,
        user_id=user_data["id"],
        email=user_data["email"]
    )


@app.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    """
    Authenticate a user.
    1. Fetch user by email from io-service
    2. Verify password against stored hash
    3. Return a JWT token
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.IO_SERVICE_URL}/users/{payload.email}",
                timeout=10.0
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Serviciul de date (io-service) nu este disponibil"
            )

    if response.status_code == 404:
        raise HTTPException(status_code=401, detail="Email sau parolă incorectă")
    elif response.status_code != 200:
        raise HTTPException(status_code=500, detail="Eroare la autentificare")

    user_data = response.json()

    if not verify_password(payload.password, user_data["password_hash"]):
        raise HTTPException(status_code=401, detail="Email sau parolă incorectă")

    access_token = create_access_token({
        "sub": str(user_data["id"]),
        "email": user_data["email"]
    })

    return TokenResponse(
        access_token=access_token,
        user_id=user_data["id"],
        email=user_data["email"]
    )


@app.get("/me")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Return the authenticated user's profile from the JWT token."""
    return {
        "user_id": int(current_user["sub"]),
        "email": current_user["email"]
    }


@app.delete("/account")
async def delete_account(current_user: dict = Depends(get_current_user)):
    """Delete the authenticated user's account."""
    email = current_user["email"]

    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{settings.IO_SERVICE_URL}/users/{email}",
                timeout=10.0
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Serviciul de date (io-service) nu este disponibil"
            )

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Eroare la ștergerea contului")

    return {"detail": "Contul a fost șters cu succes"}
