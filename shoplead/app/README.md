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
