import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import google.generativeai as genai

# Load secrets from .streamlit/secrets.toml
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# App UI
st.set_page_config(page_title="Pakistan Govt Info Chatbot", layout="wide")
st.title("🇵🇰 Pakistan Government Info Chatbot")
st.markdown("Multilingual, Real-Time Updates from Federal and Provincial Ministries.")

# Initialize session state for chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Language choice (persistent)
if "lang" not in st.session_state:
    st.session_state.lang = "English"

st.session_state.lang = st.radio("Select Language / زبان منتخب کریں", ["English", "اردو"], index=0)

# All ministries, houses, and departments (federal and provincial)
gov_sources = {
    "PID": "http://pid.gov.pk/",
    "PM Office": "https://pmo.gov.pk/",
    "President House": "https://president.gov.pk/",
    "National Assembly": "https://na.gov.pk/",
    "Senate of Pakistan": "https://senate.gov.pk/",
    "Supreme Court": "https://www.supremecourt.gov.pk/",
    "Ministry of Finance": "https://www.finance.gov.pk/",
    "Ministry of Health": "https://nhsrc.gov.pk/",
    "Ministry of IT": "https://moitt.gov.pk/",
    "Ministry of Foreign Affairs": "https://mofa.gov.pk/",
    "Ministry of Education": "https://www.mofept.gov.pk/",
    "Ministry of Law": "http://molaw.gov.pk/",
    "Ministry of Energy": "https://www.mowp.gov.pk/",
    "Ministry of Human Rights": "http://mohr.gov.pk/",
    "Ministry of Climate Change": "https://mocc.gov.pk/",
    "Ministry of Industries": "https://moip.gov.pk/",
    "Ministry of Railways": "https://railways.gov.pk/",
    "Ministry of Defence": "https://mod.gov.pk/",
    "Ministry of Religious Affairs": "https://mora.gov.pk/",
    "NDMA": "http://www.ndma.gov.pk/",
    "ECP": "https://www.ecp.gov.pk/",
    "FBR": "https://fbr.gov.pk/",
    "NADRA": "https://www.nadra.gov.pk/",
    "PTA": "https://pta.gov.pk/",
    "HEC": "https://hec.gov.pk/",
    "Punjab Govt": "https://punjab.gov.pk/",
    "Sindh Govt": "https://sindh.gov.pk/",
    "KP Govt": "https://kp.gov.pk/",
    "Balochistan Govt": "https://balochistan.gov.pk/"
}

# Fetch latest updates from official websites
def fetch_updates():
    updates = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for name, url in gov_sources.items():
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            containers = soup.find_all(["li", "p", "div", "span", "a"], limit=100)
            for tag in containers:
                text = tag.get_text(strip=True)
                if not text or len(text) < 40:
                    continue
                if any(kw in text.lower() for kw in [
                    "prime minister", "president", "minister", "announcement",
                    "govt", "government", "update", "notice", "press release",
                    "notification", "cabinet", "policy", "development"]):
                    updates.append({
                        "source": name,
                        "url": url,
                        "text": text,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
        except:
            continue

    # Remove duplicates
    seen = set()
    unique_updates = []
    for u in updates:
        if u["text"] not in seen:
            unique_updates.append(u)
            seen.add(u["text"])

    return unique_updates[:50]

# Generate a Gemini response
def generate_response(query, updates, lang):
    update_text = "\n".join([f"{u['time']} - {u['source']}: {u['text']}" for u in updates])
    prompt = f"""
You are a real-time government update assistant for Pakistani citizens.

Use the updates below to answer user queries:

{update_text}

User Query: {query}
Language: {lang}

Instructions:
- Respond ONLY with real-time information from updates.
- Include date, time, and source.
- If no match is found, say "No relevant update found."
- Respond in {lang}.
"""
    model = genai.GenerativeModel("models/gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()

# Display past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if user_input := st.chat_input("Ask a question / سوال کریں"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("⏳ Fetching latest updates..."):
            updates = fetch_updates()
            if updates:
                reply = generate_response(user_input, updates, st.session_state.lang)
            else:
                reply = "⚠️ No recent updates available at the moment."
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
