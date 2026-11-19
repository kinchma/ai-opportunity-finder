# kb_sources: sourced best-practice notes (built 2026-11-16)

Purpose: real, citable sources for the shared knowledge base, written as short notes in the same
header format `kb/` uses (source, url, industries, then `---`, then paragraphs), plus `license:`,
`accessed:` and `note:` lines that the loader ignores. These notes are summaries in my own words
written from each source on the access date, not copies of the pages. Every file names its source
and URL so a retrieved passage can be cited. They live outside `kb/` on purpose: the app loads
everything in `kb/`, so move or copy a file into `kb/<industry>/` when you want it used, or point
`KB_DIR` at this folder.

| File | Source | License | Layer |
|---|---|---|---|
| general/sba-manage-finances.md | SBA Business Guide, Manage your finances | Public domain (US gov) | Core |
| general/sba-hire-and-manage-employees.md | SBA Business Guide, Hire and manage employees | Public domain | Core |
| general/sba-taxes-and-legal-compliance.md | SBA Business Guide, Pay taxes; Stay legally compliant | Public domain | Core |
| general/sba-assets-and-equipment.md | SBA Business Guide, Buy assets and equipment | Public domain | Core |
| general/sba-marketing-sales-and-payments.md | SBA Business Guide, Marketing and sales | Public domain | Core |
| general/sba-ai-for-small-business.md | SBA Business Guide, AI (labelled "SI") for small business | Public domain | AI use and risk |
| general/sba-cybersecurity-and-fraud.md | SBA Business Guide, Cybersecurity; Fraud | Public domain | Core / AI risk |
| general/sba-prepare-for-emergencies.md | SBA Business Guide, Prepare for emergencies | Public domain | Core |
| general/irs-pub583-recordkeeping.md | IRS Publication 583 (Rev. Dec 2024) | Public domain | Core (bookkeeping, records) |
| general/nist-ai-rmf.md | NIST AI RMF 1.0 (NIST AI 100-1) and NIST AI 600-1 | Public domain | AI use and risk |
| manufacturing/nist-mep-lean-methods.md | NIST MEP, Lean and process improvement | Public domain | Manufacturing overlay |
| manufacturing/nist-mep-value-stream-mapping.md | NIST MEP, Value Stream Mapping | Public domain | Manufacturing overlay |
| trailer-manufacturing/nhtsa-manufacturer-requirements.md | NHTSA New Manufacturers Handbook (rev. 10/24/2025) | Public domain | Trailer overlay |

License notes (checked 2026-11-16)
- SBA: "Government information on SBA.gov is in the public domain" and may be freely copied; credit SBA. Third-party items on SBA pages may be copyrighted. (https://www.sba.gov/about-sba/open-government/about-the-sba-gov-website/)
- NIST, IRS, NHTSA: works of the US government, public domain (17 U.S.C. 105). Credit the agency.
- OpenStax Entrepreneurship: NOT included. The 2020 PDF edition is CC BY 4.0, but the current openstax.org edition (2026) shows CC BY-NC-SA with "Commercial use requires permission". Because this project may become a commercial consulting service, use only the 2020 CC BY edition with the required attribution ("Access for free at openstax.org"), or leave it out. Same caution for OpenStax Introduction to Business 2e (CC BY-NC-SA).
- SCORE (score.org) templates: copyrighted; link to them, do not copy.
- NATM and TTMA (trailer trade associations): member material, not checked; link only.

Gaps still open
- No sourced overlay yet for retail/hardware stores, wholesale distribution or marketing agencies (the existing kb/ placeholder notes cover distribution and professional services). Candidate public-domain sources: SBA industry pages, Census/BLS industry statistics, state MEP and SBDC guides.
- No per-process "what AI can and cannot do reliably" layer beyond the SBA and NIST notes; that layer is my own synthesis and should be labelled as such.
- The SBA site was reorganised in late 2026 (business-guide pages now live under /counseling/manage-your-business/ with anchors); re-check URLs before the final report.
