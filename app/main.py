from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.store import event_store
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup: replay the log file to rebuild the in-memory index.
    This is the crash recovery step — if the server died, we come back up
    knowing exactly where every event lives in the file.
    """
    event_store.recover()
    yield


app = FastAPI(
    title="Append-Only Event Store",
    description="A crash-safe event store where events.log is the database.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)