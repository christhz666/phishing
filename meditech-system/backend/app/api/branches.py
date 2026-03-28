# Placeholder para módulos API
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def placeholder():
    return {"status": "endpoint_en_desarrollo"}
