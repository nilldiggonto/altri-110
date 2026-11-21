from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, teams
from app.core.config import settings

app = FastAPI(
    title="altri API",
    version="0.1.0",
    description="Team Scorecard, Issues, To-Dos, Rocks and Level 10 Meetings. Auth: Bearer token from /api/auth/login.",
)
app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"],
)
app.include_router(auth.router, prefix="/api")
app.include_router(teams.router, prefix="/api")


@app.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok"}
