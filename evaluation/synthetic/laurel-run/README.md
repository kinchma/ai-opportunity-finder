# Laurel Run Trailer Works — synthetic test case

This folder contains one **fictional academic test case** for an agentic company-discovery and analysis project. Laurel Run is an invented, family-owned Pennsylvania trailer manufacturer. The operating snapshot is October 31, 2026; people, businesses, records, metrics and products are fictional. The package is not a profile of the real website that inspired the visual design.

## Start here

1. Put this entire `Laurel_Run_Test_Case` folder in your project's chosen test-cases directory. You can keep future synthetic companies as sibling folders with their own manifests and files.
2. Open `CLAUDE_DESKTOP_PROMPT.md`, copy its prompt, and paste it into Claude Desktop after giving Claude access to your existing project and this test-case folder. Claude should inspect your architecture before making changes.
3. Start the discovery stage from the fictional website, not from the full company package. The published site is `https://laurelrun-hzs8tm2r.manus.space`. **On November 16, 2026 it was private and redirected unauthenticated visitors to sign-in.** Make it Public in the website publication controls if an external agent must crawl that URL, or use the local site as described below.
4. Your actual application should ask the human owner to confirm or correct the discovered industry before proceeding. The fictional website's form only prepares a draft locally: it does not contact an owner or confirm anything.
5. Only at the later analysis stage, provide the documents in `01_analysis_agent_material/` as appropriate. Evaluate a completed agent run separately against `02_evaluator_only_DO_NOT_SHARE/`.

## What's in the folder

| Item | Purpose |
|---|---|
| `case_manifest.json` | Portable case ID, website locations and stage-specific paths. Treat this as test-harness metadata, not discovery evidence. |
| `website/` | Source and static pages for the fictional manufacturer website; see its README for local use. |
| `01_analysis_agent_material/` | The fictional company profile, organization and tools, operational records, marketing/social data, 10 process documents, 10 SME personas, 11 simulated interview transcripts, CSV datasets and research notes. Ten interviews cover the documented processes; one covers marketing and social media. The research references real external sources but does not establish facts about this fictional firm. |
| `02_evaluator_only_DO_NOT_SHARE/` | Hidden evaluation expectations, answer key, planted-issue explanations and marketing analysis. Do not give this to a discovery or analysis agent. |
| `SYNTHETIC_COMPANY_CREATION_PROMPT.md` | The updated prompt used to create a company, including the social-media focus. This is case-generation material, not evidence for the running discovery agent. |
| `CLAUDE_DESKTOP_PROMPT.md` | A ready-to-paste request for the Claude Desktop project builder. |

## Agent access boundaries

The folder labels are **not** security controls. An agent given the parent directory, broad filesystem access, or an index containing all files can read the answer key. To preserve a meaningful test:

- **Discovery:** expose only the website URL or `website/site/`; do not provide the manifest, generation prompt, company documents or evaluator key as evidence.
- **Analysis:** expose only the website and explicitly authorized files under `01_analysis_agent_material/`; keep the evaluator folder and generation prompt out of prompts, search indexes, retrieval tools and filesystem mounts accessible to the analysis agent.
- **Evaluation:** after the run is complete, an authorized evaluator may compare the result to `02_evaluator_only_DO_NOT_SHARE/`. Claude Desktop may build the evaluator, but the deployed discovery/analysis agent must not receive this material. Verify the actual permissions and tool scopes, not just folder names.

The website and documents are intentionally not live business services. The company has no LinkedIn profile. The Facebook and Instagram activity in the records is simulated; there are no actual account handles or live profiles, and there is no TikTok account. Do not invent external profiles or treat this scenario as a rule for other companies.

The interviews in `01_analysis_agent_material/interviews/` are simulated **text transcripts**, each paced for approximately 20 minutes. No real interviews were conducted and no audio recordings are included. Some SMEs appear in more than one interview, reflecting the company's small size.

## Local website

From this case folder, run:

```bash
python3 -m http.server 8000 --directory website/site
```

Then open `http://127.0.0.1:8000/` on the same machine. A remote agent cannot reach another computer's `127.0.0.1`; use a securely reachable host or the published site with appropriate visibility. See `website/README.md` for asset and rebuilding details. The local server is a simple test service, not a production deployment.

## Extend to additional companies

Keep each company in a sibling folder, with its own stable case ID, metadata, website, analysis materials and isolated evaluation material. Let each case define its own facts, channels, expected outcomes and owner-confirmation behavior. Do not globally hardcode Laurel Run's industry, absent LinkedIn account, employee count, issues or source paths.
