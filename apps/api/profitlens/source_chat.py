"""Authorized, deterministic source observations for conversational explanations."""

import calendar
from datetime import date
from urllib.parse import urlencode

from sqlalchemy import func, select

from . import database as db
from .records import wire
from .security import visible

NOTICE = (
    "Source observations are not verified net revenue, cash collected or profit. "
    "Costs, tax treatment, contract compliance and completeness are unknown unless separately verified. "
    "Sales and expenditure from different sources must not be subtracted to invent profit."
)


def enrich(conn, s, pack, all_periods=False, intent="overview"):
    table = db.financial_facts
    scope = visible(table, s)
    if pack["customer_id"]:
        scope &= table.c.customer_id == pack["customer_id"]
    if not conn.scalar(select(table.c.id).where(scope).limit(1)):
        return pack
    predicate = scope
    params = {}
    if pack["customer_id"]:
        params["customer_id"] = pack["customer_id"]
    period = pack["billing_period"]
    if period and not all_periods:
        first = date.fromisoformat(period + "-01")
        last = first.replace(day=calendar.monthrange(first.year, first.month)[1])
        predicate &= table.c.occurred_on.between(first, last)
        params.update(start=first.isoformat(), end=last.isoformat())
    groups = list(
        conn.execute(
            select(
                table.c.kind,
                table.c.currency,
                func.sum(table.c.amount).label("amount"),
                func.count().label("count"),
            )
            .where(predicate)
            .group_by(table.c.kind, table.c.currency)
            .order_by(table.c.kind, table.c.currency)
        ).mappings()
    )
    # Never turn the legacy empty ledger's zero counters into source-data findings.
    if not pack["invoice_lines"] and not pack["expense_lines"]:
        pack.update(metrics={}, cards=[], actions=[], findings=[], warnings=[])
        pack["profitability_status"] = "source_observations_only"
        if all_periods:
            pack["billing_period"] = None
            pack["facts"].pop("selected_period", None)
    pack["source_context"] = {
        "scope": "all imported dates including unknown dates"
        if all_periods
        else period,
        "limitations": NOTICE,
        "groups": [],
        "row_sample": "Up to three largest absolute amounts; not the whole dataset or proven anomalies.",
    }
    pack["facts"]["source_period"] = (
        "all imported dates" if all_periods else (period or "all imported dates")
    )
    pack["scope_label"] = "Source observations · " + pack["facts"]["source_period"]
    pack["source_citations"] = []
    pack["metric_sources"] = {}
    base = f"/api/workspaces/{s.org}/facts"
    for index, row in enumerate(groups):
        prefix = "source_" + chr(97 + index)
        metric = prefix + "_amount"
        count = prefix + "_count"
        pack["metrics"][count] = {"value": str(row["count"]), "unit": "records"}
        if not row["kind"].endswith("_balance"):
            pack["metrics"][metric] = {
                "value": str(row["amount"]),
                "unit": row["currency"],
            }
        source_id = "source-group:" + prefix
        pack["metric_sources"][count] = source_id
        pack["metric_sources"][metric] = source_id
        pack["source_context"]["groups"].append(
            {
                "kind": row["kind"],
                "count_metric": count,
                "amount_metric": metric if metric in pack["metrics"] else None,
                "source_id": source_id,
            }
        )
        pack["source_citations"].append(
            {
                "source_id": source_id,
                "filename": row["kind"].replace("_", " ")
                + " · authorized source records",
                "page": None,
                "source_url": base + "?" + urlencode(params | {"kind": row["kind"]}),
                "content": f"{row['count']} records in this scope. " + NOTICE,
                "evidence_status": "source_observation",
            }
        )
        pack["cards"].append(
            {
                "label": row["kind"].replace("_", " "),
                "value": str(row["amount"]) + " " + row["currency"]
                if metric in pack["metrics"]
                else "Non-additive snapshots",
                "tone": "neutral",
            }
        )
    rows = list(
        conn.execute(
            select(table)
            .where(predicate)
            .order_by(func.abs(table.c.amount).desc(), table.c.id)
            .limit(3)
        ).mappings()
    )
    for index, row in enumerate(rows):
        prefix = "source_row_" + chr(97 + index)
        metric = prefix + "_amount"
        pack["metrics"][metric] = {"value": str(row["amount"]), "unit": row["currency"]}
        source_id = "source-row:" + row["id"]
        pack["metric_sources"][metric] = source_id
        pack["facts"][prefix + "_description"] = (
            row["description"][:200] or "Unspecified description"
        )
        pack["facts"][prefix + "_counterparty"] = (
            row["counterparty"][:120] or "Unknown counterparty"
        )
        pack["source_citations"].append(
            {
                "source_id": source_id,
                "filename": "Source row " + str(row["row_number"]),
                "page": None,
                "source_url": base + "/" + row["id"],
                "content": f"{row['kind']}: {row['amount']} {row['currency']}; {row['description'][:200]}",
                "evidence_status": "source_observation",
                "metric_id": metric,
                "description_fact": prefix + "_description",
                "counterparty_fact": prefix + "_counterparty",
            }
        )
    # Include row contents and aggregates in the snapshot checked again after model latency.
    pack["source_context"]["sample"] = [dict(r) for r in rows]
    pack["actions"].insert(
        0,
        dict(
            view="data",
            label="Explore source data & insights",
            customer_id=pack["customer_id"],
            billing_period=None if all_periods else period,
            record_id=None,
        ),
    )
    return wire(pack)
