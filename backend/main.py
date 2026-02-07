from fastapi import FastAPI
import uvicorn

from backend.core.config import settings
from backend.database.db import init_db
from backend.round1.routes import router as round1_router
from backend.round2.routes import router as round2_router
from backend.round2.websocket import router as ws_router


app = FastAPI(title="Multi-Round Interview Agent")
app.include_router(round1_router)
app.include_router(round2_router)
app.include_router(ws_router)

# Allow CORS for local development (Streamlit runs on different port)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
