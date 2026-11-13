# ShopLead AI — Freebuff Build Prompt (copy-paste)

Paste everything below the line into Freebuff as one prompt.

---

You are building **ShopLead AI v1**, a minimal web app for independent auto repair shops (and specialty shops like Mazda RX-7 / JDM).

## Product rules (non-negotiable)

1. Shop staff paste an inbound customer message (SMS, web form, Facebook DM, or voicemail transcript).
2. The app extracts structured fields and produces a **follow-up draft**.
3. **Never auto-send** any SMS, email, or Facebook message. Every draft is for **human review and approve**. UI must say: “Draft for shop review — not sent.”
4. Never put internal spreadsheet language in customer-facing drafts (no “column B”, “column C”, “column D”).
5. Never claim a message was already sent.

## Stack (keep it simple and runnable fast)

Prefer one of:
- Plain HTML + vanilla JS + localStorage (fastest), OR
- Next.js / Node single-page app

No real Twilio/SMS integration in v1. Export CSV / Google Sheets–compatible CSV only.

## Core screens

1. **Inbox / Paste** — textarea for raw customer message + optional source (SMS / Web / Facebook / Voicemail) + Submit.
2. **Lead card** — show extracted:
   - Customer name
   - Phone (if present)
   - Vehicle (year, make, model — normalized)
   - Requested service
   - Urgency: `CRITICAL — SAFETY` | `HIGH` | `HIGH — INSPECT` | `NORMAL`
   - Missing information (human language, not column letters)
   - Next action (shop-facing)
   - AI summary
   - Follow-up draft (editable)
3. **Approve gate** — buttons: Edit draft, Mark approved (still does not send), Copy draft, Export CSV. Status chip: `Draft prepared — review required; not sent` → `Approved locally — not sent`.
4. **Leads list** — seed + new leads, filter by urgency.
5. **Rules** page — plain-English urgency + extraction rules (see below).

## Extraction: rule + LLM hybrid

Implement deterministic rules first; use an LLM only as optional enhancement if an API key is present. v1 must work offline with rules alone.

### Vehicle parsing

- Detect year 1900–2099 near make/model.
- Normalize common makes: hyuandai→Hyundai, honda, toyota, ford, mazda, scion, etc.
- Specialty: `RX7`, `RX-7`, `RX seven`, `FDRX7`, `FD RX7` → **Mazda RX-7** with year if present.
- Scion XD / xD → **Scion xD**.
- Do not emit garbage like `"2008 that has"` as the vehicle.

### Service extraction

Map clear asks:
- alignment / wheel alignment
- oil change / drain plug / oil filter
- wheel bearings / how to do wheel bearings → service: wheel bearing service / DIY guidance request (flag shop policy)
- brake pads / rotors / brakes (see urgency)
- exhaust / catalytic / flange / clamp / weld
- apex seal / rotary rebuild / motor rebuild
- check engine / CEL / engine light / car stops working
- body damage / crash / panel
- engine noise / squeaky motor / banging when shut off → diagnosis

### Urgency rules (CRITICAL is rare)

**CRITICAL — SAFETY** only if one or more:
- grinding brakes **and** soft/spongy pedal
- “can’t stop” / “won’t stop” / no brakes
- pulling hard while braking
- brake fluid leak / puddle of brake fluid
- explicit “don’t drive” / “tow” / “unsafe to drive”
- vehicle dies / stops working while driving in a way that strands them mid-road (still HIGH if intermittent — use judgment: intermittent limp may be HIGH)

**HIGH / HIGH — INSPECT:**
- separated exhaust / dragging pipe / fumes in cabin
- serious drivability that isn’t hard safety
- customer says they have no transportation and need urgent repair

**NORMAL or HIGH (not CRITICAL):**
- Routine “need brake pads / rotors replaced” + callback request → **HIGH** or **NORMAL** with note “inspect before advising driveability” — **NOT CRITICAL**
- Squeaky brakes alone without soft pedal / can’t stop → **HIGH** (inspect), not CRITICAL tow language
- Alignment, oil change, how-to wheel bearings, apex seal estimate → **NORMAL**

### Missing info

Ask only for what’s actually missing, in customer language:
- customer name
- year / make / model
- phone / best callback number
- preferred days or times
- photos (if they offered)
Never say “column B/C/D”.

### Follow-up draft

- Friendly shop voice, short.
- Reference the vehicle and service correctly when known.
- Ask only for missing pieces.
- For true CRITICAL: advise not driving / tow when rules fire; otherwise do not scare customers with tow language for pad replacements.
- Closing line always: “This is a draft for the shop to review; it has not been sent.”

## Demo seed data

Seed 6–8 leads covering:
1. Maria — 2018 Honda Civic — grinding + soft pedal → CRITICAL
2. Squeaky brakes only, no vehicle → HIGH inspect, ask vehicle
3. 2008 Scion xD — squeaky motor → NORMAL, engine noise diagnosis
4. 2014 Hyundai Tucson — cat pipe separated from flange → HIGH — INSPECT, exhaust repair
5. 2019 Ford Expedition — needs alignment → NORMAL, wheel alignment
6. 1987 Mazda RX-7 — apex seal / rebuild quote → NORMAL
7. 1985 Mazda RX-7 — how to do wheel bearings → NORMAL, DIY/how-to request
8. 1987 RX-7 — brake pads callback → HIGH or NORMAL with inspect note, **NOT CRITICAL**

Scrub any real phone numbers from samples; use placeholders like `(555) 010-0142`.

## Export

One-click CSV with columns:
`Date,Customer,Phone,Vehicle,Requested Service,Status,Urgency,Missing Information,Next Action,Follow-up Draft,Original Message,AI Summary,Automation Status`

## Acceptance tests Freebuff must pass

1. Paste “I need brake pads on my 1987 RX7, call me back” → urgency ≠ CRITICAL; vehicle = 1987 Mazda RX-7; service mentions brake pads.
2. Paste Maria grinding + soft pedal → CRITICAL; draft mentions not driving / tow; status not sent.
3. Drafts never contain the words “column B”, “column C”, or “column D”.
4. “2014 hyuandai Tucson … catalytic converter pipe separated” → Hyundai Tucson + exhaust/flange repair + HIGH — INSPECT.
5. Approve button does not send anything; only flips local status.

Build the full runnable app now with README (how to open/run), seed data, and the Rules page.
