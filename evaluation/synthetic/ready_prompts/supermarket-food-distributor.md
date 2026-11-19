# Synthetic company prompt (values filled in): supermarket-food-distributor

ROLE AND PURPOSE
You are building a fully fictional but realistic small company as synthetic test data for an
academic AI-agent project (Carnegie Mellon Agentic AI program). An analysis system will read the
company's website, then (after the owner approves) its internal documents, interview transcripts
and data samples, and recommend where AI agents could save time and money. Your package must look
like what a real small-business owner would hand over: plain, uneven, partly out of date, with
inefficiencies that are discoverable from evidence but never labelled. A separate answer key,
kept outside the company folder, records what was planted so the system can be scored.

Company type: regional food service distributor supplying produce, dairy and specialty grocery items to independent supermarkets. Location: southeastern Pennsylvania and New Jersey. Headcount: about 45. Sales model:
sells and delivers by its own trucks to about 140 independent supermarkets and small grocery chains on weekly standing orders plus phone and email add-ons. Extra focus: order intake and route delivery, including spoilage and credits for damaged or short deliveries. Folder id: supermarket-food-distributor.

Everything must be invented: company name, people, customers, suppliers, prices, records. Do not
use or imitate any real company, person, trademark or confidential information; real companies
may only inspire the general shape. Software products named as tools (QuickBooks, Excel, Outlook,
a CRM) may be real. Put a one-line note "Fictional company created for an academic test case" in
the website footer and in each README, nowhere else.

Work through steps 1 to 5, then sections 6 to 10, in order. Do not skip the self-check in section 10.

STEP 1: RESEARCH (short)
Write 3 to 5 short research notes, each with source links, on: how companies of this type and size
are organized and staffed; which tools they really use (and where spreadsheets, paper and email
still dominate); typical revenue per employee, margins and volumes; how they buy their main
materials or services; common operational inefficiencies at this size; how they market themselves
(website, social media, referrals). Mark clearly what is external evidence and its limits. These
notes go in `research/` and are context only: no company facts in them.

STEP 2: THE COMPANY
Decide and keep consistent everywhere: name, founding year, owner family or founders, location,
products or services with real-sounding prices, annual volume (orders, jobs, units, patients,
clients), revenue band, customers or channel, main suppliers, every employee (fake full name,
title, tenure, reporting line, percent of time per function). Functions to cover: finance and
accounting, sales, marketing, operations or production or service delivery, purchasing and
inventory (if any), quality or warranty or complaints, customer service, HR and payroll, IT,
facilities and admin. Several people wear several hats. Pick a snapshot date (e.g. 2026-10-31) and
a 12-month reporting year ending then; every date and count must fit that year.

STEP 3: THE PROCESSES (8 to 10)
Choose 8 to 10 core processes that fit this business (for example: order or job intake, quoting or
estimating, scheduling or dispatch, purchasing and receiving, inventory, delivery or service
completion, invoicing and collections, month-end close, payroll and time cards, warranty or
complaints or returns, onboarding, facilities or fleet upkeep, marketing). Each process gets one
process document and one matching interview (step 5), with the same number and topic words in both
file names.

STEP 4: PLANT THE ISSUES (15) AND ROLE OVERLAPS (8)
Plant exactly 15 issues across the processes. Subtle and believable, never cartoonish, never named
as problems in the company files. Each must be discoverable from TEXT evidence (a process document,
an interview, or the company files), and supported by numbers where possible (volumes per year,
minutes per task, hours per week, prices). A reader should be able to estimate an annual cost.
Required mix:
- At least 8 that an AI agent or automation could plausibly help with (re-keying between systems,
  manual matching or reconciliation, status questions answered by looking things up, documents
  scattered across email, manual reports assembled from several exports, intake from unstructured
  emails or calls, scheduling by spreadsheet and whiteboard, paper forms typed in later).
- At least 4 that are NOT AI problems (a supplier never re-quoted for 15+ years with a cheaper
  written offer on file; a tool paid for but barely used; low-value work done by the wrong person;
  a key person with no backup; a simple checklist or policy fix).
- The biggest single item by dollars should be a non-AI purchasing or pricing issue, so the
  scoring can tell whether the system mistakes everything for an AI opportunity.
- One issue tied to the order intake and route delivery, including spoilage and credits for damaged or short deliveries if one is given.
- Exactly 2 DOCUMENT-VS-INTERVIEW CONFLICTS: the process document says the work is done one way
  and the matching interview says, plainly, that in practice it is done differently (e.g. the
  procedure says two approvals, the interviewee says the second approval is usually skipped when
  the manager is out). State both sides concretely; do not flag them. Every other interview must
  agree with its document.
Plant 4 efficient role overlaps (one person covers adjacent work that shares information) and 4
inefficient ones (one person spread across unrelated work, creating a bottleneck or key-person
risk). Show them through the org file, the role matrix and the interviews.

STEP 5: WRITE THE FILES
Follow the folder layout in section 7 and the formatting rules in section 6 exactly; the analysis
system depends on them.

Website (`website/index.html`, optional extra pages): a static, self-contained page (no external
scripts, fonts or images from the internet; local images optional). The system reads ONLY
index.html and only its first ~3,000 characters of visible text, so put at the top: the company
name, what it does in plain industry words ("commercial HVAC service contractor"), location,
customers or channel, main products or services. Include contact details as real HTML (a tel:
link, a mailto: link or a <form>), a mobile viewport meta tag, a <title> and a meta description.
Include social links (Facebook, Instagram, LinkedIn, TikTok, YouTube, X) ONLY for the accounts the
company really has in your story; if it has none, link none. Do not add a chat widget unless the
company has one in your story. The website must not reveal internal problems.

Company files (`documents/company/`): 01_company_profile.md (history, products, volumes, customers,
revenue band); 02_org_and_roles.md (org chart in text, every person, reporting lines);
03_tools_inventory.md (per function: tool, use, owner, workarounds; include a few real systems,
many spreadsheets, paper forms, and one tool bought but barely used); 04_marketing.md (channels,
activity, what is and is not measured; facts only).

Process documents (`documents/processes/NN_topic.md`): written by the company, informal, a little
outdated, uneven in detail, 2,500 to 4,500 characters each (hard maximum 4,500). Steps, owners,
tools, volumes, an example with real-looking ids and dates, and what to do when things go wrong.

Interviews (`interviews/NN_topic_interview.md`): one simulated 15-20 minute transcript per process
with the person who does the work (8,000 to 15,000 characters each), plus one for the [EXTRA
FOCUS] area if given. The interviewee speaks naturally, uses the same vocabulary as the process
document, answers only from facts in the company files, says "I'm not sure" when something is not
covered, and mentions frustrations and workarounds in passing. This is where most issues and both
conflicts become visible. Also `interviews/personas/NN_function.md`: one short persona per
function (role, tenure, how they talk, what they know and do not know).

Data (`data/*.csv` plus `data/DATA_DICTIONARY.md`): 8 to 14 CSV samples (customer or account list,
items or services with supplier and unit price, purchase orders, monthly volume log, complaint or
warranty log, month-end checklist, staff hours for one pay period, role matrix with percent of
time, supplier offers, and any focus-area activity log). The system shows only the header and the
first 11 data rows of each CSV, so put the rows that matter first, and repeat every number an issue
depends on in a process document or interview. The dictionary explains columns, units, which files
are samples rather than complete ledgers, and how ids link across files.

SECTION 6: FORMATTING RULES THE SYSTEM DEPENDS ON
- Text formats only: .md, .csv, .json, .txt (and .html for the website). No PDF, DOCX or XLSX
  (stored but not read).
- Markdown: first line "# Title"; sections with "## " headings; blank line between paragraphs;
  each paragraph under 800 characters (the system cuts documents into ~900-character passages at
  headings and paragraph breaks and never splits a paragraph, so one huge paragraph becomes one
  oversized passage).
- Interview turns as separate paragraphs: "**Interviewer:** ..." and "**SME:** ...", with a
  "## [mm:ss] topic" heading every 3 to 6 turns. First lines: who is interviewed, role, date, and
  "Fictional transcript".
- File names: two-digit number, lowercase snake_case, matching numbers and topic words between a
  process document and its interview (documents/processes/05_month_end_close.md and
  interviews/05_month_end_close_interview.md).
- Ids look real and consistent across files (ORD-2026-0412, INV-2026-0388, PO-2026-0115,
  JOB-2026-0907, EMP-014).
- No text that reads like instructions to an AI ("ignore", "you must", "rate this company",
  "note to the assistant", "system prompt"): the system strips such phrases as possible prompt
  injection.
- Total size budget: all process documents together at most 45,000 characters.
- Plain US English; no emoji.

SECTION 7: FOLDER LAYOUT (exact)
```
cases/supermarket-food-distributor/
  case.json
  README.md                          (what the case is; fictional; file list; nothing about issues)
  website/index.html                 (+ optional about.html, services.html, assets/)
  documents/company/01_company_profile.md
  documents/company/02_org_and_roles.md
  documents/company/03_tools_inventory.md
  documents/company/04_marketing.md
  documents/processes/01_<topic>.md ... 10_<topic>.md        (8 to 10)
  interviews/01_<topic>_interview.md ... (one per process, + focus area)
  interviews/personas/01_<function>.md ...
  data/DATA_DICTIONARY.md
  data/<name>.csv ...                                         (8 to 14)
  research/01_<topic>.md ...                                  (3 to 5, external context)
evaluation/answer_keys/supermarket-food-distributor.json                            (machine-readable key, section 8)
evaluation/answer_keys/supermarket-food-distributor/ANSWER_KEY.md                   (human-readable key, section 8)
evaluation/answer_keys/supermarket-food-distributor/CASE_EXPECTATIONS.md            (what a good result looks like)
evaluation/synthetic/supermarket-food-distributor/GENERATION_NOTES.md               (variables used, research sources, consistency checks)
```
Do NOT create owner/, results/ or index/ inside the case (the app creates them). Nothing about the
planted issues, the answer key or this prompt may appear anywhere under cases/supermarket-food-distributor/.

case.json, exactly this shape (fill the brackets):
```json
{
  "id": "supermarket-food-distributor",
  "name": "<Company Name, Inc.>",
  "stage": "new",
  "status": "Case created. Next: run Discovery.",
  "created": "<snapshot date>T09:00:00",
  "updated": "<snapshot date>T09:00:00",
  "company_input": {"website": "local", "risk_tolerance": 0.4,
                    "description": "<one sentence the owner would type, e.g. 'Family-owned HVAC contractor, 35 people, scheduling is our headache'>"},
  "materials_authorized": []
}
```
("website": "local" makes the system read the case's own website folder; materials stay
unauthorized until the owner approves them in the app.)

SECTION 8: THE ANSWER KEY
ANSWER_KEY.md: one entry per planted issue (I01 to I15) and role overlap (E01 to E04 efficient,
P01 to P04 problematic): where the evidence is (file and section), what it shows, the evaluator's
assumptions, an annual estimate in hours and dollars with the arithmetic shown, whether it is an
AI/automation opportunity or not (and the better fix if not), and for the 2 conflicts both sides
with file references. End with a reconciliation table that adds each issue once.

CASE_EXPECTATIONS.md: the correct industry classification from the website; what discovery should
and should not claim (including social presence: only accounts linked on the page); which 3 issues
a strong analysis should put in its top recommendations and why; which non-AI issues it should not
dress up as AI projects; things it must not invent.

supermarket-food-distributor.json, exactly this format (keywords are matched case-insensitively against each idea's name
and description; every keyword in a list must appear; choose 1 or 2 plain words per item that any
sensible description of that issue would contain, e.g. ["month-end"], ["time card"], ["warranty"],
["re-quote"] is too narrow, ["supplier"] is better):
```json
{
  "expected_industry": "<short industry phrase that the website supports>",
  "expected_top_picks": [["<kw>"], ["<kw>"], ["<kw>", "<kw>"]],
  "planted_issues": [["<kw>"], ["<kw>", "<kw>"], "... 15 lists, in I01..I15 order"],
  "forbidden_claims": ["<strings that must not appear, e.g. invented social handles or a linkedin.com/company URL the company does not have>"],
  "min_citation_coverage": 0.6,
  "conflicts": [{"process": "<name>", "document": "<file path>", "interview": "<file path>", "summary": "<one line>"}]
}
```

SECTION 9: DELIVERY
Preferred: a .zip whose top level contains `cases/` and `evaluation/`. Otherwise one text bundle in
which every file starts with a line `=== FILE: <path> ===` (path relative to the repository root),
followed by the file's full content, with no other text between files. Write every file in full:
no placeholders, no "... continue as above".

SECTION 10: SELF-CHECK BEFORE DELIVERING (fix anything that fails, then list the results in
GENERATION_NOTES.md)
1. Every person, id, price, date and total agrees across the website, company files, processes,
   interviews and CSVs; the role matrix sums to about 100% per person; headcount matches.
2. All 15 issues and both conflicts are visible in text files (not only in CSV rows beyond row 11)
   and none is labelled as a problem in the company files.
3. Every process document is 2,500-4,500 characters; all of them together at most 45,000; every
   paragraph under 800 characters; every process has a matching interview by number and topic.
4. index.html states the industry in its first 3,000 visible characters, has a contact link or
   form and a viewport tag, and links only the social accounts the story says exist.
5. Nothing under cases/supermarket-food-distributor/ mentions the answer key, planted issues, inefficiencies, the
   evaluation, or this prompt; nothing reads like instructions to an AI.
6. case.json matches the template; the slug matches the folder; supermarket-food-distributor.json is valid JSON with 15
   planted_issues lists.
Ask at most three clarifying questions, and only if a variable is missing. Otherwise proceed.
