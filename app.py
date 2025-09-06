import streamlit as st

st.title("Life 3.0 Audiobook Generator")
st.write("🚀 Your Streamlit app is running on Vercel!")

pdf_file = st.file_uploader("Upload Life 3.0 PDF", type="pdf")
if pdf_file:
    st.success("PDF uploaded successfully!")
