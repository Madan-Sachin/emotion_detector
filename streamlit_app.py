import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

st.set_page_config(page_title="Message Collector", page_icon="💬", layout="centered")
st.title("💬 Message Collector")

# Google Sheets Setup
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

try:
    creds_dict = dict(st.secrets["gcp"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open("UserInput").sheet1
except Exception as e:
    st.error(f"❌ Error connecting to Google Sheets: {e}")
    st.stop()

# User Input
msg = st.text_input("Enter your message:")

if st.button("Submit"):
    if msg.strip():
        sheet.append_row([msg])
        st.success("✅ Message saved!")
    else:
        st.warning("Please enter a message before submitting.")

# Show all messages
st.subheader("📋 Submitted Messages")
try:
    records = sheet.get_all_records()
    if records:
        st.dataframe(pd.DataFrame(records))
    else:
        st.write("No messages yet.")
except Exception as e:
    st.error(f"Error reading messages: {e}")
