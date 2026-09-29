import streamlit as st

from api_client import compare_drift

st.set_page_config(page_title="Drift Comparison - DataGuard", layout="wide")
st.title(" Drift Comparison")

if "datasets" not in st.session_state or len(st.session_state["datasets"]) < 2:
    st.warning("You need at least 2 uploaded datasets to compare. Go to the Upload page first.")
    st.stop()

dataset_ids = list(st.session_state["datasets"].keys())

col1, col2 = st.columns(2)
with col1:
    baseline_id = st.selectbox(
        "Baseline dataset",
        options=dataset_ids,
        format_func=lambda x: f"{st.session_state['datasets'][x]} ({x[:8]}...)",
        key="baseline_select",
    )
with col2:
    current_id = st.selectbox(
        "Current dataset",
        options=dataset_ids,
        format_func=lambda x: f"{st.session_state['datasets'][x]} ({x[:8]}...)",
        index=min(1, len(dataset_ids) - 1),
        key="current_select",
    )

if baseline_id == current_id:
    st.warning("Select two different datasets to compare.")
    st.stop()

if st.button("Compare"):
    with st.spinner("Comparing datasets..."):
        try:
            result = compare_drift(baseline_id, current_id)
        except Exception as e:
            st.error(f"Comparison failed: {e}")
            st.stop()

    st.subheader("Numerical Drift")
    numerical_drift = result["numerical_drift"]
    if not numerical_drift:
        st.info("No shared numeric columns to compare.")
    for drift in numerical_drift:
        icon = "🔴" if drift["drift_detected"] else "🟢"
        with st.expander(f"{icon} {drift['column']} — {'Drift detected' if drift['drift_detected'] else 'No drift'}"):
            col1, col2 = st.columns(2)
            col1.metric("Baseline Mean", drift["baseline_mean"])
            col2.metric("Current Mean", drift["current_mean"], delta=f"{drift['relative_mean_change_pct']}%")
            st.caption(f"KS statistic: {drift['ks_statistic']} | p-value: {drift['ks_pvalue']}")
            st.write(drift["explanation"])

    st.subheader("Categorical Drift")
    categorical_drift = result["categorical_drift"]
    if not categorical_drift:
        st.info("No shared categorical columns to compare (excluding high-cardinality columns like IDs).")
    for drift in categorical_drift:
        icon = "🔴" if drift["drift_detected"] else "🟢"
        with st.expander(f"{icon} {drift['column']} — {'Drift detected' if drift['drift_detected'] else 'No drift'}"):
            st.caption(f"Jensen-Shannon divergence: {drift['js_divergence']}")
            if drift["new_categories"]:
                st.write("**New categories:**", ", ".join(drift["new_categories"]))
            if drift["removed_categories"]:
                st.write("**Removed categories:**", ", ".join(drift["removed_categories"]))
            st.write(drift["explanation"])

    summary = result["summary"]
    st.subheader("Summary")
    if summary["drift_detected"]:
        st.warning(f"Drift detected in: {', '.join(summary['columns_with_drift'])}")
    else:
        st.success("No significant drift detected.")
    st.caption(summary["note"])

    st.subheader("Schema Changes")
    schema = result["schema_comparison"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Added Columns", len(schema["added_columns"]))
    col2.metric("Removed Columns", len(schema["removed_columns"]))
    col3.metric("Row Count Change", schema["row_count_change"])
    if schema["added_columns"]:
        st.write("**Added:**", ", ".join(schema["added_columns"]))
    if schema["removed_columns"]:
        st.write("**Removed:**", ", ".join(schema["removed_columns"]))
    if schema["dtype_changes"]:
        st.write("**Data type changes:**")
        for change in schema["dtype_changes"]:
            st.write(f"- `{change['column']}`: {change['baseline_dtype']} → {change['current_dtype']}")