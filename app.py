import streamlit as st
import openai
import anthropic
import google.generativeai as genai
import requests
import json
import os

# --- PERSISTENCE LOGIC ---
CONFIG_FILE = "config.json"

def save_config(config_data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return None

# Initial Page Config
st.set_page_config(page_title="UNIVERSAL AI HUB 2026", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Load saved config if it exists
saved_data = load_config()

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.header("🔌 Provider Setup")
    
    providers_list = ["OpenAI", "Anthropic (Claude)", "Google (Gemini)", "Groq", "Hugging Face", "RapidAPI", "Microsoft Copilot"]
    
    default_provider = saved_data.get("provider", "OpenAI") if saved_data else "OpenAI"
    default_key = saved_data.get("key", "") if saved_data else ""
    default_model = saved_data.get("model_id", "") if saved_data else ""
    
    provider = st.selectbox(
        "Select AI Engine", 
        providers_list,
        index=providers_list.index(default_provider) if default_provider in providers_list else 0
    )
    
    key = st.text_input("API Key / Token", value=default_key, type="password")
    
    # Model ID mapping with saved defaults
    if provider == "OpenAI":
        model_id = st.text_input("Model", value=default_model or "gpt-4o")
    elif provider == "Anthropic (Claude)":
        model_id = st.text_input("Model", value=default_model or "claude-3-5-sonnet-20240620")
    elif provider == "Google (Gemini)":
        model_id = st.text_input("Model", value=default_model or "gemini-1.5-flash")
    elif provider == "Groq":
        model_id = st.text_input("Model", value=default_model or "llama-3.3-70b-versatile")
    elif provider == "Hugging Face":
        model_id = st.text_input("Model Path", value=default_model, placeholder="meta-llama/Llama-3.1-8B")
    elif provider == "RapidAPI":
        model_id = st.text_input("Full Request URL", value=default_model, placeholder="https://api-name.p.rapidapi.com/v1/chat/completions")
    elif provider == "Microsoft Copilot":
        model_id = st.text_input("Endpoint URL", value=default_model)

    if st.button("💾 Save Configuration"):
        config_to_save = {
            "provider": provider,
            "key": key.strip(),
            "model_id": model_id.strip()
        }
        save_config(config_to_save)
        st.success("Configuration saved locally!")

    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

# --- THE UNIVERSAL API ADAPTER ---
def universal_call(prompt):
    if not key:
        return "⚠️ Missing API Key. Check the sidebar."
    
    try:
        # OpenAI / Groq
        if provider in ["OpenAI", "Groq"]:
            base = "https://api.groq.com/openai/v1" if provider == "Groq" else None
            client = openai.OpenAI(api_key=key, base_url=base)
            res = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}]
            )
            return res.choices[0].message.content

        # Claude
        elif provider == "Anthropic (Claude)":
            client = anthropic.Anthropic(api_key=key)
            res = client.messages.create(
                model=model_id, 
                max_tokens=2048, 
                messages=[{"role": "user", "content": prompt}]
            )
            return res.content[0].text

        # Gemini
        elif provider == "Google (Gemini)":
            genai.configure(api_key=key)
            model = genai.GenerativeModel(model_id)
            res = model.generate_content(prompt)
            return res.text

        # Hugging Face
        elif provider == "Hugging Face":
            api_url = f"https://api-inference.huggingface.co/models/{model_id}"
            headers = {"Authorization": f"Bearer {key}"}
            payload = {"inputs": prompt, "options": {"wait_for_model": True}}
            response = requests.post(api_url, headers=headers, json=payload)
            data = response.json()
            if isinstance(data, list):
                return data[0].get('generated_text', str(data))
            return data.get('generated_text', str(data))

        # RapidAPI
        elif provider == "RapidAPI":
            # Automatically extracts the host from your full URL
            host = model_id.split("//")[-1].split("/")[0]
            headers = {
                "X-RapidAPI-Key": key,
                "X-RapidAPI-Host": host,
                "Content-Type": "application/json"
            }
            # Standard payload for the 'NextAPI' cheapest-gpt-4 provider
            payload = {
                "messages": [{"role": "user", "content": prompt}],
                "model": "gpt-4o",
                "max_tokens": 500
            }
            response = requests.post(model_id, headers=headers, json=payload)
            if response.status_code != 200:
                return f"RapidAPI Error {response.status_code}: {response.text}"
            
            res_j = response.json()
            return res_j['choices'][0]['message']['content']

        # Azure / Microsoft Copilot
        elif provider == "Microsoft Copilot":
            headers = {"api-key": key, "Content-Type": "application/json"}
            payload = {"messages": [{"role": "user", "content": prompt}]}
            # Default to a standard API version if not specified
            response = requests.post(model_id, headers=headers, json=payload, params={"api-version": "2024-02-01"})
            return response.json()['choices'][0]['message']['content']

    except Exception as e:
        return f"🚨 System Error: {str(e)}"

# --- MAIN UI ---
st.title("🌐 Universal AI Hub")
st.info(f"Currently using: **{provider}**")

# Display history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle input
if user_input := st.chat_input("Ask your AI..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            response = universal_call(user_input)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
