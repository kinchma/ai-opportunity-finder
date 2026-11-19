# Prompt: build a realistic synthetic small company (works with Manus or any capable LLM)

Fill in the three variables, then paste everything below the line.

- [INDUSTRY / MODEL]: trailer manufacturer selling through ~80 independent dealers, family-owned, in Pennsylvania, founded 1980s (inspired by the shape of Car Mate Trailers; do not copy it)
- [HEADCOUNT]: about 50
- [EXTRA FOCUS]: marketing and social media, including a realistic assessment of the company’s presence and activity on Facebook, Instagram, TikTok, and other relevant channels; clearly distinguish fictional company facts from external research.

---

ROLE
You are building a fully fictional but highly realistic small company to use as synthetic test data for an academic AI-agent project. Use [INDUSTRY / MODEL] and [HEADCOUNT] below as the starting point. Do not use any real company's name, people, text, or confidential information; use real companies only as inspiration for the general shape of the business. Everything you produce must be invented.

STEP 1: RESEARCH FIRST
Search the web and write short research notes, with source links, on:
- How companies of this type and size are organized and staffed.
- Which tools they actually use for accounting, quoting, inventory, production scheduling, HR and payroll, and customer or dealer management, and where spreadsheets and paper still dominate versus real CRM, ERP, or MRP systems.
- Typical revenue per employee, margins, and purchasing patterns for this industry.
- How they source their main materials and components.
- Common operational inefficiencies in companies this size.
- How small manufacturers and dealer-led businesses use marketing and social media, including Facebook, Instagram, TikTok, and other relevant channels, noting evidence limitations and avoiding assumptions based solely on company age.
Base every later choice on this research.

STEP 2: BUILD THE COMPANY
Create a fictional name, location, history, owner family, revenue, product lines, and customer or dealer network. Then produce:
1. Company profile and website copy (about page, product or service pages), plus a realistic assessment of marketing and social-media presence, activity, ownership, dealer referrals, measurements, and gaps.
2. Org chart plus a role-by-function matrix: every person (fake names, titles, tenure) and which functions they perform, with approximate percent of their time. Functions: finance and accounting, sales, marketing, production or operations, purchasing and inventory, quality and warranty, customer service, HR and payroll, IT, facilities and admin. Some people wear several hats.
3. Tools inventory per function: tool, how it is used, who owns it, workarounds. Use a realistic mix: a few real systems, many spreadsheets, at least one tool that was bought but is barely used, and some paper forms.
4. Process documents (1 to 2 pages each) for: order to delivery, production scheduling, purchasing and receiving, inventory counting, month-end close, payroll and time cards, warranty or returns, quoting, onboarding, and facilities upkeep. Write them the way a small company really writes them: informal, a bit outdated, uneven in detail.
5. Sample data files (CSV or XLSX): customer or dealer list, parts or materials list with supplier and unit price, purchase orders for the last 12 months, monthly production or service log, warranty or complaint log, month-end checklist, staff roster with hours.
6. One SME persona per functional area (one page each): name, role, tenure, how they talk, what they know, what they do not know, frustrations. A persona must answer interview questions using only facts in the company files and say "I'm not sure" when something is not covered.

STEP 3: BUILD IN REALISTIC INEFFICIENCIES
Embed 12 to 15 inefficiencies, including a grounded marketing or social-media issue where the fictional evidence supports one. They must be subtle and believable, never cartoonish, and must not be labeled in the company documents. They should only be discoverable by reading the processes, data, and interviews. Include variety across these types:
- Spreadsheets still carrying parts of the business that should be in a system (for example production scheduling or dealer orders).
- Manual month-end tasks (exports, re-keying, hand reconciliation).
- A supplier used for 20+ years for certain parts and never re-quoted, so prices run 10 to 20 percent above competitive resellers. Include data that shows it.
- Low-value tasks done by the wrong person (for example the receptionist walking the site to collect wastebaskets and empty them).
- Double entry between quotes, orders, and production work orders.
- Paper time cards or approvals typed in later.
- Inventory counted by hand on a schedule, with reordering by gut feel and occasional stockouts.
- Warranty or complaint tracking buried in email threads.
- Key-person risk (one person who understands the pricing spreadsheet).
- Tools bought but under-used.
Also plant role overlaps: 3 to 4 that are efficient (one person covers adjacent functions that share data) and 3 to 4 that are inefficient (one person spread across unrelated functions, creating bottlenecks or key-person risk).

STEP 4: ANSWER KEY (separate file, titled "Do not share with the analysis agent")
For each planted inefficiency or overlap, list: where it hides (file and process), why it is inefficient or efficient, a rough annual cost in hours or dollars with your assumptions, and what a good fix looks like (AI agent, simple automation, purchasing or process change, or not an AI problem).

CONSTRAINTS
- Realistic over dramatic. Imperfect, plain writing in the process documents.
- Keep everything internally consistent: names, dates, headcount, costs, and totals must reconcile across all files.
- Public and synthetic information only.
- Deliver a folder of Markdown plus CSV or XLSX files and a README that lists every file.
- Ask at most five clarifying questions, and only if truly needed. Otherwise proceed.
