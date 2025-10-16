import gspread
from google.oauth2.service_account import Credentials
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import json
import time

# Google Sheets Setup
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds_dict = json.load(open("credentials.json"))
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open("UserInput").sheet1

# Load Falcon Model
model_name = "tiiuae/falcon-7b-instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", torch_dtype="auto")
generator = pipeline("text-generation", model=model, tokenizer=tokenizer)

# Keep track of processed rows
processed_rows = 0

while True:
    all_records = sheet.get_all_records()
    new_records = all_records[processed_rows:]

    for i, record in enumerate(new_records, start=processed_rows + 2):  # +2 for header
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

        # Update Google Sheet (Column B = Emotion)
        sheet.update_cell(i, 2, emotion)
        print(f"Processed row {i}: {msg} -> {emotion}")

    processed_rows = len(all_records)
    time.sleep(10)  # Check for new messages every 10 seconds
