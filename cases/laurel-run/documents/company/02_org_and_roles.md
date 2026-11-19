# Organization and roles

**As of 2026-10-31.** All names, jobs and employment facts are fictional. Laurel Run has exactly 50 employees. The indentation below is direct supervisory reporting; a person appears once. The founder Elwood Bellamy is retired and is not an employee. Family employees are Mara, Owen and Tessa Bellamy.

- **E001 Mara Bellamy — President and CEO**
  - **E002 Owen Bellamy — Plant Manager**
    - E011 Jonah Sutter — Production Scheduler
    - **E012 Devon Kersey — Materials and Purchasing Manager**
      - E013 Jalen Sorrell — Buyer
      - E014 Cora Whitlock — Receiving and Inventory Clerk
      - E015 Mateo Renshaw — Shipping Coordinator
    - E016 Iris Calder — Quality and Warranty Lead
    - E017 Felix Harrow — Manufacturing Engineer
    - E018 Simon Denby — Facilities and IT Coordinator
    - **E019 Theo Lowry — Fabrication Supervisor**
      - E021 Micah Orlin — Fabricator/Welder
      - E022 Daphne Weller — Fabricator/Welder
      - E023 Silas Breck — Fabricator/Welder
      - E024 Naomi Peller — Fabricator/Welder
      - E025 Ruben Mallory — Fabricator/Welder
      - E026 Mira Ellery — Fabricator/Welder
      - E027 Caleb Winsor — Fabricator/Welder
      - E028 Orla Penwick — Fabricator/Welder
      - E029 Evan Torrey — Fabricator/Welder
      - E030 Taryn Holcomb — Fabricator/Welder
      - E031 Dorian Wren — Fabricator/Welder
      - E032 Nell Forster — Cutting Technician
      - E033 Bryce Langley — Cutting Technician
      - E034 Vera Linden — Cutting Technician
      - E035 Elise Worrall — Paint Technician
      - E036 Harlan Mott — Paint Technician
    - **E020 Avery Carver — Assembly Supervisor**
      - E037 Ada Fenwick — Assembly Technician
      - E038 Gavin Thorne — Assembly Technician
      - E039 Liora Beckett — Assembly Technician
      - E040 Rowan Delaney — Assembly Technician
      - E041 Mabel Keene — Assembly Technician
      - E042 Quinn Alden — Assembly Technician
      - E043 Soren Maddox — Assembly Technician
      - E044 June Merritt — Assembly Technician
      - E045 Ellis Calderwood — Assembly Technician
      - E046 Rhea Voss — Assembly Technician
      - E047 Jonah Weller — Assembly Technician
      - E048 Faye Hollis — Assembly Technician
      - E049 Ansel Croft — Finish and Inspection Technician
      - E050 Esme Larkin — Finish and Inspection Technician
  - **E003 Tessa Bellamy — Dealer Sales Manager**
    - E008 Priya Ellwood — Dealer Account Coordinator
    - E009 Grant Tolland — Dealer Account Representative
    - E010 Keira Morrow — Marketing and Dealer Support Coordinator
  - **E004 Lydia Fenner — Controller**
    - E005 Nia Hadley — Office and Payroll Administrator
    - E006 Elena Corwin — Accounting Clerk
  - E007 Holly Darnell — Reception and Admin Coordinator

## How to read the role matrix

`../data/staff_role_matrix.csv` has one row for each of the 50 people above. `employee_id` is the unique person key, and `reporting_manager_id` is the direct manager's employee ID; only the CEO's manager field is blank. Hire dates are ISO dates. `tenure_years_as_of_2026_10_31` is elapsed calendar days since hire divided by 365.2425 and rounded to two decimal places; it is not completed whole years.

The ten numeric `_pct` columns are estimated shares of each person's working time at the snapshot. They are finance/accounting, sales, marketing, production/operations, purchasing/inventory, quality/warranty, customer service, HR/payroll, IT and facilities/admin, respectively. Each row totals 100. These are approximate allocations, not payroll charges or separate positions. Reporting remains as shown above even when a role contributes across functions: for example, Priya supports sales and dealer service, Devon combines purchasing with inventory, Nia administers both HR and payroll, and Simon handles IT and facilities. Fabrication and assembly supervisors also work with their crews and approve time cards.
