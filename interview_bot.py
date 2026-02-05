import streamlit as st
import google.generativeai as genai
import json
import pandas as pd

st.set_page_config(page_title="IIMN Interview Debrief", page_icon="🎙️")

# --- SIDEBAR ---
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

st.title("🎙️ IIMN Interview Voice Collector")
st.markdown("**Record your experience. AI fills the form.**")

# --- INPUT ---
tab1, tab2 = st.tabs(["🔴 Record", "📂 Upload"])
audio_file = None

with tab1:
    recorded_audio = st.audio_input("Click to Record")
    if recorded_audio:
        audio_file = recorded_audio
with tab2:
    uploaded_file = st.file_uploader("Upload Audio", type=["mp3", "wav", "m4a", "ogg"])
    if uploaded_file:
        audio_file = uploaded_file

# --- LOGIC ---
if audio_file and st.button("Process Experience"):
    if not api_key:
        st.error("⚠️ API Key is missing.")
    else:
        try:
            with st.spinner("Connecting to AI..."):
                genai.configure(api_key=api_key)
                
                # --- AUTO-DETECT AUDIO MODEL ---
                # We specifically look for 1.5 models because the old 'gemini-pro' CANNOT hear audio.
                active_model = "models/gemini-1.5-flash" # Default target
                
                found_models = [m.name for m in genai.list_models()]
                
                # Try to find the best match in the user's available models
                if 'models/gemini-1.5-flash' in found_models:
                    active_model = 'models/gemini-1.5-flash'
                elif 'models/gemini-1.5-pro' in found_models:
                    active_model = 'models/gemini-1.5-pro'
                
                # st.write(f"Using Model: {active_model}") # Uncomment to debug
                model = genai.GenerativeModel(active_model)
                
                # Process Audio
                audio_bytes = audio_file.read()
                
                prompt = """
                Extract the following details from the interview audio into JSON format:
                {
                    "Candidate_Name": "Name or Anonymous",
                    "Company": "Company Name",
                    "Role_Offered": "Role",
                    "Round_Type": "Technical/HR/Case",
                    "Questions_Asked": ["List of questions..."],
                    "Preparation_Tips": "Tips mentioned"
                }
                Return ONLY JSON.
                """
                
                response = model.generate_content([
                    prompt,
                    {"mime_type": "audio/mp3", "data": audio_bytes}
                ])
                
                # Parse JSON
                json_text = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(json_text)
                
                st.success("✅ Extracted!")
                st.json(data)
                
                # Download
                df = pd.DataFrame([data])
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download CSV", csv, "interview_data.csv", "text/csv")

        except Exception as e:
            st.error(f"Error: {e}")
            st.warning("If you see a 404 error, PLEASE run: 'pip install --upgrade google-generativeai' in your terminal.")
