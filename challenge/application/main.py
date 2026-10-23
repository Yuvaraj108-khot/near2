import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from config import APP_NAME, PROTOCOL_VERSION

from routers.channel import router as channel_router
from routers.pipeline import router as pipeline_router
from routers.receipts import router as receipts_router
from routers.ledger import router as ledger_router
from routers.reconciliation import router as reconciliation_router
from routers.instructions import router as instructions_router
from routers.directory import router as directory_router

app = FastAPI(
    title=APP_NAME,
    description="Institutional Clearing Gateway implementing the Concentric Saptaratha Settlement Architecture",
    version=PROTOCOL_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database schema
init_db()

# Register API Routers
app.include_router(channel_router)
app.include_router(pipeline_router)
app.include_router(receipts_router)
app.include_router(ledger_router)
app.include_router(reconciliation_router)
app.include_router(instructions_router)
app.include_router(directory_router)

# Static files & Web UI
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/api/health")
def health_check():
    return {
        "status": "OPERATIONAL",
        "protocol": PROTOCOL_VERSION,
        "engine": "Vyūha Clearing Engine v4.2"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
