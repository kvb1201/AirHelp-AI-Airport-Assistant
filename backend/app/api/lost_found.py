"""Lost / found baggage MVP: intake, ranked matches, claim-code or PIR confirm, meet-at-desk node."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import lost_found_service as lf

router = APIRouter(prefix="/lost-found", tags=["Lost & Found"])


class ReportFields(BaseModel):
    flight: str | None = Field(None, max_length=32)
    travel_date: str | None = Field(None, max_length=32, description="ISO date or free text")
    bag_color: str | None = Field(None, max_length=120)
    unique_detail: str = Field(..., min_length=3, max_length=500)
    pir_reference: str | None = Field(None, max_length=80)
    last_seen_node_id: str | None = Field(None, max_length=120)


class LostCreateBody(ReportFields):
    pass


class FoundCreateBody(ReportFields):
    lost_report_id: str | None = None
    claim_code: str | None = Field(None, max_length=32)


class ConfirmBody(BaseModel):
    lost_report_id: str
    found_report_id: str
    shared_secret: str = Field(..., min_length=4, max_length=80)


@router.get("/meet-defaults")
def meet_defaults():
    """Default meet point on the walking graph (baggage reclaim / desk zone)."""
    return {
        "meet_graph_node_id": lf.MEET_GRAPH_NODE_ID,
        "meet_label": lf.MEET_NODE_LABEL,
    }


@router.post("/lost")
def create_lost(body: LostCreateBody):
    err = lf.validate_graph_node(body.last_seen_node_id)
    if err:
        raise HTTPException(400, err)
    try:
        return lf.create_lost(
            body.flight,
            body.travel_date,
            body.bag_color,
            body.unique_detail,
            body.pir_reference,
            body.last_seen_node_id,
        )
    except Exception as e:
        raise HTTPException(400, str(e)) from e


@router.post("/found")
def create_found(body: FoundCreateBody):
    err = lf.validate_graph_node(body.last_seen_node_id)
    if err:
        raise HTTPException(400, err)
    try:
        return lf.create_found(
            body.flight,
            body.travel_date,
            body.bag_color,
            body.unique_detail,
            body.pir_reference,
            body.last_seen_node_id,
            body.lost_report_id,
            body.claim_code,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.get("/matches/{report_id}")
def get_matches(report_id: str):
    try:
        return lf.list_matches(report_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.post("/confirm")
def confirm(body: ConfirmBody):
    try:
        return lf.confirm_match(body.lost_report_id, body.found_report_id, body.shared_secret)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
