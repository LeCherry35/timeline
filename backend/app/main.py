from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.settings import settings

api = APIRouter(prefix="/api")


@api.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app = FastAPI(title="Timeline")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api)
