# Data Dictionary

Larkmoor Comfort Heating & Air. Snapshot 2026-10-31. Reporting year 2025-11-01 to 2026-10-31. Dollar amounts in US dollars. Dates are YYYY-MM-DD; months are YYYY-MM. Blank means not recorded or not applicable.

## Files

- monthly_volume_log.csv: complete for the year. Service calls, tune-ups due and done, residential installs, RTU replacements, commercial PM visits, after-hours messages, web requests per month. Totals: 5,200 service calls; 1,280 tune-ups due, 1,044 done; 310 installs; 40 RTUs; 290 PM visits; 1,050 after-hours messages; 410 web requests.

- staff_role_matrix.csv: complete, all 35 employees. Percent of time by function; each row adds to 100.

- commercial_agreements.csv: sample of 13 of about 90 agreements, chosen to include every agreement that passed its end date before renewal in the year (11). Status: Renewed, Renewed late, Lost, Active. renewal_contact_date is the first renewal contact Wes recorded.

- comfort_club_booking_log.csv: season totals for Comfort Club tune-up booking calls.

- service_calls_sample.csv: 11 service calls from the dispatch spreadsheet with ticket and invoice dates. days_job_to_invoice is 0 when paid on site.

- purchase_orders.csv: sample of 9 purchase orders. Times are when the PO photo was texted to Kyle, when Kyle replied OK, and when Lisa ordered. delivery_method "will call (Ray)" means picked up at the Northgate counter.

- supplier_quotes.csv: the Ridgeview HVAC Supply quote RQ-2026-03 against current Northgate prices for the same Aerovance models.

- install_jobs.csv: sample of 10 install jobs from the install log with pickup method, data plate photos and warranty registration status.

- timesheets_pay_period.csv: all 24 field employees for pay period PAY-2026-21 (2026-10-04 to 2026-10-17), with Ruth's correction notes. Totals 1,912 regular and 188 overtime hours.

- month_end_checklist.csv: the September 2026 close checklist with completion dates and Dana's hours per step.

- marketing_activity.csv: complete for the year. Facebook posts (9 total), new Google reviews, rating, radio and postcard spend.

## Ids

- EMP-001 to EMP-035: employees (ADP RUN ids), used in the role matrix, timesheets and service calls (tech_id).
- SC-2026-nnnn: service calls in the dispatch spreadsheet. INV-2026-nnnn: QuickBooks invoices.
- CA-2025-nnn: commercial agreements, numbered by the year first signed.
- CC-nnnn: Comfort Club members.
- JOB-2026-nnnn: install jobs. PO-2026-nnnn: purchase orders. PAY-2026-nn: pay periods. RQ-2026-nn: supplier quotes.
