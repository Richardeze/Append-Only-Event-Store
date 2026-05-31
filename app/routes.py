"""
routes.py — HTTP endpoints.
POST /events          → write a new event
GET  /events/:id      → read one event by ID (direct seek, no scan)
GET  /events          → list all events (for demo / debugging)
GET  /stats           → store statistics
"""
from fastapi import APIRouter, HTTPException
from app.models import EventPayload, Event, StatsResponse
from app.store import event_store

router = APIRouter()


@router.get("/")
def homepage():
    return {
        "message": "Append-Only Event Store is running",
        "status": "ok",
        "endpoints": {
            "write_event": "POST /events",
            "read_event": "GET /events/{id}",
            "list_events": "GET /events",
            "stats": "GET /stats",
            "docs": "GET /docs"
        }
    }


@router.post(
    "/events",
    response_model=Event,
    status_code=201,
    summary="Append a new event",
    description=(
        "Accepts any event type + payload. "
        "Assigns a UUID and UTC timestamp, appends to events.log, "
        "and records the byte offset in the in-memory index."
    ),
)
def create_event(body: EventPayload) -> Event:
    """
    1. Build a full Event (adds id + createdAt)
    2. Append it to the log
    3. Return the saved event (so the client knows its ID)
    """
    event = Event.from_payload(body)
    saved = event_store.append(event.model_dump())
    return saved


@router.get(
    "/events/{event_id}",
    response_model=Event,
    summary="Fetch one event by ID",
    description=(
        "Looks up the byte offset from the in-memory index, then seeks "
        "directly to that position in events.log — no file scan."
    ),
)
def get_event(event_id: str) -> Event:
    """
    Direct byte-seek read. O(1) regardless of how large the log grows.
    Returns 404 if the ID is not in the index.
    """
    event = event_store.get(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found.")
    return event


@router.get(
    "/events",
    response_model=list[Event],
    summary="List all events",
    description="Returns every event in insertion order. Useful for debugging.",
)
def list_events() -> list[Event]:
    return event_store.list_all()


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Store statistics",
)
def stats() -> StatsResponse:
    data = event_store.stats()
    return StatsResponse(total=data["total_events"], bytes=data["log_size_bytes"])