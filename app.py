import streamlit as st
import openai
import anthropic
import google.generativeai as genai

st.set_page_config(page_title="CHATAPI", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "config" not in st.session_state:
    st.session_state.config = {"model": "OpenAI", "key": "", "endpoint": ""}

st.title("CHATAPI")

with st.sidebar:
    st.header("Settings")
    selected_model = st.selectbox(
        "AI Provider", 
        ["OpenAI", "Claude", "Gemini", "Microsoft Copilot"]
    )
    
    auth_key = st.text_input("API Key", type="password")
    
    azure_url = ""
    if selected_model == "Microsoft Copilot":
        azure_url = st.text_input("Azure Endpoint URL (Target Resource)")

    if st.button("Save & Initialize"):
        st.session_state.config = {
            "model": selected_model,
            "key": auth_key,
            "endpoint": azure_url
        }
        st.success("Credentials Active for Session")

    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

def call_api(prompt):
    cfg = st.session_state.config
    if not cfg["key"]:
        return "Missing API Key in Sidebar."

    try:
        if cfg["model"] == "OpenAI":
            client = openai.OpenAI(api_key=cfg["key"])
            res = client.chat.completions.create(
                model="gpt-4o",
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

        elif cfg["model"] == "Microsoft Copilot":
            client = openai.AzureOpenAI(
                api_key=cfg["key"],
                api_version="2024-02-01",
                azure_endpoint=cfg["endpoint"]
            )
            res = client.chat.completions.create(
                model="gpt-4", 
                messages=[{"role": "user", "content": prompt}]
            )
            return res.choices[0].message.content

    except Exception as e:
        return f"API Error: {str(e)}"

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Message CHATAPI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = call_api(prompt)
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
