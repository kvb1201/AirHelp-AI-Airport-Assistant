"""Lost / found baggage reports: SQLite persistence, similarity ranking, safe confirm."""

from __future__ import annotations

import os
import re
import secrets
import sqlite3
import uuid
from difflib import SequenceMatcher
from pathlib import Path
from time import time

from app.core.graph.airport_data import NODES


def db_path() -> Path:
    """SQLite file on this machine (the storage laptop). Override with LOST_FOUND_DB_PATH."""
    custom = (os.environ.get("LOST_FOUND_DB_PATH") or "").strip()
    if custom:
        return Path(custom).expanduser().resolve()
    return Path(__file__).resolve().parents[1] / "data" / "lost_found.sqlite3"


def get_db_path() -> str:
    return str(db_path())

MEET_GRAPH_NODE_ID = "t2_baggage_claim"
MEET_NODE_LABEL = "Baggage reclaim / arrivals interface — meet at the airline baggage desk nearby."


def _connect() -> sqlite3.Connection:
    p = db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as c:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS lf_reports (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                created_at REAL NOT NULL,
                flight TEXT,
                travel_date TEXT,
                bag_color TEXT,
                unique_detail TEXT NOT NULL,
                pir_reference TEXT,
                last_seen_node_id TEXT,
                claim_code TEXT,
                status TEXT NOT NULL DEFAULT 'open',
                matched_with_id TEXT
            )
            """
        )
        c.execute("CREATE INDEX IF NOT EXISTS lf_kind_status ON lf_reports(kind, status)")


def _gen_id() -> str:
    return str(uuid.uuid4())


def _gen_claim_code() -> str:
    return secrets.token_hex(4).upper()[:8]


def _norm(s: str | None) -> str:
    if not s:
        return ""
    return " ".join(s.lower().strip().split())


def _flight_key(s: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", _norm(s))


def validate_graph_node(node_id: str | None) -> str | None:
    if not node_id or not str(node_id).strip():
        return None
    nid = str(node_id).strip()
    if nid not in NODES:
        return f"Unknown graph node id: {nid}"
    return None


def create_lost(
    flight: str | None,
    travel_date: str | None,
    bag_color: str | None,
    unique_detail: str,
    pir_reference: str | None,
    last_seen_node_id: str | None,
) -> dict:
    init_db()
    rid = _gen_id()
    code = _gen_claim_code()
    with _connect() as c:
        c.execute(
            """
            INSERT INTO lf_reports (
                id, kind, created_at, flight, travel_date, bag_color, unique_detail,
                pir_reference, last_seen_node_id, claim_code, status
            ) VALUES (?, 'lost', ?, ?, ?, ?, ?, ?, ?, ?, 'open')
            """,
            (
                rid,
                time(),
                (flight or "").strip() or None,
                (travel_date or "").strip() or None,
                (bag_color or "").strip() or None,
                unique_detail.strip(),
                (pir_reference or "").strip() or None,
                (last_seen_node_id or "").strip() or None,
                code,
            ),
        )
    return {
        "id": rid,
        "kind": "lost",
        "claim_code": code,
        "message": "Share this code only with someone you believe has your bag, or with airline staff. Meet at the baggage desk after you both confirm.",
    }


def create_found(
    flight: str | None,
    travel_date: str | None,
    bag_color: str | None,
    unique_detail: str,
    pir_reference: str | None,
    last_seen_node_id: str | None,
    lost_report_id: str | None,
    claim_code: str | None,
) -> dict:
    init_db()
    rid = _gen_id()
    now = time()

    if lost_report_id and claim_code:
        row = _get_row(lost_report_id)
        if not row or row["kind"] != "lost":
            raise ValueError("lost_report_id does not refer to an open lost report")
        if row["status"] != "open":
            raise ValueError("That lost report is no longer open")
        cc = (claim_code or "").strip().upper().replace(" ", "")
        expected = (row["claim_code"] or "").upper()
        if len(cc) != len(expected) or not secrets.compare_digest(
            expected.encode("utf-8"),
            cc.encode("utf-8"),
        ):
            raise ValueError("Claim code does not match that lost report")

        with _connect() as c:
            c.execute(
                """
                INSERT INTO lf_reports (
                    id, kind, created_at, flight, travel_date, bag_color, unique_detail,
                    pir_reference, last_seen_node_id, claim_code, status, matched_with_id
                ) VALUES (?, 'found', ?, ?, ?, ?, ?, ?, ?, NULL, 'matched', ?)
                """,
                (
                    rid,
                    now,
                    (flight or "").strip() or None,
                    (travel_date or "").strip() or None,
                    (bag_color or "").strip() or None,
                    unique_detail.strip(),
                    (pir_reference or "").strip() or None,
                    (last_seen_node_id or "").strip() or None,
                    lost_report_id,
                ),
            )
            c.execute(
                "UPDATE lf_reports SET status = 'matched', matched_with_id = ? WHERE id = ?",
                (rid, lost_report_id),
            )

        return {
            "id": rid,
            "kind": "found",
            "status": "matched",
            "matched_lost_report_id": lost_report_id,
            "meet_graph_node_id": MEET_GRAPH_NODE_ID,
            "meet_label": MEET_NODE_LABEL,
            "message": "Matched using claim code. Meet at the baggage desk; staff can supervise handover.",
        }

    with _connect() as c:
        c.execute(
            """
            INSERT INTO lf_reports (
                id, kind, created_at, flight, travel_date, bag_color, unique_detail,
                pir_reference, last_seen_node_id, claim_code, status
            ) VALUES (?, 'found', ?, ?, ?, ?, ?, ?, ?, NULL, 'open')
            """,
            (
                rid,
                now,
                (flight or "").strip() or None,
                (travel_date or "").strip() or None,
                (bag_color or "").strip() or None,
                unique_detail.strip(),
                (pir_reference or "").strip() or None,
                (last_seen_node_id or "").strip() or None,
            ),
        )

    return {
        "id": rid,
        "kind": "found",
        "status": "open",
        "message": "Report saved. Use “possible matches” to compare with open lost reports, then confirm with the traveller’s claim code or matching PIR reference.",
    }


def _get_row(report_id: str) -> sqlite3.Row | None:
    init_db()
    with _connect() as c:
        cur = c.execute("SELECT * FROM lf_reports WHERE id = ?", (report_id,))
        return cur.fetchone()


def _row_to_public_lost(r: sqlite3.Row) -> dict:
    return {
        "id": r["id"],
        "kind": "lost",
        "flight": r["flight"],
        "travel_date": r["travel_date"],
        "bag_color": r["bag_color"],
        "unique_detail": r["unique_detail"],
        "last_seen_node_id": r["last_seen_node_id"],
        "has_pir": bool(r["pir_reference"]),
        "created_at": r["created_at"],
    }


def _row_to_public_found(r: sqlite3.Row) -> dict:
    return {
        "id": r["id"],
        "kind": "found",
        "flight": r["flight"],
        "travel_date": r["travel_date"],
        "bag_color": r["bag_color"],
        "unique_detail": r["unique_detail"],
        "last_seen_node_id": r["last_seen_node_id"],
        "has_pir": bool(r["pir_reference"]),
        "created_at": r["created_at"],
    }


def _score(lost: sqlite3.Row, found: sqlite3.Row) -> float:
    lf, ff = _flight_key(lost["flight"]), _flight_key(found["flight"])
    if lf and ff:
        flight_s = 1.0 if lf == ff else 0.0
    elif lf or ff:
        flight_s = 0.35
    else:
        flight_s = 0.5

    td_l, td_f = (lost["travel_date"] or "").strip(), (found["travel_date"] or "").strip()
    if td_l and td_f:
        date_s = 1.0 if td_l == td_f else 0.0
    elif td_l or td_f:
        date_s = 0.35
    else:
        date_s = 0.5

    bc_l, bc_f = _norm(lost["bag_color"]), _norm(found["bag_color"])
    if bc_l and bc_f:
        color_s = SequenceMatcher(None, bc_l, bc_f).ratio()
    elif bc_l or bc_f:
        color_s = 0.4
    else:
        color_s = 0.45

    ud_l, ud_f = _norm(lost["unique_detail"]), _norm(found["unique_detail"])
    detail_s = SequenceMatcher(None, ud_l, ud_f).ratio() if (ud_l and ud_f) else 0.0

    ln, fn = (lost["last_seen_node_id"] or "").strip(), (found["last_seen_node_id"] or "").strip()
    if ln and fn and ln == fn:
        node_s = 1.0
    elif not ln and not fn:
        node_s = 0.5
    else:
        node_s = 0.2

    score = 0.22 * flight_s + 0.2 * date_s + 0.18 * color_s + 0.35 * detail_s + 0.05 * node_s
    return round(score, 4)


def list_matches(report_id: str, limit: int = 8) -> dict:
    init_db()
    base = _get_row(report_id)
    if not base:
        raise ValueError("Report not found")

    want_kind = "found" if base["kind"] == "lost" else "lost"
    with _connect() as c:
        cur = c.execute(
            "SELECT * FROM lf_reports WHERE kind = ? AND status = 'open' AND id != ?",
            (want_kind, report_id),
        )
        candidates = cur.fetchall()

    scored: list[tuple[float, sqlite3.Row]] = []
    for other in candidates:
        if base["kind"] == "lost":
            s = _score(base, other)
        else:
            s = _score(other, base)
        if s >= 0.12:
            scored.append((s, other))

    scored.sort(key=lambda x: -x[0])
    out = []
    for s, r in scored[:limit]:
        pub = _row_to_public_found(r) if want_kind == "found" else _row_to_public_lost(r)
        pub["similarity"] = s
        out.append(pub)

    return {
        "report_id": report_id,
        "your_kind": base["kind"],
        "matches": out,
        "disclaimer": "Suggestions only. Always verify in person with airline baggage staff. Do not share phone numbers in-app.",
    }


def confirm_match(lost_report_id: str, found_report_id: str, shared_secret: str) -> dict:
    init_db()
    lost = _get_row(lost_report_id)
    found = _get_row(found_report_id)
    if not lost or not found:
        raise ValueError("One or both report ids are invalid")
    if lost["kind"] != "lost" or found["kind"] != "found":
        raise ValueError("confirm_match requires lost_report_id (lost) and found_report_id (found)")
    if lost["status"] != "open" or found["status"] != "open":
        raise ValueError("Both reports must still be open")

    secret = (shared_secret or "").strip()
    secret_upper = secret.upper().replace(" ", "")
    expected_cc = (lost["claim_code"] or "").upper()
    ok_claim = bool(expected_cc) and len(secret_upper) == len(expected_cc) and secrets.compare_digest(
        expected_cc.encode("utf-8"),
        secret_upper.encode("utf-8"),
    )
    pir_l = _norm(lost["pir_reference"])
    pir_f = _norm(found["pir_reference"])
    ok_pir = (
        len(pir_l) >= 4
        and len(pir_f) >= 4
        and pir_l == pir_f
    )

    if not (ok_claim or ok_pir):
        raise ValueError(
            "Shared secret did not match the lost report’s claim code or both parties’ PIR references",
        )

    with _connect() as c:
        c.execute(
            "UPDATE lf_reports SET status = 'matched', matched_with_id = ? WHERE id = ?",
            (found_report_id, lost_report_id),
        )
        c.execute(
            "UPDATE lf_reports SET status = 'matched', matched_with_id = ? WHERE id = ?",
            (lost_report_id, found_report_id),
        )

    return {
        "ok": True,
        "lost_report_id": lost_report_id,
        "found_report_id": found_report_id,
        "meet_graph_node_id": MEET_GRAPH_NODE_ID,
        "meet_label": MEET_NODE_LABEL,
        "message": "Match confirmed. Meet at the baggage / information area on the map. Prefer handing the bag to airline staff for verification.",
    }
