from fastapi import APIRouter, HTTPException, Query
from services.directory_service import lookup_directory, list_directory

router = APIRouter(prefix="/api/directory", tags=["Routing Directory"])

@router.get("/lookup")
def directory_lookup_endpoint(code: str = Query(...)):
    entry = lookup_directory(code)
    if not entry:
        raise HTTPException(status_code=404, detail="Institution routing code not found")
    return {"code": code.upper(), **entry}

@router.get("/list")
def directory_list_endpoint():
    return list_directory()
