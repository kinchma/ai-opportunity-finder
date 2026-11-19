# Moving the project to the Mac (written Nov 14, 2026)

Goal: run everything on the MacBook with LM Studio on localhost, so no second machine or
network is needed while travelling.

## 1. On the Omen: put the project on GitHub (private)
In PowerShell, in the project folder:

    git --version          # if "not recognized":  winget install Git.Git   then reopen PowerShell
    gh --version           # if "not recognized":  winget install GitHub.cli then reopen PowerShell
    git init -b main
    git add .
    git status             # CHECK: .env, .env.off, .venv and runs must NOT be listed
    git commit -m "AI Opportunity Finder: all six agents real, 113 tests"
    gh auth login          # GitHub.com > HTTPS > Yes > Login with a web browser
    gh repo create ai-opportunity-finder --private --source=. --push

The repo is private. `cases/` is included (it holds text fetched from two real companies'
websites); decide what to do with it before making the repo public for the final submission.

## 2. On the Mac: get the code
    xcode-select --install             # only if "git" is not found
    brew install gh                    # or download GitHub CLI from cli.github.com
    gh auth login
    cd ~/Documents                     # or wherever you want it
    gh repo clone ai-opportunity-finder
    cd ai-opportunity-finder

## 3. On the Mac: Python
    python3 --version                  # need 3.10 or newer (the Omen uses 3.13)
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.mac .env

## 4. On the Mac: LM Studio
- Load Qwen3.6-35B-A3B (already there) AND a small second model for the Critic, both at once.
- Developer tab: start the server (port 1234). "Serve on Local Network" is not needed.
- Open `.env` and set `LLM_MODEL` and `LLM_CRITIC_MODEL` to the exact ids LM Studio shows.
- Check:  curl http://localhost:1234/v1/models     (both ids should be listed)

## 5. Test and run
    python -m pytest -q                # expect 113 passed
    streamlit run app_cases.py

The Carmate case comes across with the repo. Its `result.json` is the failed 7:26 pm run (the
Mac was unreachable); click "Re-run analysis". Then follow "Run this on the Omen" in
PROJECT_NOTES.md Part 9 from step 3: the steps are the same on the Mac.

## Daily routine while travelling
    git add . ; git commit -m "what changed" ; git push       # on the Mac, end of each night
Back home on the Omen:  git pull
