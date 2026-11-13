# ShopLead AI (local scaffold)

Human-gated lead triage for independent auto shops. **Drafts never auto-send.**

## Run

```bash
cd /workspace/shoplead/app
python3 -m http.server 8765
```

Open http://127.0.0.1:8765/

Or open `index.html` directly in a browser (seed fetch needs a local server).

## What it does

- Paste SMS / Facebook / web / voicemail text → extract customer, vehicle, service, urgency, missing info, next action, draft reply
- Edit + **Approve locally (still not sent)**
- Seeded with 8 fixed-demo leads
- Export CSV
- Rules tab documents urgency policy

## Acceptance checks (also logged in browser console)

1. Brake pads on 1987 RX7 → not CRITICAL; vehicle Mazda RX-7
2. Maria grinding + soft pedal → CRITICAL — SAFETY; draft says not sent
3. No "column B/C/D" in drafts
4. 2014 hyuandai Tucson flange → Hyundai Tucson + HIGH — INSPECT

## Project layout

- `PRESSURE_TEST.md` — market pressure test (also in Drive)
- `FREEBUFF_PROMPT.md` — copy-paste Freebuff build prompt
- `fixed_demo_leads.csv` / `fixed_demo_rules.csv` — fixed demo data
- `app/` — runnable local web scaffold

## GitHub

`gh` is not logged in on this box, and Cursor cannot create a GitHub repo via API for you. To publish:

1. Create a private repo `shoplead-ai` under `dubkipz773` on GitHub
2. Then:

```bash
cd /workspace/shoplead
git init
git add .
git commit -m "ShopLead AI scaffold: pressure test, fixed demo, Freebuff prompt, local app"
git branch -M main
git remote add origin git@github.com:dubkipz773/shoplead-ai.git
git push -u origin main
```

(Or connect `gh auth login` first.)
