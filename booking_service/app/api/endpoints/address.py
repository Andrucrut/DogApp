from fastapi import APIRouter, Depends, Query

from app.schemas.address import AddressSuggestResponse, AddressSuggestion
from app.services.geocoder import suggest_address

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get("/suggest", response_model=AddressSuggestResponse)
async def suggest(
    country: str = Query(..., min_length=1),
    city: str = Query(..., min_length=1),
    q: str = Query(..., min_length=2),
    limit: int = Query(7, ge=1, le=15),
) -> AddressSuggestResponse:
    items = await suggest_address(country=country, city=city, query=q, limit=limit)
    return AddressSuggestResponse(items=[AddressSuggestion(**i) for i in items])

