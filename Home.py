import streamlit as st
import pandas

st.set_page_config(layout="wide",
                   page_title="101L Tools - Home")

st.title("101L Tools")
st.write("Welcome. Please select a tool from the sidebar or below:")

st.subheader("Available Tools")
st.markdown("[Grade Visualizer](/Grade_Visualizer)")
st.markdown("[Sheet Printer](/Sheet_Printer)")