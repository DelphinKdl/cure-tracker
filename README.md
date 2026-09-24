# Cure Tracker

A decision-support prototype for tracking concrete curing progress on a construction site, built to demonstrate applied research into a real structural-quality method for a Field Engineer / Project Safety Assistant.

## The Problem

Structural formwork can't be stripped, and post-tension cables can't be stressed, until concrete reaches a target compressive strength (commonly 3,000-5,000 PSI). Site teams have historically relied on a fixed calendar wait (e.g., "strip after 7 days") as a conservative default. That default cuts both ways: it wastes schedule when warm curing conditions mean concrete actually reaches strength faster, and it risks structural failure if a team strips early based on assumption rather than evidence. The underlying question a site engineer actually needs answered isn't "how many days has it been," it's "has this specific pour, under its actual temperature history, reached strength yet."

## My Role

I researched, designed, and built this end to end as a solo project: identifying the real industry-standard technique used to answer this problem (the Nurse-Saul maturity method, ASTM C1074), translating its formula into working software, and making a deliberate engineering-judgment call on how the tool should represent its own authority (see "Challenges & Learning" below). I have no construction field background (M.Sc. Data Analytics), so this project doubled as self-directed domain research, verified against the published ASTM method rather than assumption.

## The Data

Each record tracks one concrete pour: a pour ID, its location (referenced against the structural grid used on real construction drawings, e.g. "Level 3, Grid C4-C6"), its target mix strength (3,000 / 4,000 / 5,000 PSI), and a time series of temperature readings taken after the pour. For this demo, temperature data is synthetic, generated to mimic a realistic hydration-heat curve (concrete runs hot right after pouring, then cools toward ambient over several days), clearly labeled as illustrative in the app itself. The data model mirrors what a real site team would actually log by hand or sensor, just without a live sensor feed behind it.

## Tools & Techniques

- **Python, Streamlit** for the interactive dashboard
- **Pandas / NumPy** for time-series and numerical calculation
- **Altair** for the strength-vs-time chart with a target-threshold reference line
- **openpyxl** for generating shareable Excel job-file reports
- **JSON flat-file persistence** so pour records survive across sessions without needing a database
- **ASTM C1074 / Nurse-Saul maturity method** as the core domain technique

## The Process

1. **Log** a pour (location, target strength, pour time), persisted immediately.
2. **Collect** temperature readings over the curing window (manual entry or sample data).
3. **Transform** readings into a cumulative maturity index using the Nurse-Saul formula: `M(t) = Σ (T_avg - T0) × Δt`.
4. **Model** estimated compressive strength from maturity, using an illustrative calibration curve (clearly labeled as synthetic, since no real lab-tested mix data exists for a demo).
5. **Visualize** estimated strength against the target PSI threshold over a 28-day curing window.
6. **Flag status**, explicitly as decision support, never as automated approval.
7. **Export** a shareable report (Excel/JSON) per pour, the artifact a site team would actually keep on file.

## Key Insights

- Temperature history drives strength gain, not calendar time. That's the entire reason the maturity method exists instead of a fixed-day rule.
- Higher-strength mixes need proportionally more accumulated maturity to hit their target, so a single wait time can't work across different mix designs.
- A badge that implies automated approval could mislead a crew into skipping a required engineering sign-off. The wording a decision-support tool uses carries real liability weight, not just UI polish.

## Business Impact

The maturity method exists industry-wide because it targets two costly failure modes on a schedule: stripping formwork too early (structural risk, rework, potential safety incident) and waiting longer than necessary (idle schedule float, delayed subsequent trades). A tool like this makes that trade-off visible and evidence-based instead of a guess. This build is a prototype, so I'm not claiming a measured dollar figure. What I can say directly: the decision it supports has real cost on both sides of getting the timing wrong, which is exactly why site teams use this method over a fixed calendar rule.

## Challenges & Learning

- **No field background.** Every domain term (PSI, grid references, EOR sign-off, PT-cable stressing) had to be researched and verified, not assumed. I ended up building a plain-language glossary into the app itself, partly for visitors, partly because I needed it to hold up under questioning.
- **The honesty boundary.** The hardest design decision wasn't the math, it was making sure the tool's own language never overstated its authority. A status badge reading "approved" instead of "pending EOR sign-off" would have misrepresented real liability, not just used weaker wording.
- **Persistence correctness.** An early version only saved a pour's data once temperature readings existed, silently losing records saved earlier in a session. Catching that taught me to verify state-persistence explicitly, save-then-reload, rather than trusting that a feature "looked like it worked" after one pass.
- **Verifying without guessing.** Rather than assuming the Nurse-Saul calculation was right, I hand-computed a reference case and asserted it in an automated test, then used Streamlit's own testing framework to run the full user flow end-to-end and catch runtime errors before calling anything done.

## Reflects Skills Aligned With

This project reflects skills directly aligned with the Field Engineer / Project Safety Assistant at a Construction company: independently researching a real structural-quality standard, translating it into a working field tool, and exercising the same judgment a site team needs, knowing precisely where data-driven insight ends and licensed engineering authority begins.

---

## Running It

```bash
pip install -r requirements.txt
streamlit run app.py
```

Runs fully offline, no external API or network dependency. Optional: `python seed_pour_log.py` populates `pour_log.json` with sample historical pours for a populated demo.
