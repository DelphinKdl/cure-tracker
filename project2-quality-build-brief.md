# Build Brief: Concrete Pour Log & Maturity Curve Tracker
**For: Devin**
**Owner: Delphin Kaduli**
**Deadline: working demo by end of day 2026-09-24, this is for a career fair booth demo at Turner Construction on 2026-09-25.**

## Context

I'm a data/analytics professional (M.Sc. Data Analytics, no construction field experience) applying to entry-level Field Engineer / Project Safety Assistant roles at Turner Construction. I'm building this as a live demo to show at their career fair booth, not a production app, a prototype that proves I researched a real structural-quality technique and can turn it into a usable field tool.

**The real problem this solves:** site engineers manage concrete pours. Structural formwork can't be stripped, and post-tension cables can't be stressed, until the concrete reaches a target compressive strength (e.g., 3,000 PSI). Waiting too long wastes schedule; stripping too early risks structural failure. Site teams use temperature-based "maturity" methods to estimate strength development over time instead of just waiting a fixed number of days.

## Hard constraints, read before building

1. **No live LLM/AI API calls, no internet dependency.** This will be demoed live on a laptop, possibly without reliable wifi. Everything must run fully offline on local data and math, no external API calls of any kind.
2. **Single-file or small Streamlit app** (`app.py` + maybe a small helper module). Python, Streamlit, matplotlib or Plotly for the chart. Keep dependencies minimal.
3. **Must run in under 90 seconds for a full demo walkthrough.**
4. **Critical honesty requirement, do not skip this:** the app must NOT claim to "approve" formwork stripping on its own. In real projects, stripping approval requires an **engineer-of-record (EOR) sign-off**, not just a math threshold. The status badge must say **"Maturity threshold reached, pending EOR sign-off"**, never "APPROVED FOR STRIPPING." This matters: if a real Turner engineer asks how stripping decisions actually work, the app's own language needs to already be correct, not something I have to walk back.
5. **Label all data as synthetic.** Any calibration curve or sample dataset must be visibly labeled "illustrative / sample data, not from an actual tested mix design" somewhere in the UI. Don't let it look like real lab data.

## Plan

**Goal:** A Streamlit dashboard that lets a user log concrete pour data and temperature readings, and visually estimates strength development over a ~28-day curing window using the Nurse-Saul maturity method, clearly framed as a decision-support tool, not an automated approval system.

**Non-goals:** No real calibration data (none exists for this, it's illustrative), no claim of engineering authority, no persistence required beyond the session (in-memory is fine).

## Build spec

### The real technique to implement: Nurse-Saul maturity method (ASTM C1074)
Maturity index formula:

```
M(t) = Σ (T_a − T₀) × Δt
```

Where:
- `T_a` = average concrete temperature during a time interval (°F or °C, pick one and be consistent)
- `T₀` = datum temperature, commonly 14°F (−10°C), use this as the default
- `Δt` = length of the time interval (hours)
- `M(t)` = cumulative maturity index (degree-hours) at time `t`

### What to build

1. **Pour log form:**
   - Pour ID (text/auto-increment)
   - Location (text, e.g. "Level 3, Slab, Grid C4-C6")
   - Mix Design, target compressive strength: dropdown of 3,000 / 4,000 / 5,000 PSI
   - Pour Date/Time
   - A way to log periodic temperature readings after the pour (e.g., a small table: timestamp, ambient/concrete temperature in °F), for the demo, allow either manual entry of a few readings OR a "generate sample readings" button that fills in a plausible synthetic temperature curve so the demo doesn't require typing 20 rows live at the booth.

2. **Maturity calculation:** implement the Nurse-Saul formula above in Python, computing cumulative maturity index over time from the logged temperature readings.

3. **Synthetic strength-maturity calibration curve:** since no real lab calibration data exists for this demo, build a simple illustrative function that maps maturity index → estimated compressive strength (e.g., a logarithmic curve that plausibly reaches the target PSI around a realistic timeframe like 3-7 days for typical mixes). **Label this clearly in the UI as "Sample calibration curve, illustrative only, not from tested mix data."**

4. **Live chart:** plot estimated compressive strength vs. time (up to 28 days) as temperature readings are logged, with a horizontal reference line at the target PSI for the selected mix design.

5. **Status badge, exact wording required:**
   - While below threshold: "Curing, below target strength"
   - Once maturity-based estimate crosses the target PSI: **"Maturity threshold reached, pending EOR sign-off"** (do not use "approved," "cleared," "ready to strip," or similar language anywhere in the UI)

### Visual style
- Clean dashboard layout: pour details at top, chart in the middle, status badge prominent but using the exact wording above.
- Keep text minimal and legible from a few feet away.

## Execution steps (build in this order)

1. Build the pour log form and data model (Pour ID, Location, Mix Design, Pour Date, temperature readings list).
2. Implement the Nurse-Saul maturity calculation as a standalone, testable function.
3. Build the synthetic calibration curve function (maturity index → estimated PSI) and clearly label it as illustrative.
4. Build the live chart (strength estimate vs. time, with target-PSI reference line).
5. Implement the status badge with the exact required wording, double check no stronger claim ("approved") appears anywhere.
6. Add the "generate sample readings" convenience button so the demo doesn't require live data entry of many rows.
7. Full timed run-through of the demo flow, cold. Should take under 90 seconds (log a pour → generate sample readings → see the chart update → see the badge). Fix anything slow or confusing.
8. Freeze by 2026-09-24. Confirm it runs fully offline.

## Acceptance criteria (test before calling this done)
- [ ] Nurse-Saul calculation is mathematically correct for a hand-checkable test case (verify by computing one example by hand and comparing).
- [ ] The badge NEVER says "approved" or implies automated stripping authorization anywhere in the UI, only "Maturity threshold reached, pending EOR sign-off."
- [ ] The calibration curve is visibly labeled as illustrative/sample data in the UI, not presented as real.
- [ ] Chart updates correctly as temperature readings are added.
- [ ] Full demo flow completes in under 90 seconds using the "generate sample readings" shortcut.
- [ ] App runs with no internet connection.
- [ ] No crashes across a few different mix-design/target-PSI selections.

## Demo pitch (for reference, not part of the app itself)
"I researched the Nurse-Saul maturity method that structural teams use to time formwork stripping, and built a dashboard that logs pour data and temperature readings and estimates strength development over the curing window. It's a decision-support tool, not a replacement for the engineer-of-record sign-off that real stripping decisions require, I wanted to understand how site teams balance schedule pressure against structural risk, since that trade-off is at the center of a lot of quality decisions on a job site."
