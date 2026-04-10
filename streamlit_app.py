import httpx
import streamlit as st

AI_API_URL = "http://localhost:8000/api/pdf/extract-ai"

st.set_page_config(
    page_title="AI PDF Data Extractor",
    page_icon="🤖",
    layout="centered",
)

st.title("🤖 AI PDF Data Extractor")
st.caption(
    "Upload a PDF and describe what data you want to extract. "
    "The AI will read the document and return a structured Excel file."
)

uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

prompt = st.text_area(
    "Extraction prompt",
    placeholder=(
        "Describe what to extract, e.g.:\n"
        "  • Extract all invoice numbers, dates, vendor names, and total amounts.\n"
        "  • Pull every person's name, title, and email address.\n"
        "  • List all product names, SKUs, and prices."
    ),
    height=130,
)

st.divider()

extract_ready = uploaded_file is not None and prompt.strip() != ""

if st.button(
    "Extract with AI",
    type="primary",
    use_container_width=True,
    disabled=not extract_ready,
):
    with st.spinner("Sending document to AI — this may take a few seconds…"):
        try:
            response = httpx.post(
                AI_API_URL,
                files={
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        "application/pdf",
                    )
                },
                data={"prompt": prompt},
                timeout=180,
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
        col1.metric("Rows extracted", data["row_count"])
        col2.metric("Fields found", len(data["fields"]))

        st.write("**Extracted fields:**", ", ".join(data["fields"]))

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
            st.warning("Extraction succeeded but the file could not be retrieved.")
            st.write("Direct link:", data["download_url"])

    elif response.status_code == 422:
        detail = response.json().get("detail", "Unprocessable file or no data found.")
        st.error(f"**Extraction failed:** {detail}")
    elif response.status_code == 400:
        detail = response.json().get("detail", "Bad request.")
        st.error(f"**Invalid input:** {detail}")
    elif response.status_code == 500:
        detail = response.json().get("detail", "Server error.")
        st.error(f"**Server error:** {detail}")
    else:
        st.error(f"Unexpected error ({response.status_code}): {response.text}")

elif not extract_ready and uploaded_file is not None:
    st.info("Enter an extraction prompt above to enable the button.")
elif not extract_ready and prompt.strip():
    st.info("Upload a PDF file above to enable the button.")

st.divider()
st.caption("Powered by LangChain + OpenAI gpt-4o-mini + PyMuPDF + openpyxl.")
