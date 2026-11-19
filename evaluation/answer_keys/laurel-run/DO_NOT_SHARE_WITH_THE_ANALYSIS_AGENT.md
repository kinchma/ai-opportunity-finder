# Do not share with the analysis agent

**PRIVATE — evaluator use only.** Exclude this file and any excerpt or paraphrase of the private answer map from every package or other material shared with the analysis agent. Public evidence paths below are relative to the sibling `../01_analysis_agent_material/` folder; they identify the records an analysis agent should use for these conclusions. Do not disclose private labels, assumed rates, counterfactuals, or this key as company facts.

## How to interpret this key

Laurel Run, its people, records, commercial offers, and amounts are fictional. The case snapshot is **2026-10-31**, and the illustrative reporting year is **2025-11-01–2026-10-31**. “Public evidence” below means evidence stated in the fictional shared files, not external verification or facts about a real business. The file paths and evidence are intentionally explicit so an evaluator can trace each inference without exposing this key.

All rates used for opportunity costing are **evaluator assumptions**, expressed in fictional fully loaded USD per staff-hour, not observed employee pay, contractor quotes, or invoices. Labor values are hypothetical opportunities to redeploy time, not necessarily payroll or cash savings: compensation falls only if a feasible staffing, overtime, hiring, or contractual change actually reduces cash outlays. Where public files describe total time on a task, the proportion that can be removed without impairing controls is generally **not observed**; the canon's full-increment estimates are assumptions to test, not measured waste. Any implied annual repeatability, no overlap, and hypothetical alternatives likewise need validation. Round figures are order-of-magnitude comparisons, before implementation, transition, service, licensing, maintenance, tax effects, and risk-adjustment costs unless explicitly noted.

The 15 numbered items are distinct **analytical buckets**, not proof that 15 separately realizable projects exist. The four constructive and four problematic role overlaps below are interpretive lenses, not extra issues. One intervention may affect several buckets; test changes and allocate time once rather than adding nominal values mechanically. Where evidence is missing, an inference or planned assumption is labeled as such; no inference should be treated as an observed failure.

## Fifteen planted issues

### I01 — Re-entry from quote to order and work-order packet

**Public evidence.** `processes/01_order_to_delivery.md` §§1–2 and `processes/08_quoting.md` §§1, “After dealer acceptance” state that Priya re-keys approved model/options into the order register and paper build packet. `data/monthly_production_log.csv` records 1,500 completions and shipments; `processes/01_order_to_delivery.md` states one WO per trailer. `data/order_example.csv` illustrates separate QTE, ORD and WO identifiers. `personas/07_customer_service.md` describes Priya's intake and order role.

**Interpretation and estimate.** Repeated transcription creates avoidable handling and a risk of inconsistent fields, but an actual error count is not shown. Evaluator assumptions: use 1,500 WOs/year as the transcription-work proxy; assume **4 incremental, preventable minutes per WO**, at **$32/staff-hour**. Thus 1,500 WOs/year × 4 minutes/WO ÷ 60 = **100 staff-hours/year**, valued at **$3,200/year**. The files do not time the work, establish the exact number of duplicate-entry actions per WO, or prove all four minutes recoverable, especially for multi-trailer orders. Exclude quote preparation, I11 revisions and I12 status inquiries.

**Response.** Use one controlled approved-data record or validated template transfer to generate register and packet fields; preserve distinct identifiers, dealer acceptance and human approval. Basic structured forms are more appropriate than autonomous AI for a simple copy task.

### I02 — Manual production-schedule reconciliation

**Public evidence.** `processes/02_production_scheduling.md` §§“Weekly setup” and “Changes, shortages and dates” describes Jonah checking orders, stock notes and supervisor reports, maintaining both Excel and the whiteboard, and giving paper packets to the floor; it states roughly 50 working weeks. `company/03_tools_inventory.md` production row and `personas/04_production_operations.md` corroborate the workflow.

**Interpretation and estimate.** The separate schedule and board invite repeated reconciliation and stale status, although no measured backlog, discrepancy rate, or reconciliation duration is provided. Evaluator assumptions: **1.5 incremental and avoidable staff-hours/week** × 50 working weeks/year × **$38/staff-hour** = **75 staff-hours/year**, or **$2,850/year**. The 1.5 hours are not public evidence. Exclude fabrication, ordinary production, I11 revision checks and I07 held workers.

**Response.** Pilot a shared, timestamped schedule with one accountable owner and a simple board-update routine; check permissions and floor access. A straightforward shared tool may suffice; do not presume an ERP or AI is necessary or integrated.

### I03 — SKU-0001 axle sourcing not formally re-competed

**Public evidence.** `processes/03_purchasing_and_receiving.md` §“Axle release and supplier offers” states that Ridge Hollow has supplied a comparable specification since June 2003 and that no formal competitive re-quote was solicited before the 2026 unsolicited offers. `data/purchase_orders.csv` has twelve selected releases, each 50 axles at $276 delivered, with 600 received for this SKU; it is not the company's full purchasing ledger. `data/supplier_offers.csv` and `data/DATA_DICTIONARY.md` §“supplier_offers.csv” record two offers, both delivered freight included, sales tax excluded, net 30, 600/year in 50-unit monthly releases, matching stated specification, contents and lead-time basis. The actual lead-time duration is not supplied. Brackenway's $240 offer is dated 2026-10-16 and Willow Vale's $250 offer 2026-10-19; both state validity through 2026-11-15. Neither was qualified or purchased at the snapshot. `data/parts_materials.csv` identifies the current supplier and component.

**Gross comparison, not a realized saving.** At the observed fictional **600-axle historical receipt quantity**, current 600 × $276/axle = **$165,600/year**; the Brackenway quantity extension is 600 × $240 = **$144,000/year**, a **$21,600/year gross quoted-price difference**. The incumbent's $36/unit premium is **15% of the $240 alternative**; the gross difference is **13.04% of current spend**. Alternatively, Willow Vale extends to **$150,000/year**, a **$15,600/year** gross difference; the incumbent's $26/unit premium is **10.4% of the $250 alternative**, or **9.42% of current spend**. These alternatives compete for the same volume and are **not additive**. Repeating 600 units next year, availability of the offered price, and unchanged quantities are evaluator assumptions, not commitments.

**Net and response.** Realizable net savings are **unknown**: qualification, engineering/compliance review, capacity and financial due diligence, actual lead times, contracting, switching/transition costs, taxes, and negotiated prices remain unresolved; no purchase or switch is shown. Refresh comparable offers, qualify fit and supplier reliability, and negotiate. Sourcing and safety review are needed, not AI by default. Do not infer a market-wide price, payload or legal compliance from the offers or the axle rating.

### I04 — Receptionist's office-wastebasket rounds

**Public evidence.** `processes/10_facilities_upkeep.md` §“Office rounds and records” states that Holly receives visitors, maintains supplies and collects office wastebaskets on daily rounds; ordinary rounds take about **2 hours/week across roughly 50 weeks**. It also says outside cleaners serve the company but their specific schedule, task assignment and price are not specified. `company/03_tools_inventory.md` facilities row and `data/staff_role_matrix.csv` row E007 show the combined reception/admin role.

**Interpretation and estimate.** Competing reception and custodial demands may create coverage pressure, but the public record does **not** document a missed visitor or the portion of the 2-hour ordinary rounds spent solely collecting wastebaskets. The canon's attribution of the entire 2 hours to the transferable activity is therefore an evaluator assumption, not an observed breakdown. At assumed **$27/staff-hour**, baseline 50 weeks/year × 2 hours/week = **100 staff-hours/year**, valued at **$2,700/year gross**. A wholly hypothetical alternative requires 50 weeks/year × 1 hour/week = **50 staff-hours/year** at assumed **$24/hour**, or **$1,200/year**. The comparison is **$2,700 − $1,200 = $1,500/year net opportunity**, with **50 fewer combined work-hours/year** if those assumptions hold. It is not a cleaner's quote, confirmed budget reduction, or evidence that existing rounds are dispensable.

**Response.** Time the wastebasket component separately, test consolidated bins or appropriately scheduled service, and verify reception coverage, hygiene, safety and total cost. Do not assume the current cleaner will take the work for free. This is ordinary work design, not an AI task. P01 shares this entire $1,500 boundary.

### I05 — Close reporting, reconciliation and re-keying

**Public evidence.** `processes/05_month_end_close.md` §“Lydia's review” describes bank/AR/AP review, shipping-to-invoice comparison, report exports and re-keyed management summary, about **4 hours/month** in all; it explicitly excludes individual AP packet matching and payroll entry. `data/month_end_checklist.csv` shows the September export, summary and reviews, with signoff on 2026-10-07; October was open at the snapshot. `personas/01_finance_accounting.md` describes Lydia's responsibility and limits.

**Interpretation and estimate.** The workflow combines necessary controls with possible repeated data handling. Evaluator assumptions: treat the full 4 hours/month as incremental time potentially removable or repurposable and apply **$42/staff-hour**: 12 months/year × 4 hours/month = **48 staff-hours/year**, or **$2,016/year**. Publicly observed time is the whole comparison/reconciliation/export/summary workload, **not** evidence that all 4 hours are redundant or avoidable; a credible net benefit must retain accountant review and measure the residual time. Exclude I13 packet matching and I06 payroll.

**Response.** Map a repeatable export and summary template, retain traceable supporting records, reconciliations, exception handling, approvals and Lydia's signoff. Test for errors and integration limits rather than assuming a software feature.

### I06 — Paper hourly cards re-entered into payroll

**Public evidence.** `processes/06_payroll_and_time_cards.md` §§“Cards and signoff” and “Prepare and review” specifies 36 hourly staff on paper cards, 14 salaried staff using exception notices, **26 periods/year**, and approximately **2 hours/period** for Nia's entry and verification, excluding supervisor signoff. `data/staff_hours.csv` is one illustrative period, not an annual payroll ledger. E021's sample has 40 and 42 hours in separate weeks; 80 × $24 plus 2 × $36 = $1,992 gross, and the later approvals/payday are only planned at the snapshot. This example is not Nia's pay or a legal classification conclusion.

**Interpretation and estimate.** Evaluator assumptions: all 2 entry/verification hours per period can hypothetically be saved while maintaining required review, at **$30/staff-hour**. 26 periods/year × 2 hours/period = **52 staff-hours/year**, valued at **$1,560/year**. The workload is in the procedure; its entire avoidability is not. Exclude supervisors' approval and E03's hypothetical onboarding/payroll handoff benefits.

**Response.** Evaluate electronic time capture and approved transfer to payroll, with access control, supervisor signoff, exception handling and separate workweek overtime calculations. Confirm actual functionality, costs and legal requirements; no autonomous payroll decision is proposed.

### I07 — Manual cycle counts, judgment-based reordering and shortages

**Public evidence.** `processes/04_inventory_counting.md` §§“Each week” and “When something is short” states that Cora counts six selected categories on paper, then updates Excel; Devon considers on-hand, open POs and expected needs. It gives approximately **1.5 hours/week** for counting and interpreting the selected lines over 50 weeks. `data/inventory_cycle_counts.csv` is one illustrative six-item count, including two one-unit variances, not a full inventory reconciliation. `data/inventory_shortages.csv` records **four events**, each holding **three workers for three hours** before reassignment; no substitution or safety compromise occurred. `processes/02_production_scheduling.md` notes these were not whole-plant stoppages.

**Interpretation and estimate.** Evaluator assumptions: count/interpretation increment 50 weeks/year × 1.5 hours/week × **$30/staff-hour** = **75 staff-hours and $2,250/year**. The public 1.5 hours is the entire stated selected-count workload, not an observed avoidable increment; ongoing physical counts and review remain necessary. Separately, 4 events/year × 3 people/event × 3 hours/person = **36 held staff-hours/year**; at assumed **$30/staff-hour**, this is **$1,080/year**. Treating all 36 hours as unproductive and preventable, and the two buckets as nonoverlapping, are evaluator assumptions, not established counterfactuals. Combined illustrative opportunity: **111 staff-hours and $3,330/year**; no proof that all future shortages can be prevented.

**Response.** Establish documented min/max or reorder triggers using verified on-hand, allocations, open POs and lead times; continue targeted cycle counts, check exceptions and monitor actual results. Do not substitute components without Felix and Iris reviewing fit and required specifications. Avoid counting the same wait or coordination again under I02 or E02.

### I08 — Claim information scattered between email threads and an index

**Public evidence.** `processes/07_warranty_and_returns.md` §§“When a dealer reports a problem” and “Examples and workload” describes a small Excel claim index with details and photos in original email threads, and **120 case openings/year** across mixed shipment cohorts. `data/warranty_complaint_log.csv` contains 14 selected cases, including CLM-2026-0088 with email details and photos; it is not all 120 claims. `personas/06_quality_warranty.md` describes Iris's inspection and claim work.

**Interpretation and estimate.** Retrieval and follow-up can require extra searching, but no search duration, failure frequency, repair cost or claim-specific financial liability is recorded. Evaluator assumptions: 120 opened cases/year × **15 incremental and avoidable minutes/case** ÷ 60 = **30 staff-hours/year**; at **$32/staff-hour**, **$960/year**. Not a failure rate of current-year units; exclude technical evaluation, repairs, I11 revision verification and E04's hypothetical extra handoff.

**Response.** Maintain a permission-controlled shared claim index with links to source correspondence, required fields, owner and status; preserve human repair approval and completion evidence. A simple index is preferable to an AI system making coverage or safety decisions. P04 uses this same $960, not a new cost.

### I09 — Pricing-formula knowledge and exception approvals concentrated in sales management

**Public evidence.** `processes/08_quoting.md` §“Work up the price” states that Tessa maintains and understands the formula/rate workbook, handles approximately **100 exception questions/year**, and quotes remain pending if her answer or approval is unavailable; Priya uses routine templates. `company/03_tools_inventory.md` sales row and `personas/02_sales.md` confirm Tessa's leadership and workbook role.

**Interpretation and estimate.** This creates a plausible key-person and exception-routing exposure. The public records identify Tessa as the named owner and direct exceptions to her, but they do **not expressly establish that no other person understands any formula** or document lost deals, a quote-delay duration, or a price error. Evaluator assumptions: 100 exceptions/year × **12 incremental and preventable minutes/exception** ÷ 60 = **20 staff-hours/year**; at **$55/staff-hour**, **$1,100/year**. Exclude routine quote work and I01 re-entry; do not add a speculative revenue-loss estimate.

**Response.** Document formulas and inputs, control versions, test calculations and train an approved backup; keep Tessa's stated approval until authority is properly reassigned. This is knowledge management and control, not a need for AI to set prices. P03 shares $1,100.

### I10 — Lightly used CRM subscription

**Public evidence.** `company/03_tools_inventory.md` sales row says three Zoho CRM seats are licensed, Priya has entered a small pilot set of contacts, and the dealer spreadsheet and email remain the working records. `processes/08_quoting.md` §1 specifies the fictional **$3,600/year** agreement for three seats. `data/dealer_list.csv` and its dictionary describe 80 active dealer accounts, not CRM adoption or seat-level utilization.

**Interpretation and estimate.** A paid pilot alongside the operational spreadsheet raises a question about return on spend, not proof of waste. Evaluator assumption: **75% of $3,600/year = $2,700/year at-risk spend**. The 75% is **not measured unused capacity**, and three seats cannot necessarily be reduced in quarter-seat increments; no contract language, discount, cancellation fee or recoverable amount is shown. This is neither a confirmed cash saving nor an additional labor benefit.

**Response.** Decide whether to adopt with a record owner, data migration and success measures, or reduce/renew/cancel after checking contract, seat and transition terms. A CRM agent or AI feature is not the default remedy; avoid also attributing this license cost to I15.

### I11 — Old build-sheet copies require revision verification

**Public evidence.** `processes/02_production_scheduling.md` §“Changes, shortages and dates” and `processes/01_order_to_delivery.md` §3 describe Tessa's dealer-approved change, Jonah's dated replacement page, return of the old page by Theo/Avery, and Iris's current-revision check. Both state **24 annual examples** where a changed page is checked against an older copy. The actual example in `data/order_example.csv` has no revision documented.

**Interpretation and estimate.** Coexisting copies require control and verification; the public record does not establish incorrect builds or how long checks take. Evaluator assumptions: 24 checks/year × **0.5 incremental and preventable staff-hour/check** × **$45/staff-hour** = **12 staff-hours/year** and **$540/year**. Exclude ordinary I02 schedule reconciliation and I01 data copying.

**Response.** Version-control approved packets, mark current revisions conspicuously, retrieve old pages and capture acknowledgement at the floor handoff. Keep inspection and dealer authorization; AI must not decide unapproved substitutions or safety compliance.

### I12 — Separate lookups for dealer order-status follow-ups

**Public evidence.** `processes/01_order_to_delivery.md` §4 says Priya checks the order register and asks Jonah or Mateo for current position before responding; about **300 status follow-ups/year** are separate from stockout inquiries and warranty cases. `company/03_tools_inventory.md` customer-service row and `personas/07_customer_service.md` corroborate the lookup. A target is an estimate, not a promise.

**Interpretation and estimate.** A current status is dispersed among records and people, creating potential extra lookup effort; no duration or response failure is measured. Evaluator assumptions: 300 follow-ups/year × **4 incremental and preventable minutes/follow-up** ÷ 60 = **20 staff-hours/year**; at **$32/staff-hour**, **$640/year**. Exclude I01 transcription, stockout and warranty inquiries, and social replies/referrals under I15.

**Response.** Use one owned status field with timestamps and an agreed update rhythm; a person reviews replies and qualifies tentative dates. Do not claim existing real-time integrations. E01's hypothetical split handoff is a separate counterfactual, not this existing lookup.

### I13 — Manual routine PO, packing-slip and bill matching

**Public evidence.** `processes/03_purchasing_and_receiving.md` §“At the receiving bay” specifies that Elena matches each supplier bill to the signed packing slip and PO before bill entry, with Devon approving exceptions. The procedure states roughly **480 bill/receipt packets/year**, including partial deliveries and invoices, **not necessarily 480 unique POs**. `processes/05_month_end_close.md` distinguishes packet matching from Lydia's close-report work.

**Interpretation and estimate.** Handling paper packets can add manual effort; the control itself remains necessary. Evaluator assumptions: 480 packets/year × **3 extra preventable minutes/packet** ÷ 60 = **24 staff-hours/year**; at **$32/staff-hour**, **$768/year**. The extra minutes and complete recoverability are not documented. Exclude I05 close and normal exception-approval work.

**Response.** Use consistent keyed PO references and assisted matching, with a clear audit trail, actual receipt verification and human review of exceptions. Do not auto-approve invoices or bypass segregation of duties; basic structured matching may suffice without AI.

### I14 — Switching and coverage across IT and facilities

**Public evidence.** `processes/10_facilities_upkeep.md` §“Routine service and requests” states Simon maintains devices and service coordination, some small maintenance requests wait while he is doing IT work, and roughly **24 routine handoffs/year at 20 minutes of switching and coordination each**. `data/staff_role_matrix.csv` row E018 allocates approximately 45% each to IT and facilities/admin. `personas/09_it.md` describes both duties. The safety procedure separately requires immediate supervisor-to-Owen escalation and removal of unsafe equipment from service.

**Interpretation and estimate.** Routine coverage pressure is evidenced; a measured safety incident or actual maintenance loss is not. Evaluator assumptions: all 24 × 20 minutes/year ÷ 60 = **8 staff-hours/year** can be avoided, at **$40/staff-hour**, for **$320/year**. The handoff workload is public, but its full avoidability is not. Exclude emergencies, repair time and I04 Holly rounds.

**Response.** Arrange scheduled coverage, cross-train a qualified backup or set contractor escalation for routine requests; preserve immediate safety escalation. Do not use an unattended repair bot. P02 shares $320.

### I15 — Irregular social presence and manually assembled activity recap

**Public evidence.** `company/04_marketing_social_media.md` §§“Social activity recorded during the reporting year” and “Inquiries and records,” `company/03_tools_inventory.md` marketing row, and `data/marketing_social_activity.csv` describe Facebook and Instagram throughout the year: **18 Facebook posts in 10 months**, **7 Instagram posts in 6 months**, with **7 shared topic/photo pairs**; there was **no TikTok account**. October-end followers were **248 Facebook and 73 Instagram**, not a count of distinct combined people. Thirteen Facebook plus four Instagram inquiry threads were all initially answered within two business days; **15** were given dealer details, and **6 of those 15** were forwarded with consent, not additional inquiries. The 12 recorded recap entries total **540 minutes/year**. `data/DATA_DICTIONARY.md` §“marketing_social_activity.csv” defines this as complete only for the named channels and recorded fields. `personas/03_marketing.md` corroborates ownership and the unknown outcome boundary.

**Interpretation and estimate.** The evidence supports irregular activity and a manual, multi-source reporting process—not a causal claim that posting gaps, narrow channels, small audiences or no TikTok caused lost sales. Reach, impressions, clicks, later dealer follow-through, retail conversion and attributable manufacturer revenue are **not systematically recorded**; missing is unknown, not zero. Dealers set retail prices; their retail sales are not Laurel Run revenue. Threads need not be distinct people.

Gross recorded recap workload is **540 minutes ÷ 60 = 9 staff-hours/year**, valued at **$288/year** using the evaluator-assumed **$32/staff-hour**. Evaluator counterfactual: a simpler recap takes **15 minutes/month × 12 months = 180 minutes = 3 staff-hours/year**, valued at **$96/year** at that same assumed rate. The hypothetical **net** is (540 − 180) minutes/year ÷ 60 = **6 staff-hours/year**, or **$192/year**; 15 minutes/month is untested, not a software guarantee or observed outcome. This bucket includes only reviewing, copying, reconciling and filing the recap, not creating/approving posts, replies, forwards, handouts, CRM license, order re-entry or status lookups. No lost-sales, reach or conversion value is monetized.

**Response, in non-AI-first order.** (1) Use a common recap template with retained source links and time-test it. (2) Agree a manageable calendar of approved photos or short videos, a backup and Tessa's approval; no particular channel, including TikTok, is mandatory. (3) Keep a permission-based referral log with follow-up ownership. (4) Manually review available reach, click, inquiry and dealer-feedback measures separately, and consider a basic dashboard only if worth its cost. Apply access and consent controls. None of these guarantees reach, referral or sales, and correlation is not causal attribution.

## Role-overlap map — exactly four constructive and four problematic

These descriptions identify public evidence and a potential reason to retain or change the role combination; their monetary examples are **evaluator assumptions**, not observed duplication, proof of efficiency or cash savings. Working weeks and pay periods follow the stated case schedules. Constructive examples model extra handoff that might arise in a hypothetical split; none is included in the issue total. The problematic examples use the existing issue value once; they add no second charge.

### Constructive overlaps

**E01 — Priya E008, dealer sales plus customer service.** Public evidence: `data/staff_role_matrix.csv` row E008 shows approximately 50% sales and 40% customer service; `processes/08_quoting.md` and `processes/01_order_to_delivery.md` show one person handling intake, routine quotes, accepted orders and dealer status requests. Shared context can reduce handoffs. Evaluator comparison, not an observed avoided handoff: a hypothetical split adds 50 weeks/year × **0.5 staff-hour/week** × **$32/staff-hour** = **25 staff-hours and $800/year**. Retain a single dealer-contact owner and share status; do not add this counterfactual to I12's $640 lookup or the issue total.

**E02 — Devon E012, purchasing plus inventory.** Public evidence: `processes/04_inventory_counting.md` §“Each week” shows Devon reviewing counts, on-hand, open POs and needs before quantity decisions; `processes/03_purchasing_and_receiving.md` shows his PO and exception approvals; `data/staff_role_matrix.csv` row E012 combines purchasing/inventory. Connected information may reduce coordination, though an efficiency gain is not measured. Evaluator comparison: 50 weeks/year × **0.5 staff-hour/week** × **$38/staff-hour** = **25 staff-hours and $950/year** potentially avoided versus a hypothetical split. Preserve the joint review with documented thresholds and backup; this excludes I07 counts/holds and I03 prices and is not part of the issue total.

**E03 — Nia E005, onboarding/HR plus payroll.** Public evidence: `processes/09_onboarding.md` §§“Before and at the start” and “Payroll handoff and follow-up” says Nia handles onboarding paperwork and payroll setup; `processes/06_payroll_and_time_cards.md` §“Prepare and review” shows payroll preparation. `data/staff_role_matrix.csv` row E005 identifies her HR/payroll allocation. Familiarity with hire information can reduce separate handoffs, but no avoided handoff is measured. Evaluator comparison: 26 pay periods/year × **0.5 staff-hour/period** × **$30/staff-hour** = **13 staff-hours and $390/year** versus a hypothetical split. Retain continuity with a trained backup and restricted access; exclude I06 card entry and do not add the comparison to the issue total.

**E04 — Iris E016, floor quality plus warranty.** Public evidence: `processes/01_order_to_delivery.md` §3 describes Iris's final inspection and revision check; `processes/07_warranty_and_returns.md` §§1–2 shows her reviewing claim component details and correspondence. `data/staff_role_matrix.csv` row E016 identifies the quality/warranty function. The same technical owner can potentially link field evidence to inspections and component traceability; a systematic feedback loop or measured time saving is **not documented**. Evaluator comparison: 12 months/year × **1 staff-hour/month** × **$32/staff-hour** = **12 staff-hours and $384/year** avoided versus a hypothetical split. Preserve technical continuity with organized evidence and backup; exclude I08 email search and the issue total.

### Problematic overlaps

**P01 — Holly E007, reception plus wastebasket collection.** Public evidence: `processes/10_facilities_upkeep.md` §“Office rounds and records” and `company/03_tools_inventory.md` facilities row show both duties, while `data/staff_role_matrix.csv` row E007 shows customer-service and facilities/admin allocations. A desk-coverage tradeoff is plausible, but no missed visitor or separate wastebasket-only time is documented. Illustrative comparison is **the same I04 100 baseline hours versus 50 alternative hours and $1,500/year net opportunity**, at the assumed rates and boundaries given there—not an additional $1,500. Measure task time and test coverage, hygiene and actual service pricing; no AI is needed.

**P02 — Simon E018, IT plus facilities.** Public evidence: `processes/10_facilities_upkeep.md` §§“Routine service and requests” and “Urgent hazards are different” describe both duties and delayed routine requests, while `personas/09_it.md` describes Simon's technical and facilities work. The same **I14 24 × 20 minutes = 8 staff-hours/year, valued at $320/year** under the evaluator's $40/hour assumption, is the only charge; do not add another. Arrange coverage and cross-training; urgent hazards still go immediately to the supervisor and Owen, with unsafe equipment out of service.

**P03 — Tessa E003, sales leadership plus concentrated pricing-formula ownership.** Public evidence: `processes/08_quoting.md` §“Work up the price,” `personas/02_sales.md`, and `data/staff_role_matrix.csv` row E003 show management duties, Tessa's workbook maintenance and the exception approval dependency. No other person's complete ignorance is proven, and no lost revenue is observed. Use **I09's same 100 × 12 minutes = 20 staff-hours/year, valued at $1,100/year** under the evaluator's $55/hour assumption; add no key-person or sales-loss cost. Document, version, test and cross-train without bypassing pricing authority.

**P04 — Iris E016, floor inspection plus locating warranty correspondence.** Public evidence: `processes/01_order_to_delivery.md` §3 and `processes/07_warranty_and_returns.md` §§1–2 place inspections and thread/index-follow-up with Iris. The actual extent of competing inspection attention is an inference, not an observed missed inspection. Use **I08's same 120 × 15 minutes = 30 staff-hours/year, valued at $960/year** at the assumed $32/hour; do not add this or I11 a second time. Organize claims and provide a qualified backup. The sensible quality/warranty domain combination in E04 can coexist with this separate administrative bottleneck.

## Unique-issue reconciliation and evaluator cautions

The following arithmetic uses exactly one value for each of **I01–I15** and the Brackenway gross offer difference as the chosen I03 comparison. It is an **illustrative, mixed-category comparison**, not an additive forecast, budget reduction, confirmed procurement saving, or return-on-investment calculation.

| Component | One-time-in-the-sum calculation | Illustrative USD/year |
|---|---|---:|
| Hypothetical net labor opportunity | I01 $3,200 + I02 $2,850 + I04 $1,500 + I05 $2,016 + I06 $1,560 + I07 $3,330 + I08 $960 + I09 $1,100 + I11 $540 + I12 $640 + I13 $768 + I14 $320 + I15 $192 | **$18,976** |
| Unqualified supplier gross price difference | I03: $165,600 current quantity extension − $144,000 Brackenway quantity extension | **$21,600** |
| Hypothetical at-risk license spend | I10: $3,600/year × assumed 75% | **$2,700** |
| **Unique I01–I15 comparison total** | $18,976 + $21,600 + $2,700 | **$43,276/year** |

I04 is already **net of** the $1,200 hypothetical alternative; I15 is already **net of** the hypothetical 180-minute alternative recap. The I03 comparison is **gross of** all qualification, transition and other changes and is not realized; its $15,600 Willow Vale alternative cannot be added to the $21,600 Brackenway comparison. I10's at-risk amount is not a demonstrated cancellable amount. Labor opportunity is not necessarily cash payroll savings, and the full avoidability of the public I04, I05, I06, I07 and I14 workloads is unproven. Implementation costs, required controls and interactions could materially reduce or eliminate net benefit.

The P01–P04 amounts are already inside I04, I14, I09 and I08, respectively. E01–E04 are hypothetical avoided-handoff comparisons outside the issue sum; do not add them to it. Across issues, explicitly exclude I01 copying from I09, I11 and I12; I02 schedule reconciliation from I07 holds and I11 revision checks; I05 close from I13 invoice-packet matching and I06 payroll; and I15 recap from social content, responses, referrals, I10 licensing and I12 status requests. These boundaries are evaluator design assumptions, not proof that actual work measurements would remain disjoint. Test feasibility, human-review and safety requirements, contract rights, baseline timing and actual incremental costs before presenting any business case.
