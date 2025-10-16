import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import threading
import time
import json

# ------------------------
# Falcon setup
# ------------------------
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
model_name = "tiiuae/falcon-7b-instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", torch_dtype="auto")
generator = pipeline("text-generation", model=model, tokenizer=tokenizer)

# ------------------------
# Google Sheets Setup
# ------------------------
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds_dict = dict(st.secrets["gcp"])
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open("UserInput").sheet1  # Replace with your sheet name

# ------------------------
# Background thread flag
# ------------------------
stop_thread = False

def monitor_sheet():
    global stop_thread
    processed_rows = 0
    while not stop_thread:
        all_records = sheet.get_all_records()
        new_records = all_records[processed_rows:]
        
        for i, record in enumerate(new_records, start=processed_rows + 2):
            msg = record["Message"]
            prompt = f"""
            You are an assistant that detects emotions. Only return one of these emotions: happy, love, sad, anger.
            Analyze the text and return the result as a JSON object with the key 'emotion'.
            Text: "{msg}"
            JSON output:
            """
            output = generator(prompt, max_new_tokens=50, do_sample=False)[0]["generated_text"]
            try:
                json_part = output.split("JSON output:")[-1].strip()
                emotion = json.loads(json_part).get("emotion", "neutral")
            except:
                emotion = "neutral"
            
            sheet.update_cell(i, 2, emotion)
        
        processed_rows = len(all_records)
        time.sleep(2)  # check every 2 seconds

# ------------------------
# Start background thread once
# ------------------------
if "thread_started" not in st.session_state:
    st.session_state.thread_started = True
    threading.Thread(target=monitor_sheet, daemon=True).start()

# ------------------------
# Streamlit UI
# ------------------------
st.title("💬 Real-Time Emotion Detector")

msg = st.text_input("Enter your message:")

if st.button("Submit"):
    if msg.strip():
        sheet.append_row([msg])
        st.success("✅ Message saved!")
    else:
        st.warning("Please enter a message.")

# ------------------------
# Live Emotion Display
# ------------------------
st.subheader("📋 Messages and Emotions")

while True:
    records = sheet.get_all_records()
    if records:
        df = pd.DataFrame(records)
        st.dataframe(df)
    else:
        st.write("No messages yet.")
    
    # Stop loop if user clicks the stop button
    if st.button("Stop Emotion Processing"):
        stop_thread = True
        st.warning("⚠️ Emotion processing stopped.")
        break
    
    time.sleep(3)
