#!/usr/bin/env python3
"""
Inbound Lead Enrichment Engine
--------------------------------
Automates what happens the moment an inbound lead fills out a form:

1. Enrich  -- look up firmographic data (industry, employee count) from the
   lead's email domain.
2. Record  -- build a CRM-style contact + company record ready to upsert.
3. Route   -- assign the lead to the right owner based on company size.
4. Qualify -- score the lead on a lite BANT rubric (Budget mentioned,
   Authority/title, timing/urgency, and ICP employee-band fit).

Everything runs on a local JSON file of sample leads and a static domain
lookup table, so the pipeline is fully runnable without any external API
keys. `enrich_lead()` is the seam you'd swap for a real enrichment API
(Clearbit, Apollo, BuiltWith, etc.) in production.

Usage:
    python lead_enrichment.py --input sample_inbound_leads.json --threshold 50
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List


# --------------------------------------------------------------------------
# Static "enrichment API" -- keyed by email domain.
# --------------------------------------------------------------------------

DOMAIN_INFO = {
    "northwinddata.com": {"company": "Northwind Data", "industry": "Data Infrastructure", "employee_count": 85},
    "ledgerline.io": {"company": "Ledgerline", "industry": "Fintech", "employee_count": 340},
    "fieldworksai.com": {"company": "Fieldworks AI", "industry": "Vertical SaaS", "employee_count": 40},
    "barrowfinch.com": {"company": "Barrow & Finch", "industry": "Professional Services", "employee_count": 22},
}

BUDGET_WORDS = ("budget", "approved", "sign off", "signed off")
URGENCY_WORDS = ("this week", "this quarter", "asap", "urgently", "right away")
AUTHORITY_TITLES = ("vp", "director", "head of", "chief", "cto", "ceo", "cfo")

SCORE_WEIGHTS = {
    "budget_mentioned": 30,
    "urgency_mentioned": 20,
    "employee_band_fit": 25,
    "authority_mentioned": 25,
}

TARGET_EMPLOYEE_BAND = (10, 250)


@dataclass
class EnrichedLead:
    name: str
    email: str
    message: str
    company: str
    industry: str
    employee_count: int
    score: int
    reasons: List[str] = field(default_factory=list)
    owner: str = ""
    qualified: bool = False


# --------------------------------------------------------------------------
# 1. Load
# --------------------------------------------------------------------------

def load_leads(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------------------------
# 2. Enrich
# --------------------------------------------------------------------------

def enrich_lead(lead: Dict[str, Any]) -> Dict[str, Any]:
    domain = lead["email"].split("@")[-1].lower()
    info = DOMAIN_INFO.get(domain, {"company": lead.get("company", "Unknown"), "industry": "Unknown", "employee_count": 0})
    enriched = dict(lead)
    enriched.update(info)
    return enriched


# --------------------------------------------------------------------------
# 3. CRM record
# --------------------------------------------------------------------------

def create_crm_record(enriched: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "contact": {
            "name": enriched["name"],
            "email": enriched["email"],
            "lifecycle_stage": "lead",
        },
        "company": {
            "name": enriched["company"],
            "industry": enriched["industry"],
            "employee_count": enriched["employee_count"],
        },
        "source": "inbound_form",
    }


# --------------------------------------------------------------------------
# 4. Route
# --------------------------------------------------------------------------

def route_lead(enriched: Dict[str, Any]) -> str:
    employees = enriched["employee_count"]
    if employees > 250:
        return "Enterprise AE - Dana"
    if employees >= 10:
        return "Mid-Market AE - Sam"
    return "SMB AE - Casey"


# --------------------------------------------------------------------------
# 5. Qualify
# --------------------------------------------------------------------------

def qualify_lead(enriched: Dict[str, Any]) -> tuple[int, List[str]]:
    score = 0
    reasons: List[str] = []
    message = enriched.get("message", "").lower()

    if any(w in message for w in BUDGET_WORDS):
        score += SCORE_WEIGHTS["budget_mentioned"]
        reasons.append("Budget/approval mentioned in message")

    if any(w in message for w in URGENCY_WORDS):
        score += SCORE_WEIGHTS["urgency_mentioned"]
        reasons.append("Timing/urgency mentioned in message")

    lo, hi = TARGET_EMPLOYEE_BAND
    employees = enriched["employee_count"]
    if lo <= employees <= hi:
        score += SCORE_WEIGHTS["employee_band_fit"]
        reasons.append(f"Employee count {employees} within target band {lo}-{hi}")

    if any(t in message for t in AUTHORITY_TITLES):
        score += SCORE_WEIGHTS["authority_mentioned"]
        reasons.append("Decision-maker title mentioned in message")

    return score, reasons


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def process_lead(lead: Dict[str, Any], threshold: int) -> EnrichedLead:
    enriched = enrich_lead(lead)
    score, reasons = qualify_lead(enriched)
    owner = route_lead(enriched)
    return EnrichedLead(
        name=enriched["name"],
        email=enriched["email"],
        message=enriched["message"],
        company=enriched["company"],
        industry=enriched["industry"],
        employee_count=enriched["employee_count"],
        score=score,
        reasons=reasons,
        owner=owner,
        qualified=score >= threshold,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Inbound Lead Enrichment Engine")
    parser.add_argument("--input", default="sample_inbound_leads.json")
    parser.add_argument("--threshold", type=int, default=50, help="Minimum score to mark a lead sales-qualified")
    args = parser.parse_args()

    leads = load_leads(args.input)

    for lead in leads:
        enriched = enrich_lead(lead)
        record = create_crm_record(enriched)
        result = process_lead(lead, args.threshold)

        status = "SQL" if result.qualified else "Nurture"
        print(f"\n=== {result.name} <{result.email}> ===")
        print(f"CRM record: {json.dumps(record, indent=2)}")
        print(f"Routed to: {result.owner}")
        print(f"Score: {result.score} -> {status}")
        for reason in result.reasons:
            print(f"  - {reason}")


if __name__ == "__main__":
    main()
