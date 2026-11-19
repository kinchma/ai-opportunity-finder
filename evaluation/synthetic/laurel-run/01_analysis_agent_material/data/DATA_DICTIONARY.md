# Laurel Run Trailer Works — data dictionary

**Fictional academic case; snapshot 2026-10-31.** All organizations, people, products, prices, offers, records, events and values in these files are invented for the case. These files are not records of actual businesses or people. State names are geographic references, not claims about actual dealers. No email addresses or street addresses are provided. Dollar amounts are U.S. dollars. Dates use ISO `YYYY-MM-DD`; a month uses `YYYY-MM`. Blank fields mean not provided or not applicable to the record as described below; they do not mean zero unless explicitly stated.

The reporting year is **2025-11-01 through 2026-10-31**, inclusive. Unless explicitly marked as a planned future step or an offer-validity date, event dates are on or before the snapshot. The dealer and staff lists are complete at the snapshot; the unit log is complete for the reporting year's unit counts. The monthly social ledger is complete for its specified fictional channels and recorded fields during the reporting year, not for all interactions or marketing outcomes. The other files are selected or illustrative records with the limits described below. The 12-item material catalog is not a complete bill of materials. The selected PO, count, claim, checklist and hours files are not a general ledger or complete accounting reconciliation. Software-system names, where mentioned in other company records, are real product names; their usage in this case is fictional.

## Keys and common units

- `employee_id`, or any field ending in `employee_id`, joins to `staff_role_matrix.csv`; `reporting_manager_id` is also an employee key, with a blank for the president. `dealer_id` joins to `dealer_list.csv`; `sku` joins to `parts_materials.csv`. Supplier IDs and names are shown together in the materials, offers and PO files. Each prefix has its own identifier sequence; similar numeric suffixes across record types do not imply a shared sequence.
- `quantity` and count fields use the specified material `unit`, except production figures and the example order quantity, which count trailers. Hours are hours per person unless explicitly labeled as total staff-hours. Money fields ending in `_usd` are nominal U.S. dollars; material prices are delivered prices excluding sales tax.
- Do not infer a VIN from a work-order number. No VIN appears in these sample files. The fact that a material has a particular axle or component rating does not establish a completed trailer's payload or compliance; use the trailer's applicable certification and load labels and fit review.

## `staff_role_matrix.csv`

**Coverage:** all 50 employees at the snapshot. The retired founder and outside contractors are excluded. Each person's ten functional allocations add to 100% and represent approximate working-time shares, not separate jobs or payroll amounts.

| Column | Meaning |
|---|---|
| `employee_id`, `full_name`, `title` | Staff key, invented name and role title. |
| `reporting_manager_id` | Employee key of direct manager; blank only for the president. |
| `hire_date` | Fictional employee hire date. |
| `tenure_years_as_of_2026_10_31` | Elapsed calendar days from hire to snapshot divided by 365.2425, rounded to two decimal years. |
| `finance_accounting_pct`, `sales_pct`, `marketing_pct`, `production_operations_pct`, `purchasing_inventory_pct` | Estimated percent of the employee's time in the named function. |
| `quality_warranty_pct`, `customer_service_pct`, `hr_payroll_pct`, `it_pct`, `facilities_admin_pct` | Estimated percent of the employee's time in the named function. |

## `dealer_list.csv`

**Coverage:** all 80 active independent dealer accounts at the snapshot, `DLR-0001` through `DLR-0080`, one row per dealer. This is an account list, not a list of retail customers or a complete dealer contact file. Dealer retail prices are not provided.

| Column | Meaning |
|---|---|
| `dealer_id`, `dealer_name` | Unique dealer key and invented dealer name. |
| `state` | State of the fictional account; no street or city address is asserted. |
| `account_status_as_of_snapshot`, `dealer_type` | Account status at 2026-10-31 and the independent-dealer relationship. |
| `credit_status` | Whether credit approval is recorded in this sample; `Not specified` does not mean declined or unapproved. |
| `standard_terms` | Net 30 days from the shipment invoice applies when a dealer is approved for credit. |

## `parts_materials.csv`

**Coverage:** 12 selected current supplier-of-record SKUs at the snapshot, not all materials, the complete supplier list or a complete bill of materials. The case specification supplies some ratings, grades and finishes only by reference to the intended build; no additional numeric rating or grade is inferred here.

| Column | Meaning |
|---|---|
| `sku`, `description`, `specification` | Internal item key, concise item description and material or assembly details. Both description and specification are needed for full context. |
| `supplier_id`, `supplier_name` | Current supplier-of-record key and invented name. |
| `unit` | Purchasing/counting unit, such as each, length, assembly, sheet, kit or box; SKU-0012 has 250 screws per box. |
| `delivered_unit_price_usd`, `price_basis` | Fictional delivered price per stated unit, including freight and excluding sales tax. |
| `supplier_status_as_of_snapshot` | Supplier's relationship for the item as of the snapshot. |

## `supplier_offers.csv`

**Coverage:** two individually fictional, unsolicited written alternatives for the same `SKU-0001`, not purchases, supplier approvals, contracts or evidence of market prices. Both offers match the current item specification, packaged contents, freight, 50-unit monthly release and stated lead-time basis. The lead-time duration is not supplied. Engineering fit/compliance review and supplier and financial due diligence remain pending. Validity dates after the snapshot describe the offers' stated future validity, not a completed future transaction.

| Column | Meaning |
|---|---|
| `supplier_id`, `supplier_name`, `sku` | Alternative supplier key/name and the matching internal SKU. These suppliers are not the supplier of record. |
| `item_specification` | Full quoted item description and dimensions, contents and pattern. |
| `offer_date`, `valid_through_date`, `offer_type` | Date of written offer, its stated final validity date and offer type. |
| `delivered_unit_price_usd`, `unit` | Quoted delivered price per axle assembly. |
| `annual_quantity_basis`, `monthly_release_quantity` | Quoted basis of 600 each annually, in 50-unit monthly releases; not a commitment. |
| `payment_terms`, `freight_and_tax`, `packaged_contents_basis`, `lead_time_basis`, `lot_size_basis` | Stated commercial and comparison terms; freight is included and sales tax excluded. |
| `offer_status_as_of_snapshot`, `qualification_status` | Offer-only status and qualification work still pending at the snapshot. |

**Quantity extensions:** the twelve selected current-supplier releases in `purchase_orders.csv` total 600 × $276 = **$165,600** delivered, excluding sales tax. At the same 600-unit quantity, the Brackenway offer extends to 600 × $240 = **$144,000**, and the Willow Vale offer to 600 × $250 = **$150,000**. These are separate quantity extensions, not alternate purchase records or additional invoice totals.

## `purchase_orders.csv`

**Coverage:** 12 selected PO lines, one 50-unit `SKU-0001` release in each reporting-year month. For this selected SKU the rows reflect the case's 600 units of receipts in the year. They are not all the company's POs, total purchases, supplier invoices, cost of goods sold or the general ledger. The October line is ordered 2026-10-08 and received 2026-10-15; all listed receipts occurred by the snapshot. Alternative offers do not appear as POs.

| Column | Meaning |
|---|---|
| `po_id`, `line_number` | Purchase-order key and line number within that PO. |
| `order_date`, `received_date` | Date ordered and date the listed line was received in full. |
| `supplier_id`, `supplier_name`, `sku` | Supplier-of-record identifiers and internal material key. |
| `quantity_ordered`, `quantity_received`, `unit` | Ordered and received quantities in the stated material unit. |
| `delivered_unit_price_usd`, `line_total_usd`, `price_basis` | Delivered unit price and quantity-extended line amount, freight included, sales tax excluded. |
| `payment_terms`, `receipt_status_as_of_snapshot` | Stated terms and status as at 2026-10-31. |

## `monthly_production_log.csv`

**Coverage:** the complete 12-month case unit log for 2025-11 through 2026-10, including the example order's one October Trailfield. Each row represents a calendar month. Each month has 125 completions and 125 shipments. November 2025 and October 2026 each show 50 Trailfield, 45 Enclosure and 30 Workspan; the other ten months each show 50, 46 and 29 respectively. The deliberately even case counts should not be taken as evidence of seasonality.

| Column | Meaning |
|---|---|
| `month`, `period_start`, `period_end` | Month and inclusive calendar-period boundaries. |
| `trailfield_completed`, `enclosure_completed`, `workspan_completed` | Number of trailers completed during the month, by family. |
| `total_completed` | Sum of the three monthly completion counts. |
| `trailfield_shipped`, `enclosure_shipped`, `workspan_shipped` | Number of trailers shipped during the month, by family. |
| `total_shipped` | Sum of the three monthly shipment counts. |

The annual completion and shipment totals are each 600 Trailfield, 550 Enclosure and 350 Workspan, or 1,500 trailers. This is a unit log, not a monthly revenue ledger, BOM or component-consumption ledger.

## `marketing_social_activity.csv`

**Coverage:** 12 fictional calendar-month summaries from 2025-11 through 2026-10, complete for the specified social-channel activity and recorded fields in the scenario. These are invented case values, not exports from actual accounts or real platform metrics. Facebook and Instagram were present for all 12 months; no TikTok account existed in the period. A monthly zero is an observed fictional zero in the named count, not a blank or a measurement of unrecorded outcomes. There are no handles, URLs, message contents or customer identities in this file.

| Column | Meaning |
|---|---|
| `month` | Calendar month containing the original inquiry, post, recap and end-of-month follower snapshot. All counted replies, dealer contacts and forwards for that month's inquiries also occurred that month and by 2026-10-31. |
| `facebook_posts`, `instagram_posts` | Posts published on each fictional company channel in the month; a post published on both platforms counts once on each. |
| `shared_facebook_instagram_post_pairs` | Number of pairs of Facebook and Instagram posts in the same month that use the same topic and photo. Each pair contains one post from each channel and is already included in both platform post counts. |
| `tiktok_account_present`, `tiktok_posts` | `No` throughout the period and zero posts, respectively; zero does not mean an account existed. |
| `facebook_followers_at_month_end`, `instagram_followers_at_month_end` | Fictional per-account follower snapshots as of each month-end, not flows or unique combined people; do not sum the monthly snapshots or the two channels to estimate distinct people. |
| `facebook_product_inquiries`, `instagram_product_inquiries` | New product- or availability-related inbound message threads by originating platform, excluding spam, comments and dealer operational correspondence; additional messages in a thread are not new threads. Counts need not equal distinct people. |
| `facebook_replied_within_2_business_days`, `instagram_replied_within_2_business_days` | Number of that month's inquiry threads first answered within two business days after receipt, and by the snapshot. A business day is Monday–Friday excluding company holidays. These are subsets of the inquiry counts, not additional inquiries. |
| `facebook_given_dealer_contact`, `instagram_given_dealer_contact` | Number of that month's inquiry threads where the person asked where to buy and Keira supplied dealer contact information. Subsets of the inquiry counts, not confirmed visits or sales. |
| `facebook_forwarded_to_dealer_with_consent`, `instagram_forwarded_to_dealer_with_consent` | Number of that month's threads for which Keira sent the person's contact and inquiry to a dealer with permission; a subset of those given dealer contact information, not a confirmed visit, order or sale. |
| `monthly_recap_minutes` | Keira's fictional recorded minutes reviewing the two channels and related correspondence, copying and reconciling the monthly activity counts, and filing the recap for Tessa. Excludes time creating posts, obtaining approval, replying to or forwarding inquiries, and preparing handouts. A recap is recorded even in months with no posts. |

The 12 rows total **18 Facebook posts**, **7 Instagram posts**, 7 shared post pairs and zero TikTok posts. Facebook had posts in 10 months; Instagram in 6. At the snapshot the two follower counts are **248** and **73**, respectively. The year contains 13 Facebook and 4 Instagram inquiry threads, all 17 initially answered within two business days; 11 and 4 threads, respectively, received dealer contact information, and 5 and 1 of those were forwarded to a dealer with permission. The other two threads sought product information only. Monthly recaps total **540 minutes**. No later dealer response, retail conversion, social reach, link clicks, attributed manufacturer order or sales outcome is recorded or implied.

## `warranty_complaint_log.csv`

**Coverage:** 14 individually fictional selected claim openings during the reporting year, not the full annual claims universe. The case assumes 120 claims opened in the reporting year, including trailers from prior and current shipment cohorts. A count of opened claims is not a failure rate for trailers shipped during the reporting year. No actual VIN, customer identity or claim-specific financial liability is included. The sample's two open cases have no closing date as of the snapshot.

| Column | Meaning |
|---|---|
| `claim_id`, `dealer_id`, `dealer_name` | Claim key and reporting dealer's key/name. |
| `model_family`, `trailer_shipment_date` | Trailer family and fictional date it shipped to the dealer; the date identifies the cohort, not a VIN. |
| `reported_date`, `issue_description` | Opening/report date and a concise description of the dealer's concern. |
| `reviewed_by_employee_id`, `reviewed_by_name` | Quality and warranty employee who reviewed the case. |
| `dealer_repair_approval_date` | Date Iris approved the dealer repair; blank if not shown. |
| `closed_date`, `status_as_of_snapshot` | Closure date when closed, or blank when open; status is at 2026-10-31. |
| `record_channel`, `closure_evidence` | Source of the case correspondence and, where closed, its completion evidence. |

`CLM-2026-0088` is an Enclosure case from `DLR-0002`: reported 2026-10-05 with lamp detail and photos in the dealer email thread, reviewed by Iris, repair approved 2026-10-09 and closed 2026-10-20.

## `month_end_checklist.csv`

**Coverage:** one fictional completed close checklist for September 2026, not all months, every accounting control or the October close. The final September checklist signoff is 2026-10-07. October's close remains open at the 2026-10-31 snapshot. These checklist entries do not reproduce account balances, amounts or individual AP packet matching.

| Column | Meaning |
|---|---|
| `period_start`, `period_end` | Inclusive September accounting period. |
| `step_id`, `task` | Within-checklist step identifier and task description. |
| `completed_by_employee_id`, `completed_by_name` | Person recorded as completing the individual step. |
| `completed_date`, `status`, `completion_note` | Date, completion status and brief fictional checkoff note. |

## `staff_hours.csv`

**Coverage:** all 50 staff IDs with illustrative hours for the biweekly period Sunday 2026-10-18 through Saturday 2026-10-31. The roster includes 36 hourly employees—`E006`, `E007`, `E014`, `E015`, and `E019`–`E050`—and 14 salaried employees. This is not the annual payroll ledger. Hourly rows represent illustrative paper-card summaries; salaried weekly hours are illustrative estimates, **not hourly time cards**, and salaried staff use exception notices. Blank salaried regular/overtime fields do not assert exempt status or determine legal classification. No employee salary amounts are supplied.

| Column | Meaning |
|---|---|
| `employee_id`, `full_name`, `title`, `reporting_manager_id` | Roster identity, role and direct manager. |
| `pay_basis` | `Hourly` or `Salary`; not a legal overtime classification. |
| `pay_period_start`, `pay_period_end` | Inclusive 14-day period. |
| `week1_start`, `week1_end`, `week1_hours` | First Sunday–Saturday workweek and illustrative hours. |
| `week1_regular_hours`, `week1_overtime_hours` | For hourly rows only, hours up to 40 and hours above 40, calculated separately for week 1. |
| `week2_start`, `week2_end`, `week2_hours` | Second Sunday–Saturday workweek and illustrative hours. |
| `week2_regular_hours`, `week2_overtime_hours` | For hourly rows only, hours up to 40 and hours above 40, calculated separately for week 2. |
| `total_hours`, `hours_basis` | Sum of the two illustrative weekly hours and the type of record/estimate. |
| `hourly_rate_usd`, `illustrative_gross_usd` | Filled only for the Micah example; blank for all other people, not zero. Gross is before withholding. |
| `approval_status_as_of_snapshot`, `planned_approver_employee_id`, `planned_approval_date` | Hourly supervisory approval is planned for 2026-11-02, not completed at snapshot; no salaried approval is presented. |
| `payday_status_as_of_snapshot`, `planned_payday` | Payday on 2026-11-05 is planned, not a completed post-snapshot event. |

For `E021`, week 1 is 40 hours and week 2 is 42 hours, including two hours above 40 in week 2. At $24/hour and a $36 illustrative overtime rate, gross is 80 × $24 + 2 × $36 = **$1,992**, before withholding. This fictional example is not a general legal-payroll interpretation.

## `inventory_cycle_counts.csv`

**Coverage:** one illustrative 2026-10-30 cycle-count round covering six selected SKU categories. Cora's weekly count practice is not a claim that all other weekly counts are included. Values are selected on-hand examples, not a complete inventory ledger, GL reconciliation, BOM or valuation.

| Column | Meaning |
|---|---|
| `count_date`, `sku`, `description`, `unit` | Date, internal item key, description and stock unit. |
| `stock_sheet_before_count`, `physical_count` | Quantity on the stock sheet before the count and quantity physically counted. |
| `count_variance` | Physical count minus pre-count stock-sheet quantity. |
| `stock_sheet_after_count` | Illustrative updated stock-sheet quantity after the count. |
| `counted_by_employee_id`, `counted_by_name`, `reviewed_by_employee_id` | Employee references for counting and review. |

## `inventory_shortages.csv`

**Coverage:** four separate fictional shortage events during the reporting year, each affecting three named staff for three hours before reassignment to other work. These are event examples, not a complete inventory movement history. No substitution occurred and no safety compromise is represented; they are not claims that the entire plant stopped.

| Column | Meaning |
|---|---|
| `shortage_id`, `event_date`, `sku`, `description` | Internal event key, event date and material affected. |
| `employee_1_id`, `employee_2_id`, `employee_3_id` | The three distinct affected staff IDs for the event. |
| `staff_held_count`, `hours_held_per_staff`, `total_staff_hours_held` | Number of affected staff, hours per person and their product in staff-hours; each event records 3 × 3 = 9 staff-hours. |
| `next_action`, `substitution_made`, `safety_compromise` | Recorded next work action and whether a substitution or safety compromise occurred. |

## `order_example.csv`

**Coverage:** one fictional linked dealer quote, order, one-trailer work order, shipment and invoice; this is an illustrative record, not a full order or invoice ledger. Its one shipped Trailfield is included in October's 50 Trailfield shipments. It is unrelated to the selected supplier PO totals.

| Column | Meaning |
|---|---|
| `dealer_id`, `dealer_name` | Approved-credit dealer's key and invented name. |
| `quote_id`, `quote_date`, `quote_preparer_employee_id`, `quote_approver_employee_id` | Quote key/date and the staff who prepared and approved it. |
| `dealer_acceptance_date`, `order_id`, `order_date` | Written dealer-acceptance date and the distinct order key/date. |
| `work_order_id`, `work_order_date`, `scheduler_employee_id` | Separate one-trailer production work-order key/date and scheduling employee. |
| `family`, `configuration`, `quantity` | Trailer model family, baseline configuration and quantity of trailers. |
| `dealer_base_price_usd`, `option_description`, `option_price_usd` | Dealer net base and the separately priced mount-only option. |
| `quote_order_invoice_total_usd` | Base plus the selected option; $4,800 + $120 = $4,920. This is not a retail price. |
| `finish_inspection_date`, `shipment_date` | Completion-inspection and dealer shipment dates. |
| `invoice_id`, `invoice_date` | Separately identified sample invoice and its shipment-date issuance. |
| `payment_terms`, `freight`, `tax_treatment` | Net 30 from shipment invoice, no separately charged freight and sales tax excluded from the amount shown. |
