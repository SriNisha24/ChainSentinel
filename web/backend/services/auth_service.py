"""ChainSentinel Authentication and Role-Based Access Control (RBAC) Service.

Provides secure local authentication for the academic prototype:
- Zero plaintext password storage (PBKDF2-HMAC-SHA256 with 100,000 iterations & unique salts).
- Cryptographic session token generation (secrets.token_hex(32)).
- Role hierarchy: ADMIN > REVIEWER > VIEWER.
- In-memory session tracking with automatic expiration.
"""

from __future__ import annotations

import datetime
import hashlib
import hmac
import logging
import secrets
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ChainSentinel.AuthService")

# Role definitions & hierarchy
ROLE_HIERARCHY: Dict[str, int] = {
    "VIEWER": 10,
    "REVIEWER": 20,
    "ADMIN": 30,
}

# Pre-hashed demo accounts (PBKDF2-HMAC-SHA256, 100,000 iterations)
# Passwords (academic demo reference in demo script):
#   viewer:   ViewerPass@2026!
#   reviewer: ReviewerPass@2026!
#   director: DirectorPass@2026!
#   admin:    AdminPass@2026!
USER_DATABASE: Dict[str, Dict[str, Any]] = {
    "viewer": {
        "username": "viewer",
        "full_name": "Operations Observer",
        "role": "VIEWER",
        "department": "Operations Monitoring",
        "salt_hex": "a7d0d1c972105d3e317ae10728080eed",
        "hash_hex": "3b05e8ffe3d5e6d7fbc1968d12ad435eba34a9f0259752df0301fe1d84600e5f",
        "is_active": True,
    },
    "reviewer": {
        "username": "reviewer",
        "full_name": "Senior Supply Chain Analyst",
        "role": "REVIEWER",
        "department": "Supply Chain Logistics",
        "salt_hex": "2eeab65b3ffec6efc6a11094d3ff6b5f",
        "hash_hex": "c65e4fa9adce9dc25a6ff5478eb8f9eb365115f9c54c1b35e89954406d7e2958",
        "is_active": True,
    },
    "director": {
        "username": "director",
        "full_name": "Director of Supply Chain Logistics",
        "role": "REVIEWER",
        "department": "Executive Supply Chain",
        "salt_hex": "42165696be65a6b80c949dc810dd71e8",
        "hash_hex": "c1cdb5a18616833063cd5c49eb58d9c1a40645f7ca811c9bba28c476bc7f42dc",
        "is_active": True,
    },
    "admin": {
        "username": "admin",
        "full_name": "Platform Safety & Reliability Administrator",
        "role": "ADMIN",
        "department": "Platform Reliability Engineering",
        "salt_hex": "1c92809fd1bb1084a51cd6005aeaf1c8",
        "hash_hex": "f390587e5437dbc6a13c55c236e434f2979294a0a3b3609b359780a588e2f41c",
        "is_active": True,
    },
}


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AuthorizationError(Exception):
    """Raised when an authenticated user lacks permission for an operation."""
    pass


class AuthService:
    """Manages prototype authentication, token generation, and authorization checks."""

    def __init__(self, token_lifetime_minutes: int = 60):
        self.token_lifetime = datetime.timedelta(minutes=token_lifetime_minutes)
        # In-memory session store: token -> Session dict
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def _verify_password(self, plain_password: str, salt_hex: str, expected_hash_hex: str) -> bool:
        salt_bytes = bytes.fromhex(salt_hex)
        computed_hash = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt_bytes, 100000).hex()
        return hmac.compare_digest(computed_hash, expected_hash_hex)

    def login(self, username: str, password: str, client_ip: str = "127.0.0.1") -> Dict[str, Any]:
        """Authenticates user credentials and issues a secure session token."""
        user = USER_DATABASE.get(username.lower().strip())
        if not user or not user["is_active"]:
            logger.warning(f"Failed login attempt for username: {username} from {client_ip}")
            raise AuthenticationError("Invalid username or password.")

        if not self._verify_password(password, user["salt_hex"], user["hash_hex"]):
            logger.warning(f"Invalid password for username: {username} from {client_ip}")
            raise AuthenticationError("Invalid username or password.")

        # Clean expired sessions occasionally
        self._prune_expired_sessions()

        token = secrets.token_hex(32)
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        expires_at = now_utc + self.token_lifetime

        session_data = {
            "token": token,
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"],
            "department": user["department"],
            "created_at": now_utc.isoformat(),
            "expires_at": expires_at.isoformat(),
            "client_ip": client_ip,
        }

        self._sessions[token] = session_data
        logger.info(f"User {user['username']} logged in successfully (role: {user['role']})")
        return session_data

    def validate_token(self, token: Optional[str]) -> Optional[Dict[str, Any]]:
        """Validates a session token and returns session data if valid and active."""
        if not token:
            return None

        # Clean bearer prefix if present
        clean_token = token.replace("Bearer ", "").strip()
        session = self._sessions.get(clean_token)
        if not session:
            return None

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        expires_at = datetime.datetime.fromisoformat(session["expires_at"])

        if now_utc > expires_at:
            del self._sessions[clean_token]
            return None

        return session

    def logout(self, token: str) -> bool:
        """Revokes an active session token."""
        clean_token = token.replace("Bearer ", "").strip()
        if clean_token in self._sessions:
            del self._sessions[clean_token]
            return True
        return False

    def require_role(self, session: Optional[Dict[str, Any]], required_role: str) -> Dict[str, Any]:
        """Enforces that an active session possesses at least required_role hierarchy."""
        if not session:
            raise AuthenticationError("Authentication required for this operation.")

        user_role = session.get("role", "VIEWER")
        user_level = ROLE_HIERARCHY.get(user_role, 0)
        req_level = ROLE_HIERARCHY.get(required_role, 99)

        if user_level < req_level:
            raise AuthorizationError(
                f"Forbidden: Operation requires '{required_role}' privileges (user possesses '{user_role}')."
            )

        return session

    def _prune_expired_sessions(self) -> None:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        expired = [
            t for t, s in self._sessions.items()
            if now_utc > datetime.datetime.fromisoformat(s["expires_at"])
        ]
        for t in expired:
            del self._sessions[t]


# Global singleton instance
auth_service = AuthService()

