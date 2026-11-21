from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, meetings, realtime, teams
from app.core.clock import clock
from app.core.config import settings
from app.db.session import SessionLocal
from app.services.resume import latest_persisted


@asynccontextmanager
async def lifespan(_: FastAPI):
    with SessionLocal() as db:
        clock.resume_after(latest_persisted(db))
    yield


app = FastAPI(
    title="altri API",
    version="0.1.0",
    description="Team Scorecard, Issues, To-Dos, Rocks and Level 10 Meetings. Auth: Bearer token from /api/auth/login.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"],
)
app.include_router(auth.router, prefix="/api")
app.include_router(teams.router, prefix="/api")
app.include_router(meetings.router, prefix="/api")
app.include_router(realtime.router, prefix="/api")


@app.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok"}
