import os
import json
from fastapi import APIRouter

router = APIRouter(prefix="/api/instructions", tags=["Settlement Instructions"])

MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "treasury_manifest.json")

@router.get("/manifest")
def get_treasury_manifest_endpoint():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data
