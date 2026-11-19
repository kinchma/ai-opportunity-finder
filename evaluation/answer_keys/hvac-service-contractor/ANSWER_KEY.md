# Answer Key - Larkmoor Comfort Heating & Air (hvac-service-contractor)

Evaluator-only. Never copy into cases/hvac-service-contractor/. Snapshot 2026-10-31.

## Rates used in the estimates

- Office staff loaded cost: $32 per hour. Owners and managers: $50 per hour. Field tech or installer loaded labor: $45 per hour.
- ACCA truck cost reference (research note 3): about $84 per hour, used only as an upper bound.
- Hours are rounded. Estimates are the evaluator's, not the company's.

## Planted issues

### I01 Paper service tickets re-keyed into QuickBooks (AI / automation)
Evidence: documents/processes/03_service_ticket_to_invoice.md (The paper ticket, Volumes and timing, When things go wrong); interviews/03_service_ticket_to_invoice_interview.md ([06:30], [12:00], [13:30]); data/service_calls_sample.csv.
Shows: every ticket typed by Dana, about 4 minutes each; 25 to 35 tickets a month late or missing at first; commercial invoices about 8 days after the job; new customers typed twice.
Estimate: (5,200 + 290) tickets x 4 min = 366 hours x $32 = about $11,700 a year, plus faster commercial cash and a few unbilled tickets a year.
Fix: capture the ticket digitally (photo or mobile form) and extract to a QuickBooks-ready draft; Dana reviews instead of typing.

### I02 Dispatch on a whiteboard plus a spreadsheet, status calls answered by walking to the board (AI / automation)
Evidence: documents/processes/02_scheduling_and_dispatch.md (Daily steps, Volumes); interviews/02_scheduling_and_dispatch_interview.md ([02:30], [06:00], [09:30]); interviews/01_service_call_intake_interview.md ([00:00]).
Shows: board and spreadsheet both kept, 15 to 20 minutes a day reconciling; 60 to 80 tech call-ins a day; 30 to 40 "when is the tech coming" calls a day in summer and winter.
Estimate: reconciliation 20 min x 250 days = 83 hours; status calls 35 x 3 min x about 150 peak days = 263 hours; total about 346 hours x $32 = about $11,000.
Fix: one schedule with tech status from the field; automated "on the way" texts; status lookups answered from the schedule.

### I03 Commercial PM renewals tracked by memory (AI / automation) - conflict C1
Evidence: documents/processes/04_maintenance_agreements.md (Renewal procedure); interviews/04_maintenance_agreements_interview.md ([03:00], [07:00]); data/commercial_agreements.csv; interviews/02_scheduling_and_dispatch_interview.md ([11:00]).
Shows: 11 of 90 agreements passed their end date before renewal; 7 renewed late with missed visits, 4 lost (2,800 + 4,200 + 6,900 + 4,100 = $18,000 a year).
Estimate: $18,000 a year of agreement revenue lost, plus missed visit billing and repair work the visits would have found. 11 of 90 lapsing is an 88% on-time rate versus an 86%+ target; the loss is the 4 lost agreements.
Fix: renewal reminders generated from the agreement end dates (90/60/30 days) with a drafted renewal email for Wes.

### I04 After-hours answering-service messages retyped every morning (AI / automation)
Evidence: documents/processes/01_service_call_intake.md (Steps for after-hours messages); interviews/01_service_call_intake_interview.md ([07:00]).
Shows: about 1,050 messages a year emailed to service@, printed, checked and typed into the dispatch spreadsheet; 20 minutes normal mornings, 45+ on winter Mondays.
Estimate: 1,050 x 6 min = 105 hours x $32 = about $3,400, plus later callbacks on busy mornings.
Fix: parse Midstate emails into draft dispatch rows, flag ones the on-call tech already handled.

### I05 Website requests answered in about 1.5 business days (AI / automation)
Evidence: documents/processes/01_service_call_intake.md (Steps for web form requests); interviews/01_service_call_intake_interview.md ([11:00]); data/service_calls_sample.csv (SC-2026-4418, SC-2026-4201).
Shows: 410 requests a year to a shared inbox checked "when the phones are quiet"; average 1.5 business days, 2 to 3 in peak; customers say they already had someone out.
Estimate (assumption): if 10% are lost to slow response, 41 jobs x $410 average repair = about $16,800 of revenue a year.
Fix: instant acknowledgment and self-booking or a call-back queue; triage of the shared inbox.

### I06 Comfort Club tune-ups booked by outbound phone calls (AI / automation)
Evidence: documents/processes/04_maintenance_agreements.md (Comfort Club); interviews/09_marketing_and_reviews_interview.md ([10:30]); data/comfort_club_booking_log.csv; data/monthly_volume_log.csv.
Shows: 640 members, 1,280 tune-ups owed, 2,580 calls at about 4 minutes, 236 tune-ups never booked.
Estimate: 2,580 x 4 min = 172 hours x $32 = about $5,500; plus 236 paid-for visits not delivered (236 x $94.50 half of the $189 plan = about $22,300 of service owed) and churn risk.
Fix: text or email invitations with self-scheduling; calls only for non-responders.

### I07 Paper timesheets added up and typed into ADP RUN (AI / automation)
Evidence: documents/processes/08_payroll_and_timesheets.md; interviews/08_payroll_and_timesheets_interview.md ([05:30], [09:00]); data/timesheets_pay_period.csv.
Shows: 24 field sheets per payroll, 3 or 4 missing, about 6 corrections, 5 hours per payroll, 26 payrolls.
Estimate: 26 x 5 = 130 hours x $50 = $6,500 a year.
Fix: mobile time capture with daily totals and overtime checks that export to ADP RUN.

### I08 Van stock not tracked, about 2 parts runs per tech per week (automation)
Evidence: documents/processes/06_purchasing_and_inventory.md (Van stock); interviews/06_purchasing_and_inventory_interview.md ([12:30]); interviews/02_scheduling_and_dispatch_interview.md (wrap-up).
Shows: restock depends on a clipboard; nobody knows what is on a van; 14 techs x 2 trips a week, 45 minutes to an hour each.
Estimate: 14 x 2 x 50 weeks = 1,400 trips x 0.75 hour = 1,050 hours x $45 = about $47,000 of paid tech time (higher at the $84 truck rate, and some lost billable calls).
Fix: van stock replenishment from parts used on tickets (ties to I01); min/max per van.

### I09 Main supplier never re-quoted; written offer 7.5% lower on file (NOT AI) - largest dollar item
Evidence: documents/processes/06_purchasing_and_inventory.md (Suppliers); interviews/06_purchasing_and_inventory_interview.md ([02:30]); data/supplier_quotes.csv; documents/company/01_company_profile.md.
Shows: Northgate since 1994, no equipment quotes compared; Ridgeview quote RQ-2026-03 for the same Aerovance models at 7.5% less, valid to 2026-12-31, on Kyle's desk since March.
Estimate: $1.2 million x 7.5% = $90,000 a year (upper bound; less if Northgate matches).
Better fix: management decision. Ask Northgate to match or split purchasing. No AI needed.

### I10 Housecall Pro paid for but used only for reminder texts (NOT AI)
Evidence: documents/company/03_tools_inventory.md; documents/processes/02_scheduling_and_dispatch.md; interviews/02_scheduling_and_dispatch_interview.md ([09:30]); interviews/03_service_ticket_to_invoice_interview.md ([16:00]).
Shows: $299 a month since March 2024; Kyle copies the next day's calls in by hand, about 20 minutes a night.
Estimate: $3,588 subscription + 83 hours x $50 = $4,150; about $7,700 a year.
Better fix: decide to adopt it properly (it could address I01, I02, I07) or cancel and pick a tool the techs will use.

### I11 Install lead drives to the supply counter every install morning (NOT AI)
Evidence: documents/processes/05_installations.md (step 2); interviews/05_installations_interview.md ([02:30]); interviews/06_purchasing_and_inventory_interview.md ([10:00]); data/purchase_orders.csv; data/install_jobs.csv.
Shows: about 1.5 hours each morning before crew 1 starts; free next-morning delivery is available.
Estimate: about 230 install mornings x 1.5 hours = 345 hours x $45 = $15,500, plus partial idle time for the waiting crew.
Better fix: order by 2 pm for delivery to the warehouse the day before. Process change.

### I12 Commercial pricing lives on one person's laptop (NOT AI)
Evidence: documents/processes/04_maintenance_agreements.md (Pricing); interviews/04_maintenance_agreements_interview.md ([09:30]); interviews/03_service_ticket_to_invoice_interview.md ([12:00]).
Shows: only Wes uses "Commercial Pricing 2026.xlsx"; during a two-week absence in July, 6 quotes waited and 2 were lost (about $21,000).
Estimate: about $21,000 of work lost in one absence; ongoing delays on commercial invoices.
Better fix: put the sheet on the shared drive, document it, train a backup (Kyle or Glen).

### I13 Monthly Numbers report built by copying three spreadsheets (AI / automation)
Evidence: documents/processes/07_month_end_close.md; interviews/07_month_end_close_interview.md ([05:30], [09:30]); data/month_end_checklist.csv.
Shows: about 10 hours a month to copy, de-duplicate, count and re-type; report on the 12th business day versus a 10th-day target; Kyle's weekly request not possible.
Estimate: 120 hours x $32 = $3,800 a year, plus a slower report.
Fix: automated report from the dispatch, install and agreement sheets and QuickBooks exports.

### I14 Warranty registrations missed (NOT AI, checklist fix) - linked to conflict C2
Evidence: documents/processes/05_installations.md (steps 5 and 7); interviews/05_installations_interview.md ([06:00], [09:30]); data/install_jobs.csv.
Shows: 37 of 310 installs not registered within 60 days; 5 claims this year, about $4,200 of parts paid by the company.
Estimate: $4,200 a year now, growing as the 37 units age.
Better fix: hold the job close until the data plate photo is in; register on the job day.

### I15 No regular review requests; Facebook irregular (AI / automation, focus area)
Evidence: documents/company/04_marketing.md; interviews/09_marketing_and_reviews_interview.md ([02:30], [06:00]); data/marketing_activity.csv.
Shows: 4.3 stars from 112 reviews; about 30 new reviews from about 5,500 jobs; 9 Facebook posts; no lead source tracking.
Estimate: not directly dollar-valued. Qualitative: more reviews and regular posts support the 70% repeat and referral base.
Fix: automatic review request after completed jobs; a simple post calendar.

## Document-vs-interview conflicts

C1 (process 04, maintenance agreements). Document documents/processes/04_maintenance_agreements.md, Renewal procedure: renewal letter 90 days before the end date, calls at 60 and 30 days. Interview interviews/04_maintenance_agreements_interview.md [03:00]: Wes gets to renewals when he notices them, usually in the last month or after the end, no letters, no 60/30-day calls.

C2 (process 05, installations). Document documents/processes/05_installations.md, step 5: no job is closed without data plate photos. Interview interviews/05_installations_interview.md [06:00]: crews often skip photos when late; Ben closes the job anyway so Dana can invoice.

## Role overlaps

Efficient:
- E01 Marisol Quintero: CSR and backup dispatcher. Already knows waiting customers (02_org_and_roles.md; interview 01 [14:30]; role matrix 75/25).
- E02 Lisa Tran: purchasing and inventory. Knows on-order and on-shelf together (interview 06 [00:00]).
- E03 Ruth Vossberg: payroll and HR from the same personnel files (interview 08 [00:00]).
- E04 Sam Kowalczyk: lead tech and field trainer; trains on jobs he already runs (02_org_and_roles.md; role matrix 75/25).

Problematic:
- P01 Dana Pruitt: bookkeeper and informal IT; interruptions, no backup for either (interview 03 [00:00]; interview 07 [15:00]).
- P02 Ray Mendez: install lead doing supply counter runs (I11; role matrix 20% purchasing).
- P03 Wes Delacroix: sells, prices and renews alone; renewals slip when busy (I03, I12; interview 04 [16:00]).
- P04 Kyle Vossberg: operations manager approving every PO over $500 by text while in the field; orders miss the 2 pm cutoff (06_purchasing_and_inventory.md; interview 06 [06:00]; data/purchase_orders.csv).

## Reconciliation (each issue counted once)

| Id | Issue | AI? | Annual estimate |
|---|---|---|---|
| I09 | Supplier re-quote | No | $90,000 (upper bound) |
| I08 | Van stock / parts runs | Automation | $47,000 |
| I12 | Pricing key person | No | $21,000 (one absence) |
| I03 | Commercial renewals | Yes | $18,000 |
| I05 | Slow web leads | Yes | $16,800 (assumed 10% loss) |
| I11 | Counter pickups | No | $15,500 |
| I01 | Ticket re-keying | Yes | $11,700 |
| I02 | Dispatch double entry and status calls | Yes | $11,000 |
| I10 | Housecall Pro unused | No | $7,700 |
| I07 | Timesheets | Yes | $6,500 |
| I06 | Tune-up booking calls | Yes | $5,500 labor (+ $22,300 service owed) |
| I14 | Warranty registrations | No | $4,200 |
| I13 | Month-end report | Yes | $3,800 |
| I04 | After-hours retyping | Yes | $3,400 |
| I15 | Reviews and social | Yes | not valued |
| | Total (excluding I06 service owed and I15) | | about $262,000 |

The top three AI picks by combined time, revenue and fit: I01 (ticket capture, also feeds I08 and I13), I03 (renewals), I06 (tune-up booking). I05 and I02 are strong alternates.
