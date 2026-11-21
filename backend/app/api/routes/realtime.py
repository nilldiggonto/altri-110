import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from fastapi.concurrency import run_in_threadpool

from app.api.deps import can_read_team, user_from_token
from app.core.clock import now
from app.db.session import SessionLocal
from app.realtime.hub import Subscriber, hub
from app.services import meetings

router = APIRouter()


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def _authorized(token: str | None, team_id: str) -> bool:
    with SessionLocal() as db:  # short session: never hold a pooled connection for the socket's life
        user = user_from_token(db, token)
        return bool(user and can_read_team(db, user, team_id))


def _hello(team_id: str) -> str:
    with SessionLocal() as db:
        mt = meetings.active_meeting(db, team_id)
        state = meetings.state(db, mt, now()).model_dump(mode="json") if mt else None
    return json.dumps({"type": "hello", "server_now": _iso(now()), "meeting": state})


async def _send(ws: WebSocket, sub: Subscriber) -> None:
    while True:
        get = asyncio.ensure_future(sub.queue.get())
        over = asyncio.ensure_future(sub.overflow.wait())
        done, pending = await asyncio.wait({get, over}, return_when=asyncio.FIRST_COMPLETED)
        for p in pending:
            p.cancel()
        if over in done:
            await ws.close(code=status.WS_1013_TRY_AGAIN_LATER)
            return
        await ws.send_text(get.result())


async def _receive(ws: WebSocket, sub: Subscriber) -> None:
    while True:
        try:
            msg = json.loads(await ws.receive_text())
        except ValueError:
            continue
        if isinstance(msg, dict) and msg.get("type") == "ping":
            sub.offer(json.dumps({"type": "pong", "server_now": _iso(now())}))


@router.websocket("/ws/teams/{team_id}")
async def team_socket(ws: WebSocket, team_id: str, token: str | None = None):
    """Team events. Same access rule as reading the team; rejected before the handshake completes.
    Reconnect at any time: the first message is always the full current state."""
    if not await run_in_threadpool(_authorized, token, team_id):
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await ws.accept()
    sub = hub.subscribe(team_id)  # before the snapshot, so nothing falls in between
    try:
        await ws.send_text(await run_in_threadpool(_hello, team_id))
        tasks = [asyncio.ensure_future(_send(ws, sub)), asyncio.ensure_future(_receive(ws, sub))]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for t in pending:
            t.cancel()
        for t in done:
            if t.exception() and not isinstance(t.exception(), WebSocketDisconnect):
                raise t.exception()
    except WebSocketDisconnect:
        pass
    finally:
        hub.unsubscribe(sub)
