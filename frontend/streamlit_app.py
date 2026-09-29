import streamlit as st

from api_client import check_health

st.set_page_config(page_title="DataGuard", layout="wide")

st.title(" DataGuard")
st.caption("Intelligent Data Quality and Dataset Drift Detection Platform")

if check_health():
    st.success(" Backend is connected and healthy.")
else:
    st.error(
        " Cannot reach the backend API. "
        "Make sure it's running: `uvicorn backend.app.main:app --reload`"
    )

st.markdown(
    """
    ### What DataGuard does
    Upload a CSV dataset to get:
    - A complete profile of your data
    - Automatically detected quality issues, explained in plain language
    - A transparent, weighted quality score
    - Drift comparison between two dataset versions

    Use the sidebar to navigate between pages once more are added.
    """
)