# Sample Recommendation: Quality Inspection Roadmap for a Small Trailer Manufacturer

Status: DRAFT sample for the capstone (synthetic demo customer, not a real company). Written 2026-11-14 from web research plus my own judgment. Ratings are illustrative placeholders, not measured. Verify regulatory points with NHTSA (and a qualified person) before using them as advice; this is not legal or compliance advice. This file is NOT in kb/ on purpose (kb files are loaded by the app).

Use in the project: (1) example of the kind of roadmap the Strategist should produce; (2) candidate "expected best picks" for a synthetic trailer-manufacturer test customer; (3) source material for the trailer overlay in the knowledge base (see PROJECT_NOTES.md Part 7).

## Why quality inspection fits a small trailer manufacturer
- Trailers must meet federal safety standards (FMVSS) for items such as lighting, tires, braking systems, brake hoses and brake fluids; manufacturers also have informational requirements (NHTSA).
- Each trailer needs a permanently affixed certification label (manufacturer, date of manufacture, FMVSS compliance statement, GVWR and GAWR per axle) and a VIN (NHTSA). Manufacturers self-certify, so the manufacturer is responsible for conformity. Record-retention rules also apply (49 CFR 576 appears in NHTSA's list; confirm details).
- That makes inspection records, traceability and consistency valuable and easy to justify.
- Typical small-shop starting point (industry articles): paper check sheets, non-conformance reports in a folder, customer returns in email, rework notes on job travelers. Logging nonconformances, tracking scrap, analyzing inspection results and managing corrective actions are structured, repeatable tasks that AI handles well (Quality Magazine; IMEC). Every state has an MEP center that can help.

## Roadmap (start low-risk, add AI where it earns its place)
Phase 0: Baseline (1-2 weeks, no AI)
- Map current inspection points: incoming materials, frame and welds, axles/brakes/tires, electrical and lighting, paint/coatings, labels and VIN, final inspection and shipping.
- List what records exist and where; agree a simple defect taxonomy (weld defect, wrong part, missing component, finish defect, label/documentation error).
- Interview the owner and lead inspector; this baseline is the Process Mapper's job and must come from the company, not from best practices.

Phase 1: Digital inspection checklists with photos (low AI, high value, low risk)
- One checklist per station plus a final inspection checklist tied to certification label items (GVWR/GAWR, VIN, label present and legible) and the FMVSS-related items the shop already checks.
- Required fields, photo capture on key items, inspector name and timestamp on every record.
- AI can draft checklists from drawings and specs; a human reviews.

Phase 2: One defect log and simple dashboard (low AI, high value, low risk)
- Replace scattered sheets with a single non-conformance and rework log; add customer returns and warranty claims.
- Pareto counts by station, defect type, model and week, calculated by code.
- A local language model classifies and summarizes free-text notes; code does the counts; a person confirms categories.

Phase 3: AI-assisted checks on specific items (medium effort and risk)
- A local vision model reviews photos for simple, well-defined items (label present, conspicuity tape/reflectors, lights mounted, tire/rim data plate readable) and flags doubtful ones for the inspector.
- Measure first: compare the model to the inspector on the same photos.

Phase 4: Computer vision for weld and paint defects at one station (higher effort, cost, risk)
- Pilot at one station with fixed cameras and lighting; collect and label images first.
- Structural welds are safety-critical: AI screens and flags, a qualified human decides and signs off. AI never certifies compliance.
- Vendor claims of 97-99% accuracy come from marketing pages; treat as unverified and test on the shop's own parts.

Phase 5: Link defects to causes (only with enough data)
- Connect defect patterns to process changes, supplier lots, operators, equipment and warranty claims.

## Illustrative scoring (placeholders for the Matcher; 1-10)
| Phase | Value | Effort | Risk | Note |
|---|---|---|---|---|
| 1 Digital checklists with photos | 7 | 3 | 2 | Fast win; creates the data everything else needs |
| 2 Defect log and dashboard | 7 | 4 | 2 | Local model classifies notes; code counts |
| 3 AI photo checks on simple items | 5 | 5 | 4 | Human confirms; measure first |
| 4 Weld/paint vision at one station | 8 | 8 | 6 | Needs data, hardware, validation; safety-critical |
| 5 Defects linked to causes | 6 | 6 | 3 | Needs months of clean data |
Suggested order: 1, 2, 3, 4, with 5 later.

## Guardrails and human intervention (ties to Checkpoint 6.1)
- AI assists and flags; a human inspector decides pass/fail; a responsible person signs off compliance and certification.
- Keep customer and production data local; no cloud vision services for the customer's photos by default.
- Escalate to the owner when evidence is thin or a safety-critical item is uncertain; log every AI flag and human decision.
- Say what is estimated versus known; do not promise accuracy or savings.

## Questions for the SME interview
- Which inspection points exist today, who does them, what is written down?
- Where are defects and returns recorded, and how long to find a past record?
- Top three recurring defects; cost of rework and warranty claims?
- What runs production (ERP, spreadsheets, paper); what equipment and cameras are on site?
- Who certifies and signs off each trailer?

## Sources (searched 2026-11-14)
- NHTSA trailer manufacturer requirements (FMVSS list, certification label, GVWR/GAWR, VIN, self-certification), nhtsa.gov.
- Quality Magazine, "AI in the Quality Department: A Practical Path Forward for Small Manufacturers" (qualitymag.com); IMEC, "AI-Powered Quality Control" (imec.org).
- Vendor pages on AI weld inspection (Oxmaint, iFactory, Overview.ai) and an industry blog (advalorem.substack.com): marketing, unverified; ideas only.
- For the knowledge base: save my own short summaries with links and dates, not copies.
