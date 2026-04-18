from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError, PyJWKClient
from pydantic import BaseModel, Field

from .runtime import setup_service_runtime


@dataclass(frozen=True)
class Settings:
    realm: str = os.getenv("AUTH_REALM", "ent-est")
    issuer: str = os.getenv("AUTH_ISSUER", "http://localhost:8080/realms/ent-est")
    jwks_url: str = os.getenv(
        "AUTH_JWKS_URL",
        "http://keycloak:8080/realms/ent-est/protocol/openid-connect/certs",
    )
    audience: str = os.getenv("AUTH_AUDIENCE", "ent-gateway,ent-frontend")
    verify_audience: bool = os.getenv("AUTH_VERIFY_AUDIENCE", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


class IntrospectRequest(BaseModel):
    token: str = Field(min_length=20)


class IntrospectResponse(BaseModel):
    active: bool
    claims: dict[str, Any] | None = None


settings = Settings()
security = HTTPBearer(auto_error=False)
jwks_client = PyJWKClient(settings.jwks_url)


def _accepted_audiences() -> list[str]:
    return [aud.strip() for aud in settings.audience.split(",") if aud.strip()]


def _has_accepted_audience(claims: dict[str, Any]) -> bool:
    accepted = set(_accepted_audiences())
    aud_claim = claims.get("aud")
    if isinstance(aud_claim, str):
        token_aud = {aud_claim}
    elif isinstance(aud_claim, list):
        token_aud = {str(item) for item in aud_claim}
    else:
        token_aud = set()

    azp = claims.get("azp")
    if isinstance(azp, str):
        token_aud.add(azp)

    return bool(token_aud.intersection(accepted))

app = FastAPI(
    title="MS-Auth-Core",
    version="0.1.0",
    description="JWT validation and identity extraction service for ENT EST Salé.",
)
setup_service_runtime(app, "ms-auth-core")


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def decode_jwt_token(token: str) -> dict[str, Any]:
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            key=signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False, "verify_iss": False},
        )
        if settings.verify_audience and not _has_accepted_audience(claims):
            raise _unauthorized("Invalid token audience")
        return claims
    except ExpiredSignatureError as exc:
        print(f"Token expired: {exc}")
        raise _unauthorized("Token expired") from exc
    except InvalidTokenError as exc:
        print(f"Invalid token: {exc}")
        raise _unauthorized("Invalid token") from exc
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Unable to validate token: {exc}")
        raise _unauthorized("Unable to validate token") from exc


def get_bearer_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("Missing bearer token")
    return decode_jwt_token(credentials.credentials)


@app.get("/auth/health", tags=["auth"])
def auth_health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ms-auth-core",
        "realm": settings.realm,
    }


@app.get("/auth/me", tags=["auth"])
def auth_me(claims: dict[str, Any] = Depends(get_bearer_claims)) -> dict[str, Any]:
    return {
        "sub": claims.get("sub"),
        "preferred_username": claims.get("preferred_username"),
        "email": claims.get("email"),
        "realm_access": claims.get("realm_access", {}),
        "aud": claims.get("aud"),
        "iss": claims.get("iss"),
        "exp": claims.get("exp"),
        "iat": claims.get("iat"),
    }


@app.post("/auth/introspect", response_model=IntrospectResponse, tags=["auth"])
def auth_introspect(payload: IntrospectRequest) -> IntrospectResponse:
    try:
        claims = decode_jwt_token(payload.token)
        return IntrospectResponse(active=True, claims=claims)
    except HTTPException:
        return IntrospectResponse(active=False, claims=None)
