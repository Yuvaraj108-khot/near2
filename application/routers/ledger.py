from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from services.channel_service import get_channel
from services.ledger_service import get_channel_journals, search_channel_journals

router = APIRouter(prefix="/api/ledger", tags=["Ledger"])

@router.get("/journal")
def get_journal_endpoint(channel_id: str = Query(...), db: Session = Depends(get_db)):
    channel = get_channel(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found in registry")
    return get_channel_journals(db, channel_id)

@router.get("/search")
def search_journal_endpoint(
    channel_id: str = Query(...),
    q: str = Query(...),
    db: Session = Depends(get_db)
):
    channel = get_channel(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found in registry")
    return search_channel_journals(db, channel_id, q)
