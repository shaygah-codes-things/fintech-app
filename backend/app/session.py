import base64, hmac, hashlib, json, os
from fastapi import APIRouter, Request, Response, HTTPException

COOKIE_NAME = "session"
SESSION_SECRET = os.getenv("SESSION_SECRET", "devsecret").encode()

SECURE_COOKIES = os.getenv("SECURE_COOKIES", "false").lower() == "true"
SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")

router = APIRouter(prefix="/auth", tags=["auth"])


def _b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _b64ud(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode())


def get_session(req: Request) -> dict | None:
    raw = req.cookies.get(COOKIE_NAME)
    if not raw:
        return None
    try:
        data, sig = raw.rsplit(".", 1)
        expect = hmac.new(SESSION_SECRET, data.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expect):
            return None
        return json.loads(_b64ud(data))
    except Exception:
        return None


def set_session(resp: Response, payload: dict) -> None:
    data = _b64u(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(SESSION_SECRET, data.encode(), hashlib.sha256).hexdigest()
    resp.set_cookie(
        COOKIE_NAME,
        f"{data}.{sig}",
        httponly=True,
        secure=SECURE_COOKIES,
        samesite=SAMESITE,
        path="/",
    )


def current_user_id(req: Request) -> int:
    sess = get_session(req)
    if not sess or "uid" not in sess:
        raise HTTPException(401, detail="bad session")
    return int(sess["uid"])


def set_user_on_request(request: Request):
    """
    Dependency for protected routes: validates session and stashes user_id on request.state
    so rate-limiter can key per-user.
    """
    sess = get_session(request)
    if not sess or "uid" not in sess:
        raise HTTPException(401, detail="bad session")
    request.state.user_id = int(sess["uid"])
