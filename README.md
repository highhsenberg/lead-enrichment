# Inbound Lead Enrichment Engine

Automates inbound lead enrichment, CRM record creation, contact routing, and
qualification the moment a form is submitted -- instead of a rep manually
looking up the company, guessing who should own it, and deciding whether
it's worth a follow-up call.

See [`example_output.md`](./example_output.md) for a full run against the
included sample leads.

## Pipeline

1. **Enrich** -- look up firmographic data (industry, employee count) from
   the lead's email domain.
2. **CRM record** -- build a contact + company record ready to upsert into
   HubSpot/Salesforce/any CRM.
3. **Route** -- assign the lead to the right owner by company size
   (Enterprise / Mid-Market / SMB).
4. **Qualify** -- score the lead on a lite BANT rubric: budget mentioned,
   urgency mentioned, ICP employee-band fit, and a decision-maker title
   mentioned in the message.

Each stage is a separate function so any one of them can be swapped for a
real integration without touching the others -- `enrich_lead()` is where a
real Clearbit/Apollo/BuiltWith call would go.

## Install

No external dependencies beyond the Python standard library.

## Usage

```bash
python lead_enrichment.py --input sample_inbound_leads.json --threshold 50
```

## Project structure

```
lead_enrichment.py            -- enrich + CRM record + route + qualify pipeline
sample_inbound_leads.json      -- 4 example leads covering qualified / nurture cases
example_output.md              -- full example run with reasoning
```

## Limitations / next steps

- The domain lookup table is a stand-in for a real enrichment API --
  swapping in Clearbit/Apollo/BuiltWith is a drop-in change to
  `enrich_lead()`.
- Qualification is keyword-based, not a trained model; it works well as an
  explainable first pass and a natural place to add an LLM-based intent
  classifier later.
- Routing rules are a flat lookup by employee count; a production version
  would also account for territory, existing account ownership, and rep
  capacity.
