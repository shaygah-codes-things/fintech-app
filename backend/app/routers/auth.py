from fastapi import APIRouter, Request, Response, HTTPException, Response
from fastapi.responses import RedirectResponse
import os, secrets, base64, hashlib, httpx
from app.session import get_session, set_session
from app.db import SessionLocal
from app.models import User
from app.rate_limit import limiter, key_per_ip  # per-IP limits for auth endpoints

router = APIRouter(prefix="/auth", tags=["auth"])

AUTHZ = "https://github.com/login/oauth/authorize"
TOKEN = "https://github.com/login/oauth/access_token"
ME = "https://api.github.com/user"
EMAILS = "https://api.github.com/user/emails"

CID = os.getenv("OAUTH_CLIENT_ID", "")
CSEC = os.getenv("OAUTH_CLIENT_SECRET", "")
REDIR = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/auth/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


def _code_verifier():
    v = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode()
    d = hashlib.sha256(v.encode()).digest()
    chal = base64.urlsafe_b64encode(d).rstrip(b"=").decode()
    return v, chal


if os.getenv("ENV") == "test":

    @router.post("/test-login")
    @limiter.limit("60/minute", key_func=key_per_ip)
    def test_login(
        request: Request, response: Response, email: str = "test@example.com"
    ):
        with SessionLocal() as db:
            u = db.query(User).filter(User.email == email).one_or_none()
            if not u:
                u = User(
                    provider="github",
                    provider_user_id=f"test-{email}",
                    email=email,
                    name="Test User",
                )
                db.add(u)
                db.commit()
                db.refresh(u)
        set_session(response, {"uid": u.id, "email": u.email})
        return {"ok": True}


@router.get("/login")
@limiter.limit("10/minute", key_func=key_per_ip)  # conservative per-IP
def login(request: Request, response: Response):
    state = secrets.token_urlsafe(16)
    ver, chal = _code_verifier()
    sess = get_session(request) or {}
    sess.update({"oauth_state": state, "pkce_verifier": ver})
    resp = RedirectResponse(
        f"{AUTHZ}?client_id={CID}&redirect_uri={REDIR}"
        f"&state={state}&scope=read:user user:email"
        f"&code_challenge={chal}&code_challenge_method=S256"
    )
    set_session(resp, sess)
    return resp


@router.get("/callback")
@limiter.limit("10/minute", key_func=key_per_ip)  # conservative per-IP
async def callback(request: Request, response: Response, code: str, state: str):
    sess = get_session(request) or {}
    if state != sess.get("oauth_state"):
        raise HTTPException(400, "bad state")
    ver = sess.get("pkce_verifier") or ""

    async with httpx.AsyncClient(headers={"Accept": "application/json"}) as x:
        tk = (
            await x.post(
                TOKEN,
                data={
                    "client_id": CID,
                    "client_secret": CSEC,
                    "code": code,
                    "redirect_uri": REDIR,
                    "grant_type": "authorization_code",
                    "code_verifier": ver,
                },
            )
        ).json()
        access = tk.get("access_token")
        if not access:
            raise HTTPException(401, f"oauth failed: {tk}")

        auth_headers = {
            "Authorization": f"Bearer {access}",
            "Accept": "application/vnd.github+json",
        }
        me = (await x.get(ME, headers=auth_headers)).json()
        emails = (await x.get(EMAILS, headers=auth_headers)).json()
        email = next(
            (e["email"] for e in emails if e.get("primary")),
            (emails[0]["email"] if emails else None),
        )

    with SessionLocal() as db:
        u = (
            db.query(User)
            .filter(User.provider == "github", User.provider_user_id == str(me["id"]))
            .one_or_none()
        )
        if not u:
            u = User(
                provider="github",
                provider_user_id=str(me["id"]),
                email=email or me.get("email"),
                name=me.get("name"),
            )
            db.add(u)
        else:
            u.email = email or u.email
            u.name = me.get("name") or u.name
        db.commit()
        db.refresh(u)

    resp = RedirectResponse(url=FRONTEND_URL)
    set_session(resp, {"uid": u.id, "email": u.email})
    return resp


@router.get("/me")
@limiter.limit(
    "120/minute"
)  # per-user if session dep set on routes using it; /me can be hit often
def me(request: Request, response: Response):
    sess = get_session(request)
    if not sess:
        raise HTTPException(401, "not authenticated")
    return {"user_id": sess.get("uid"), "email": sess.get("email")}


@router.post("/logout")
@limiter.limit("60/minute")
def logout(request: Request, response: Response):
    response.delete_cookie("session", path="/")
    return {"ok": True}
