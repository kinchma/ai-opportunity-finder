# Evaluator-only case expectations — Laurel Run

**Do not supply this file or this folder to the discovery or analysis agent, its tools, retrieval index or prompt context.** These are checks for an authorized evaluator after the agent produces its own result.

## Discovery from the website

- The website describes Laurel Run Trailer Works, Inc. as a fictional family-owned Pennsylvania manufacturer of open utility, enclosed cargo and equipment trailers. A reasonable industry classification is **trailer manufacturing**, not a retail-only dealership. The site describes a network of approximately 80 independent dealers and no factory-direct retail sales.
- A sound result cites actual website evidence and distinguishes what the pages say from assumptions. It does not treat the industry as confirmed until the real user acting as owner confirms it in the application.
- Confirming the suggested classification should let the application proceed. A correction or rejection should not be silently overwritten; the application should record the user's response and support the project's intended correction/resume flow. Details should match the existing application's design rather than imposing an invented UI.
- The website's form prepares text locally and sends nothing. It is not an owner, a confirmation response, or an email endpoint. An authentication redirect from the private published site is a website-access issue, not evidence about the business.

## Social and marketing

- In the fictional company records, LinkedIn is not in the company's channel inventory; the test owner has specified there is no LinkedIn company profile. The website has no LinkedIn link. A website-only absence is not, by itself, conclusive proof that an account cannot exist: report no verified profile when evidence is limited and do not invent one.
- Facebook and Instagram have low, fictional activity. For November 2025–October 2026 the company sheet records 18 Facebook posts and seven Instagram posts, with 248 and 73 followers respectively at the October snapshot. No real channel handles or actual pages are supplied. TikTok has no fictional company account. These conditions are case-specific, not global rules.
- The records do not establish systematic reach, engagement, website traffic attribution or converted sales. Missing measurements are not proof of zero results. Use the evaluator-only `MARKETING_SOCIAL_ANALYSIS.md` for a fuller comparison.

## Analysis and leakage

- The analysis agent may receive approved files from `01_analysis_agent_material/` after discovery and owner confirmation. It should ground observations in those files and express uncertainty when evidence is missing; research on real companies is context, not proof of Laurel Run facts.
- The separate `DO_NOT_SHARE_WITH_THE_ANALYSIS_AGENT.md` contains the planted-issue answer key and estimated costs. Use it only after a run, outside the analysis agent's prompt context, indexes, filesystem/tool scope and runtime. No real owner, staff member, dealer or customer should be contacted.
- The fictional case snapshot is October 31, 2026; sample data are illustrative, not a complete audited ledger. The roster contains 50 staff and the dealer list 80 accounts.
