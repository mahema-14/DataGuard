import streamlit as st

from api_client import upload_dataset

st.set_page_config(page_title="Upload - DataGuard", layout="wide")
st.title(" Upload Dataset")

if "datasets" not in st.session_state:
    st.session_state["datasets"] = {}

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    if st.button("Upload and Analyze"):
        with st.spinner("Uploading and validating..."):
            try:
                result = upload_dataset(uploaded_file)
                st.session_state["datasets"][result["dataset_id"]] = result["original_filename"]
                st.session_state["last_uploaded_id"] = result["dataset_id"]
                st.success(f"Uploaded successfully! Dataset ID: `{result['dataset_id']}`")
                st.json(result)
            except Exception as e:
                st.error(f"Upload failed: {e}")

if st.session_state["datasets"]:
    st.divider()
    st.subheader("Previously uploaded (this session)")
    for dataset_id, filename in st.session_state["datasets"].items():
        st.write(f"`{dataset_id}` — {filename}")