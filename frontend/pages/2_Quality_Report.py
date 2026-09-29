import streamlit as st
import plotly.express as px
import pandas as pd
import json
from api_client import get_quality_report, get_dataset_profile

st.set_page_config(page_title="Quality Report - DataGuard", layout="wide")
st.title(" Quality Report")

if "datasets" not in st.session_state or not st.session_state["datasets"]:
    st.warning("No datasets uploaded yet. Go to the Upload page first.")
    st.stop()

dataset_id = st.selectbox(
    "Select a dataset",
    options=list(st.session_state["datasets"].keys()),
    format_func=lambda x: f"{st.session_state['datasets'][x]} ({x[:8]}...)",
    index=list(st.session_state["datasets"].keys()).index(
        st.session_state.get("last_uploaded_id", list(st.session_state["datasets"].keys())[0])
    ),
)

with st.spinner("Fetching quality report..."):
    try:
        report = get_quality_report(dataset_id)
        profile = get_dataset_profile(dataset_id)
    except Exception as e:
        st.error(f"Failed to fetch report: {e}")
        st.stop()

st.download_button(
    label=" Download Report (JSON)",
    data=json.dumps(report, indent=2),
    file_name=f"dataguard_quality_report_{dataset_id[:8]}.json",
    mime="application/json",
)

score = report["quality_score"]

st.subheader("Overview")
col1, col2, col3 = st.columns(3)
col1.metric("Rows", profile["num_rows"])
col2.metric("Columns", profile["num_columns"])
col3.metric("Duplicate Rows", profile["duplicate_row_count"])

st.subheader("Quality Score")
st.metric("Overall Score", f"{score['overall_score']} / 100")
st.caption(score["note"])

sub_cols = st.columns(5)
sub_score_labels = {
    "completeness": "Completeness",
    "validity": "Validity",
    "uniqueness": "Uniqueness",
    "consistency": "Consistency",
    "outlier_health": "Outlier Health",
}
for col, (key, label) in zip(sub_cols, sub_score_labels.items()):
    col.metric(label, f"{score['sub_scores'][key]}")
    
st.divider()
st.subheader("Detected Issues")

issues = report["issues"]

if not issues:
    st.info("No quality issues detected.")
else:
    severity_order = {"critical": 0, "warning": 1, "informational": 2}
    severity_icons = {"critical": "🔴", "warning": "🟡", "informational": "🔵"}
    sorted_issues = sorted(issues, key=lambda i: severity_order.get(i["severity"], 99))

    for issue in sorted_issues:
        icon = severity_icons.get(issue["severity"], "⚪")
        column_label = f" — `{issue['column']}`" if issue["column"] else ""
        with st.expander(f"{icon} {issue['severity'].upper()}: {issue['issue_type']}{column_label}"):
            st.write(issue["explanation"])
            st.markdown(f"**Recommendation:** {issue['recommendation']}")
            if issue["measured_value"] is not None:
                st.caption(f"Measured value: {issue['measured_value']}  |  Threshold: {issue['threshold']}")   

st.divider()
st.subheader("Column Profiling")

profile_rows = []
for column in profile["column_names"]:
    missing = profile["missing_statistics"][column]
    row = {
        "Column": column,
        "Missing %": missing["missing_percentage"],
    }
    if column in profile["numeric_statistics"]:
        stats = profile["numeric_statistics"][column]
        row.update({"Type": "Numeric", "Mean": stats["mean"], "Std": stats["std"], "Min": stats["min"], "Max": stats["max"]})
    else:
        cat_stats = profile["categorical_statistics"][column]
        row.update({"Type": "Categorical", "Unique %": cat_stats["unique_percentage"]})
    profile_rows.append(row)

st.dataframe(pd.DataFrame(profile_rows), use_container_width=True)

st.divider()
st.subheader("Distributions")

numeric_columns = list(profile["numeric_statistics"].keys())
categorical_columns = [
    c for c in profile["categorical_statistics"].keys()
    if profile["categorical_statistics"][c]["unique_percentage"] < 50
]

if numeric_columns:
    from api_client import get_column_values

    selected_numeric = st.selectbox("Numeric column", numeric_columns, key="numeric_col_select")
    stats = profile["numeric_statistics"][selected_numeric]
    st.caption(
        f"Mean: {stats['mean']} | Median: {stats['median']} | Std: {stats['std']} | "
        f"Min: {stats['min']} | Max: {stats['max']}"
    )
    try:
        values_result = get_column_values(dataset_id, selected_numeric)
        fig = px.histogram(x=values_result["values"], nbins=15, title=f"Distribution of '{selected_numeric}'")
        fig.update_layout(xaxis_title=selected_numeric, yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not load distribution chart: {e}")

if categorical_columns:
    selected_cat = st.selectbox("Categorical column", categorical_columns, key="cat_col_select")
    cat_stats = profile["categorical_statistics"][selected_cat]
    top_values = cat_stats["top_values"]
    if top_values:
        chart_df = pd.DataFrame(top_values, columns=["Value", "Count"])
        fig = px.bar(chart_df, x="Value", y="Count", title=f"Top values in '{selected_cat}'")
        st.plotly_chart(fig, use_container_width=True)                 
                