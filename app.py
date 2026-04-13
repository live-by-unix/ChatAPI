import streamlit as st
import openai
import anthropic
import google.generativeai as genai
import requests

st.set_page_config(page_title="ULTIMATE CHAT API", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "config" not in st.session_state:
    st.session_state.config = {"model": "Groq", "key": "", "extra": ""}

st.title("CHATAPI")

with st.sidebar:
    st.header("Credentials")
    selected_provider = st.selectbox(
        "Provider", 
        ["Groq", "Hugging Face", "RapidAPI", "OpenAI", "Claude", "Gemini"]
    )
    
    api_key = st.text_input("API Key", type="password")
    
    extra_param = ""
    if selected_provider == "Hugging Face":
        extra_param = st.text_input("Model ID (e.g., mistralai/Mistral-7B-v0.1)")
    elif selected_provider == "RapidAPI":
        extra_param = st.text_input("API Host (e.g., twinword-sentiment-analysis.p.rapidapi.com)")

    if st.button("Save Configuration"):
        st.session_state.config = {
            "model": selected_provider,
            "key": api_key,
            "extra": extra_param
        }
        st.success("Configured!")

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

def call_api(prompt):
    cfg = st.session_state.config
    if not cfg["key"]:
        return "Please enter an API Key in the sidebar."

    try:
        if cfg["model"] == "Groq":
            client = openai.OpenAI(
                api_key=cfg["key"],
                base_url="https://api.groq.com/openai/v1"
            )
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            return res.choices[0].message.content

        elif cfg["model"] == "Hugging Face":
            model_id = cfg["extra"] if cfg["extra"] else "gpt2"
            api_url = f"https://api-inference.huggingface.co/models/{model_id}"
            headers = {"Authorization": f"Bearer {cfg['key']}"}
            res = requests.post(api_url, headers=headers, json={"inputs": prompt})
            return res.json()[0]['generated_text']

        elif cfg["model"] == "RapidAPI":
            url = f"https://{cfg['extra']}/analyze/"
            headers = {
                "X-RapidAPI-Key": cfg["key"],
                "X-RapidAPI-Host": cfg["extra"],
                "Content-Type": "application/json"
            }
            res = requests.post(url, headers=headers, json={"text": prompt})
            return str(res.json())

        elif cfg["model"] == "OpenAI":
            client = openai.OpenAI(api_key=cfg["key"])
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            return res.choices[0].message.content

        elif cfg["model"] == "Claude":
            client = anthropic.Anthropic(api_key=cfg["key"])
            res = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return res.content[0].text

        elif cfg["model"] == "Gemini":
            genai.configure(api_key=cfg["key"])
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(prompt)
            return res.text

    except Exception as e:
        return f"Error: {str(e)}"

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = call_api(prompt)
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
