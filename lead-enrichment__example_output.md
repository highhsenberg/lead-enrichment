# Example run

```
$ python lead_enrichment.py --input sample_inbound_leads.json --threshold 50

=== Jordan Blake <jordan@northwinddata.com> ===
CRM record: {
  "contact": {
    "name": "Jordan Blake",
    "email": "jordan@northwinddata.com",
    "lifecycle_stage": "lead"
  },
  "company": {
    "name": "Northwind Data",
    "industry": "Data Infrastructure",
    "employee_count": 85
  },
  "source": "inbound_form"
}
Routed to: Mid-Market AE - Sam
Score: 100 -> SQL
  - Budget/approval mentioned in message
  - Timing/urgency mentioned in message
  - Employee count 85 within target band 10-250
  - Decision-maker title mentioned in message

=== Priya Shah <priya@ledgerline.io> ===
CRM record: {
  "contact": {
    "name": "Priya Shah",
    "email": "priya@ledgerline.io",
    "lifecycle_stage": "lead"
  },
  "company": {
    "name": "Ledgerline",
    "industry": "Fintech",
    "employee_count": 340
  },
  "source": "inbound_form"
}
Routed to: Enterprise AE - Dana
Score: 0 -> Nurture

=== Alex Kim <alex@fieldworksai.com> ===
CRM record: {
  "contact": {
    "name": "Alex Kim",
    "email": "alex@fieldworksai.com",
    "lifecycle_stage": "lead"
  },
  "company": {
    "name": "Fieldworks AI",
    "industry": "Vertical SaaS",
    "employee_count": 40
  },
  "source": "inbound_form"
}
Routed to: Mid-Market AE - Sam
Score: 80 -> SQL
  - Budget/approval mentioned in message
  - Employee count 40 within target band 10-250
  - Decision-maker title mentioned in message

=== Taylor Reed <taylor@barrowfinch.com> ===
CRM record: {
  "contact": {
    "name": "Taylor Reed",
    "email": "taylor@barrowfinch.com",
    "lifecycle_stage": "lead"
  },
  "company": {
    "name": "Barrow & Finch",
    "industry": "Professional Services",
    "employee_count": 22
  },
  "source": "inbound_form"
}
Routed to: Mid-Market AE - Sam
Score: 25 -> Nurture
  - Employee count 22 within target band 10-250
```

## Why this shape

Enrichment, CRM record creation, routing, and qualification are four
separate functions on purpose. Each is a seam: `enrich_lead()` is where a
real Clearbit/Apollo/BuiltWith call would go, `create_crm_record()` is
where a real HubSpot/Salesforce upsert would go, and `route_lead()` /
`qualify_lead()` encode rules a sales team can read and adjust without
touching the enrichment or CRM logic.

Notice Priya Shah (a large, well-funded account) still gets routed to the
right owner even though she isn't sales-qualified yet -- routing and
qualification are independent decisions, which matters once a nurtured
lead becomes ready to buy later.
