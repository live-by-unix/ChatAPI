import streamlit as st
import openai
import anthropic
import google.generativeai as genai
import requests
import json
import os

CONFIG_FILE = "ai_config.json"

def save_prefs(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

def load_prefs():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

st.set_page_config(page_title="Universal AI Hub", layout="wide")
if "messages" not in st.session_state:
    st.session_state.messages = []

prefs = load_prefs()

with st.sidebar:
    st.title("⚙️ AI Settings")
    
    providers = ["OpenAI", "Anthropic", "Google Gemini", "Groq", "Hugging Face", "RapidAPI", "MS Copilot/Azure"]
    
    saved_p = prefs.get("provider", "OpenAI")
    p_index = providers.index(saved_p) if saved_p in providers else 0
    
    provider = st.selectbox("Provider", providers, index=p_index)
    api_key = st.text_input("API Key", value=prefs.get("key", ""), type="password")
    
    if provider == "RapidAPI":
        model_or_url = st.text_input("Full Request URL", value=prefs.get("model", ""), placeholder="https://api-name.p.rapidapi.com/v1/chat/completions")
        st.caption("⚠️ Paste the FULL URL from RapidAPI 'Endpoints' tab.")
    elif provider == "Hugging Face":
        model_or_url = st.text_input("Model ID", value=prefs.get("model", ""), placeholder="meta-llama/Llama-3.1-8B")
    elif provider == "MS Copilot/Azure":
        model_or_url = st.text_input("Endpoint URL", value=prefs.get("model", ""))
    else:
        model_or_url = st.text_input("Model Name", value=prefs.get("model", ""))

    if st.button("💾 Save Configuration"):
        save_prefs({"provider": provider, "key": api_key, "model": model_or_url})
        st.success("Configuration saved!")

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

def call_ai_engine(prompt):
    if not api_key:
        return "❌ Error: API Key is missing. Check sidebar."

    try:
        if provider == "RapidAPI":
            if "http" not in model_or_url:
                return "❌ Error: For RapidAPI, you must provide the FULL Request URL."
            host = model_or_url.split("//")[-1].split("/")[0]
            headers = {
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": host,
                "Content-Type": "application/json"
            }
            payload = {"messages": [{"role": "user", "content": prompt}], "model": "gpt-4o"}
            resp = requests.post(model_or_url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content']
            return f"❌ RapidAPI Error ({resp.status_code}): {resp.text}"

        elif provider in ["OpenAI", "Groq"]:
            base = "https://api.groq.com/openai/v1" if provider == "Groq" else None
            client = openai.OpenAI(api_key=api_key, base_url=base)
            res = client.chat.completions.create(
                model=model_or_url if model_or_url else "gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            return res.choices[0].message.content

        elif provider == "Anthropic":
            client = anthropic.Anthropic(api_key=api_key)
            res = client.messages.create(
                model=model_or_url if model_or_url else "claude-3-5-sonnet-20240620",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return res.content[0].text

        elif provider == "Google Gemini":
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_or_url if model_or_url else "gemini-1.5-flash")
            res = model.generate_content(prompt)
            return res.text

        elif provider == "Hugging Face":
            url = f"https://api-inference.huggingface.co/models/{model_or_url}"
            headers = {"Authorization": f"Bearer {api_key}"}
            resp = requests.post(url, headers=headers, json={"inputs": prompt})
            data = resp.json()
            return data[0]['generated_text'] if isinstance(data, list) else str(data)

        elif provider == "MS Copilot/Azure":
            headers = {"api-key": api_key, "Content-Type": "application/json"}
            payload = {"messages": [{"role": "user", "content": prompt}]}
            resp = requests.post(model_or_url, headers=headers, json=payload, params={"api-version": "2024-02-01"})
            return resp.json()['choices'][0]['message']['content']

    except Exception as e:
        return f"🚨 System Error: {str(e)}"

st.title("🌐 Universal AI Hub")
st.info(f"Active Provider: {provider}")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Ask anything..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    with st.chat_message("assistant"):
        with st.spinner("🧠 Thinking..."):
            response = call_ai_engine(user_input)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
