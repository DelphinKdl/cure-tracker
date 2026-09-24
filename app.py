"""Cure Tracker: offline concrete pour log and maturity curve demo."""

import json
from datetime import datetime, timedelta

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from maturity import DEFAULT_DATUM_TEMP_F, estimate_strength_psi, nurse_saul_maturity
from pour_log import build_excel_report, load_pours, next_pour_number, save_pour

MIX_DESIGNS_PSI = [3000, 4000, 5000]
CURING_WINDOW_DAYS = 28
EMPTY_READINGS = pd.DataFrame({"timestamp": pd.Series(dtype="datetime64[ns]"), "temp_f": pd.Series(dtype=float)})


def generate_sample_readings(start_dt: datetime) -> pd.DataFrame:
    """Synthetic temperature curve: hydration-heat decay, then a mild daily cycle."""
    rng = np.random.default_rng(42)
    ambient_f = 72.0
    peak_extra_f = 23.0

    timestamps: list[datetime] = []
    temps_f: list[float] = []

    for h in range(0, 49):
        temp = ambient_f + peak_extra_f * np.exp(-h / 18.0) + rng.normal(0, 0.8)
        timestamps.append(start_dt + timedelta(hours=h))
        temps_f.append(round(float(temp), 1))

    for h in range(54, 24 * 7 + 1, 6):
        temp = ambient_f + 4.0 * np.sin(2 * np.pi * h / 24.0) + rng.normal(0, 1.2)
        timestamps.append(start_dt + timedelta(hours=h))
        temps_f.append(round(float(temp), 1))

    for h in range(24 * 7 + 24, 24 * CURING_WINDOW_DAYS + 1, 24):
        temp = ambient_f + 3.0 * np.sin(2 * np.pi * h / 24.0) + rng.normal(0, 1.5)
        timestamps.append(start_dt + timedelta(hours=h))
        temps_f.append(round(float(temp), 1))

    return pd.DataFrame({"timestamp": timestamps, "temp_f": temps_f})


def status_badge(current_psi: float, target_psi: float) -> None:
    """Exact wording required: never claim stripping is 'approved'; only EOR can."""
    if current_psi >= target_psi:
        st.success("**Maturity threshold reached, Pending EOR sign-off**")
    else:
        st.warning("**Curing, Below target strength**")


def render_pour_form() -> dict | None:
    """Pour log entry form. Saves to disk immediately on submit (metadata only, before
    any readings exist), so it never depends on later steps to be persisted."""
    st.subheader("1. Pour Log")
    with st.form("pour_form"):
        col1, col2 = st.columns(2)
        with col1:
            location = st.text_input(
                "Location",
                value="Level 3, Slab, Grid C4-C6",
                help="Where on the job site this concrete was poured. \"Grid C4-C6\" refers to "
                "the lettered/numbered reference grid on the building's structural drawings, "
                "like a map coordinate for the floor plan.",
            )
            mix_design_psi = st.selectbox(
                "Mix Design (Target Strength in PSI)",
                MIX_DESIGNS_PSI,
                index=0,
                help="PSI (pounds per square inch) measures how much crushing force the concrete "
                "can withstand. This is the strength it needs to reach before crews can move on "
                "to the next step (like removing forms).",
            )
        with col2:
            pour_date = st.date_input("Pour Date", value=datetime.now().date())
            pour_time = st.time_input("Pour Time", value=datetime.now().time().replace(second=0, microsecond=0))

        if st.form_submit_button("Save Pour Log"):
            pour_dt = datetime.combine(pour_date, pour_time)
            st.session_state.pour = {
                "pour_id": f"P-{st.session_state.next_pour_id:03d}",
                "location": location,
                "target_psi": mix_design_psi,
                "pour_datetime": pour_dt,
            }
            st.session_state.next_pour_id += 1
            st.session_state.readings = EMPTY_READINGS.copy()
            save_pour(st.session_state.pour, st.session_state.readings)

    return st.session_state.pour


def render_readings_section(pour: dict) -> pd.DataFrame | None:
    """Temperature readings for the active pour. Returns readings once there are
    enough (>=2) to compute a maturity curve, else None."""
    st.markdown(
        f"**Pour ID:** {pour['pour_id']}  |  **Location:** {pour['location']}  |  "
        f"**Target Strength:** {pour['target_psi']} PSI  |  "
        f"**Pour Time:** {pour['pour_datetime']:%Y-%m-%d %H:%M}"
    )

    st.subheader("2. Temperature Readings")
    st.caption(
        "This is made-up sample data for the demo, not a real sensor log. "
        "Type in your own readings below, or click the button for auto-filled sample data."
    )

    if st.button("Generate sample readings"):
        st.session_state.readings = generate_sample_readings(pour["pour_datetime"])

    edited = st.data_editor(
        st.session_state.readings,
        num_rows="dynamic",
        width="stretch",
        height=250,
        column_config={
            "timestamp": st.column_config.DatetimeColumn("Timestamp", step=3600),
            "temp_f": st.column_config.NumberColumn("Temp (°F)", min_value=-20.0, max_value=200.0, step=0.5),
        },
        key="readings_editor",
    )
    st.session_state.readings = edited

    readings = edited.dropna().copy()
    if readings.empty or len(readings) < 2:
        st.info("Add at least two temperature readings (or click 'Generate sample readings') to see the maturity curve.")
        return None

    save_pour(pour, readings)
    return readings


def render_chart_and_status(pour: dict, readings: pd.DataFrame) -> None:
    st.subheader("3. Estimated Strength Development")
    st.caption(
        "This chart uses a made-up sample curve to turn temperature into an estimated PSI, "
        "not a real lab-tested calibration. Below "
        f"{DEFAULT_DATUM_TEMP_F:.0f}°F, concrete is assumed to gain no strength (the \"datum\" cutoff)."
    )

    maturity_df = nurse_saul_maturity(readings)
    maturity_df["elapsed_days"] = maturity_df["elapsed_hours"] / 24.0
    maturity_df["estimated_psi"] = estimate_strength_psi(
        maturity_df["maturity_degree_hours"].to_numpy(), pour["target_psi"]
    )
    maturity_df = maturity_df[maturity_df["elapsed_days"] <= CURING_WINDOW_DAYS]

    target_psi = pour["target_psi"]
    line = (
        alt.Chart(maturity_df)
        .mark_line(point=True, color="#1f77b4")
        .encode(
            x=alt.X("elapsed_days", title="Days Since Pour", scale=alt.Scale(domain=[0, CURING_WINDOW_DAYS])),
            y=alt.Y("estimated_psi", title="Estimated Compressive Strength (PSI)"),
            tooltip=["elapsed_days", "estimated_psi", "maturity_degree_hours"],
        )
    )
    target_rule = (
        alt.Chart(pd.DataFrame({"target_psi": [target_psi]}))
        .mark_rule(color="red", strokeDash=[6, 4])
        .encode(y="target_psi")
    )
    st.altair_chart((line + target_rule).properties(height=380), width="stretch")

    current_psi = float(maturity_df["estimated_psi"].iloc[-1])
    st.subheader("4. Status")
    status_badge(current_psi, target_psi)
    st.caption(f"Latest estimated strength: {current_psi:,.0f} PSI vs. target {target_psi:,.0f} PSI.")


def render_pour_log_section(active_pour: dict | None) -> None:
    """Always renders from disk (pour_log.json), independent of session/form state,
    so a page refresh or a new visitor never hides previously saved records."""
    st.subheader("5. Pour Log")
    st.caption("Every saved pour, persisted locally to pour_log.json. Select a row to export its report.")

    history = load_pours()
    if not history:
        st.info("No pours saved yet. Log one above to start building the record.")
        return

    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Pour ID": p["pour_id"],
                    "Location": p["location"],
                    "Target PSI": p["target_psi"],
                    "Pour Date/Time": datetime.fromisoformat(p["pour_datetime"]).strftime("%b %d, %Y %I:%M %p"),
                    "Readings Logged": len(p["readings"]),
                }
                for p in history
            ]
        ),
        width="stretch",
    )

    pour_ids = [p["pour_id"] for p in history]
    default_id = active_pour["pour_id"] if active_pour and active_pour["pour_id"] in pour_ids else pour_ids[-1]
    selected_id = st.selectbox("Pour:", pour_ids, index=pour_ids.index(default_id))
    selected = next(p for p in history if p["pour_id"] == selected_id)
    selected_readings = pd.DataFrame(selected["readings"])

    col_a, col_b = st.columns(2)
    with col_a:
        if len(selected_readings) >= 2:
            selected_pour = {
                "pour_id": selected["pour_id"],
                "location": selected["location"],
                "target_psi": selected["target_psi"],
                "pour_datetime": datetime.fromisoformat(selected["pour_datetime"]),
            }
            selected_maturity = nurse_saul_maturity(selected_readings)
            selected_maturity["estimated_psi"] = estimate_strength_psi(
                selected_maturity["maturity_degree_hours"].to_numpy(), selected["target_psi"]
            )
            st.download_button(
                f"Download {selected_id} report (Excel)",
                data=build_excel_report(selected_pour, selected_maturity),
                file_name=f"{selected_id}_cure_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.caption(f"{selected_id} has fewer than 2 readings; not enough data for a report yet.")
    with col_b:
        st.download_button(
            "Download full pour log (JSON)",
            data=json.dumps(history, indent=2),
            file_name="pour_log.json",
            mime="application/json",
        )


def main() -> None:
    st.set_page_config(page_title="Cure Tracker", layout="wide")

    st.title("Cure Tracker")
    st.write(
        "Wet concrete needs time to harden before crews can remove the wooden forms around it "
        "or tension the steel cables inside it. Cure Tracker estimates how far along that "
        "hardening process is, using the temperature of the concrete over time, so a site team "
        "knows roughly when it's worth checking with an engineer instead of just waiting a fixed "
        "number of days."
    )
    st.caption(
        "Runs fully offline. This tool estimates strength, it does not approve stripping or "
        "PT-cable stressing; that decision requires engineer-of-record (EOR) sign-off."
    )
    with st.expander("New to construction terms? Quick definitions"):
        st.markdown(
            "- **PSI (pounds per square inch):** the unit used to measure concrete strength, "
            "how much crushing force a square inch of it can take before failing. Higher PSI = "
            "stronger, denser concrete, usually required for heavier loads.\n"
            "- **Curing:** the hardening process concrete goes through over days/weeks as a "
            "chemical reaction (not just drying) makes it stronger.\n"
            "- **Grid reference (e.g. 'Grid C4-C6'):** construction drawings overlay a grid of "
            "lettered/numbered lines on the building so crews can point to an exact spot "
            "(like a spreadsheet cell reference, but for a floor plan).\n"
            "- **PT-cable stressing:** tensioning steel cables cast inside the concrete "
            "(post-tensioning) to add strength; also can't happen until the concrete is strong enough.\n"
            "- **EOR (Engineer of Record):** the licensed engineer legally responsible for the "
            "structural design; only they can sign off on stripping formwork or stressing cables.\n"
            "- **Maturity method / Nurse-Saul / ASTM C1074:** an industry-standard way to estimate "
            "concrete strength from its temperature history instead of guessing based on days elapsed. "
            "ASTM C1074 is the published standard that defines how to do this."
        )

    if "next_pour_id" not in st.session_state:
        st.session_state.next_pour_id = next_pour_number()
    if "pour" not in st.session_state:
        st.session_state.pour = None
    if "readings" not in st.session_state:
        st.session_state.readings = EMPTY_READINGS.copy()

    pour = render_pour_form()

    if pour is None:
        st.info("Log a pour above to begin tracking maturity.")
    else:
        readings = render_readings_section(pour)
        if readings is not None:
            render_chart_and_status(pour, readings)

    render_pour_log_section(pour)


if __name__ == "__main__":
    main()
