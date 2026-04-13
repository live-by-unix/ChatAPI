import streamlit as st
import openai
import anthropic
import google.generativeai as genai
import requests
import json

# Setup
st.set_page_config(page_title="UNIVERSAL AI HUB 2026", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.header("🔌 Provider Setup")
    provider = st.selectbox(
        "Select AI Engine", 
        ["OpenAI", "Anthropic (Claude)", "Google (Gemini)", "Groq", "Hugging Face", "RapidAPI", "Microsoft Copilot"]
    )
    
    key = st.text_input("API Key / Token", type="password")
    
    # Contextual inputs based on provider
    model_id = ""
    extra_header = ""
    
    if provider == "OpenAI":
        model_id = st.text_input("Model", value="gpt-5-mini")
    elif provider == "Anthropic (Claude)":
        model_id = st.text_input("Model", value="claude-4.5-sonnet")
    elif provider == "Google (Gemini)":
        model_id = st.text_input("Model", value="gemini-2.5-pro")
    elif provider == "Groq":
        model_id = st.text_input("Model", value="llama-4-70b-versatile")
    elif provider == "Hugging Face":
        model_id = st.text_input("Model Path", placeholder="meta-llama/Llama-4-8B")
    elif provider == "RapidAPI":
        model_id = st.text_input("Full Request URL", placeholder="https://api-name.p.rapidapi.com/v1/chat")
    elif provider == "Microsoft Copilot":
        model_id = st.text_input("Endpoint URL", placeholder="https://{resource}.openai.azure.com/...")
        extra_header = st.text_input("API Version", value="2025-05-01-preview")

    if st.button("🔄 Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

# --- THE UNIVERSAL API ADAPTER ---
def universal_call(prompt):
    if not key: return "❌ Please enter an API Key."
    
    try:
        # 1. OPENAI / GROQ (Standardized OpenAI Protocol)
        if provider in ["OpenAI", "Groq"]:
            base = "https://api.groq.com/openai/v1" if provider == "Groq" else None
            client = openai.OpenAI(api_key=key, base_url=base)
            res = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}]
            )
            return res.choices[0].message.content

        # 2. ANTHROPIC CLAUDE
        elif provider == "Anthropic (Claude)":
            client = anthropic.Anthropic(api_key=key)
            res = client.messages.create(
                model=model_id,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            return res.content[0].text

        # 3. GOOGLE GEMINI
        elif provider == "Google (Gemini)":
            genai.configure(api_key=key)
            model = genai.GenerativeModel(model_id)
            res = model.generate_content(prompt)
            return res.text

        # 4. HUGGING FACE (Inference API)
        elif provider == "Hugging Face":
            url = f"https://api-inference.huggingface.co/models/{model_id}"
            headers = {"Authorization": f"Bearer {key}"}
            payload = {"inputs": prompt, "parameters": {"max_new_tokens": 500}}
            response = requests.post(url, headers=headers, json=payload)
            data = response.json()
            # Handle different HF output formats
            if isinstance(data, list): return data[0].get('generated_text', str(data))
            return data.get('generated_text', str(data))

        # 5. RAPIDAPI (Adaptive Payload)
        elif provider == "RapidAPI":
            host = model_id.split("//")[-1].split("/")[0]
            headers = {
                "X-RapidAPI-Key": key,
                "X-RapidAPI-Host": host,
                "Content-Type": "application/json"
            }
            # Most RapidAPI LLMs expect this OpenAI-clone format now
            payload = {"messages": [{"role": "user", "content": prompt}], "model": "gpt-4o"}
            response = requests.post(model_id, headers=headers, json=payload)
            res_j = response.json()
            return res_j['choices'][0]['message']['content'] if 'choices' in res_j else str(res_j)

        # 6. MICROSOFT COPILOT (Azure OpenAI)
        elif provider == "Microsoft Copilot":
            headers = {"api-key": key, "Content-Type": "application/json"}
            payload = {"messages": [{"role": "user", "content": prompt}]}
            params = {"api-version": extra_header}
            response = requests.post(model_id, headers=headers, json=payload, params=params)
            res_j = response.json()
            return res_j['choices'][0]['message']['content']

    except Exception as e:
        return f"🚨 Connection Error: {str(e)}"

# --- CHAT INTERFACE ---
st.title("🌐 Universal AI Hub")
st.caption(f"Connected to: **{provider}**")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Send a message..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = universal_call(user_input)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
