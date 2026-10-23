import os
import sys
from pathlib import Path

# Ensure the root directory containing 'application' is on sys.path
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from application.database import engine, Base
from application.config import settings

# Import models so Base registers them
import application.models

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Algorithmic solver clearinghouse and multi-stage settlement execution gateway.",
    version="2.4.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
from application.routers import (
    account,
    orders,
    quotes,
    settlements,
    receipts,
    ledger,
    reconciliation
)

app.include_router(account.router, prefix=settings.API_PREFIX)
app.include_router(orders.router, prefix=settings.API_PREFIX)
app.include_router(quotes.router, prefix=settings.API_PREFIX)
app.include_router(settlements.router, prefix=settings.API_PREFIX)
app.include_router(receipts.router, prefix=settings.API_PREFIX)
app.include_router(ledger.router, prefix=settings.API_PREFIX)
app.include_router(reconciliation.router, prefix=settings.API_PREFIX)

@app.get("/api/status")
def system_status():
    return {
        "status": "OPERATIONAL",
        "service": settings.APP_NAME,
        "engine_version": "v2.4.0",
        "statutory_compliance_tier": "STANDARD_SUPERVISORY",
        "settlement_window": "ACTIVE"
    }

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("application.main:app", host="0.0.0.0", port=8000, reload=True)
