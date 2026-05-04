import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.support_ticket_service import create_ticket, list_categories

router = APIRouter()


class SupportTicketCreate(BaseModel):
    category: str = Field(..., min_length=1, max_length=64)
    description: str = Field(..., min_length=10, max_length=4000)
    where_hint: str | None = Field(None, max_length=500)
    email: str | None = Field(None, max_length=320)
    location_graph_id: str | None = Field(None, max_length=120)


class SupportTicketOut(BaseModel):
    ticket_id: str
    created_at: str
    category: str
    category_label: str
    summary: str
    email_sent: bool = False
    email_notice: str | None = None


class SupportCategoriesOut(BaseModel):
    categories: list[dict[str, str]]


@router.get("/support/ticket-categories", response_model=SupportCategoriesOut)
async def ticket_categories():
    return SupportCategoriesOut(categories=list_categories())


@router.post("/support/tickets", response_model=SupportTicketOut)
async def post_support_ticket(body: SupportTicketCreate):
    try:
        out = await asyncio.to_thread(
            create_ticket,
            category=body.category,
            description=body.description,
            where_hint=body.where_hint,
            email=body.email,
            location_graph_id=body.location_graph_id,
        )
        return SupportTicketOut(**out)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
