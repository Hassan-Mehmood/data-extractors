"""
Streamlit UI for the PDF-to-Excel extraction demo.

Run alongside the FastAPI server:
    uvicorn main:app --reload          # terminal 1 (port 8000)
    streamlit run streamlit_app.py     # terminal 2 (port 8501)
"""

import httpx
import streamlit as st

API_URL = "http://localhost:8000/api/pdf/extract"

st.set_page_config(
    page_title="PDF → Excel Extractor",
    page_icon="📊",
    layout="centered",
)

st.title("📊 PDF → Excel Extractor")
st.caption("Upload a text-based PDF with tables and download a formatted Excel file instantly.")

uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

if uploaded_file is not None:
    st.divider()
    if st.button("Extract Tables", type="primary", use_container_width=True):
        with st.spinner("Extracting tables — this may take a few seconds…"):
            try:
                response = httpx.post(
                    API_URL,
                    files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")},
                    timeout=120,
                )
            except httpx.ConnectError:
                st.error(
                    "Could not connect to the API server. "
                    "Make sure `uvicorn main:app --reload` is running on port 8000."
                )
                st.stop()

        if response.status_code == 200:
            data = response.json()
            st.success("Extraction complete!")

            col1, col2 = st.columns(2)
            col1.metric("Tables found", data["table_count"])
            col2.metric("Total data rows", data["total_rows"])

            dl_response = httpx.get(data["download_url"], timeout=30)
            if dl_response.status_code == 200:
                st.download_button(
                    label="⬇ Download Excel file",
                    data=dl_response.content,
                    file_name=data["filename"],
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            else:
                st.warning("Extraction succeeded but the file could not be retrieved for download.")
                st.write("Direct link:", data["download_url"])

        elif response.status_code == 422:
            detail = response.json().get("detail", "Unprocessable file.")
            st.error(f"**Cannot extract:** {detail}")
        elif response.status_code == 400:
            detail = response.json().get("detail", "Bad request.")
            st.error(f"**Invalid file:** {detail}")
        else:
            st.error(f"Unexpected error ({response.status_code}): {response.text}")

st.divider()
st.caption(
    "MVP scope: text-based PDFs only. Scanned / image-based PDFs require OCR (Phase 2). "
    "Powered by PyMuPDF + openpyxl."
)
