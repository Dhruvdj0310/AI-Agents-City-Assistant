
import os
import uuid
import requests
import streamlit as st

from dotenv import load_dotenv
from tavily import TavilyClient

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="City Assistant",
    page_icon="🌍",
    layout="centered"
)

load_dotenv()


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "pending_interrupt" not in st.session_state:
    st.session_state.pending_interrupt = None

config = {
    "configurable": {
        "thread_id": st.session_state.thread_id
    }
}


# ============================================================
# TITLE
# ============================================================

st.markdown(
    "<h1 style='text-align:center'>🌍 City Assistant</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<p style='text-align:center'>"
    "Get current weather and latest city news"
    "</p>",
    unsafe_allow_html=True
)


# ============================================================
# WEATHER TOOL
# ============================================================

@tool
def get_weather(city: str) -> str:
    """Returns the current weather for the given city."""

    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        return "Weather API key is not configured."

    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": city,
                "appid": api_key,
                "units": "metric"
            },
            timeout=15
        )

        response.raise_for_status()
        data = response.json()

        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]

        return f"Weather in {city}: {desc}, {temp}°C"

    except requests.RequestException:
        return "Unable to fetch weather. Please try again."

    except (KeyError, ValueError):
        return f"Could not retrieve weather for {city}."


# ============================================================
# NEWS TOOL
# ============================================================

tavily_api_key = os.getenv("TAVILY_API_KEY")

tavily_client = (
    TavilyClient(api_key=tavily_api_key)
    if tavily_api_key
    else None
)


@tool
def get_news(city: str) -> str:
    """Returns the latest news for the given city."""

    if tavily_client is None:
        return "Tavily API key is not configured."

    try:
        response = tavily_client.search(
            query=f"latest news in {city}",
            search_depth="basic",
            max_results=3
        )

        results = response.get("results", [])

        if not results:
            return f"No news found for {city}."

        news_list = []

        for item in results:
            title = item.get("title", "No title")
            url = item.get("url", "")
            snippet = item.get("content", "")[:150]

            news_list.append(
                f"- **{title}**\n\n"
                f"  Link: {url}\n\n"
                f"  Summary: {snippet}"
            )

        return (
            f"Latest news for {city}:\n\n"
            + "\n\n".join(news_list)
        )

    except Exception:
        return "Unable to fetch news. Please try again."


# ============================================================
# LLM
# ============================================================

llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash"
)


# ============================================================
# AGENT + HUMAN APPROVAL
# ============================================================

checkpointer = InMemorySaver()

Agent = create_agent(
    llm,
    tools=[get_weather, get_news],
    system_prompt=(
        "You are a helpful city assistant. "
        "Use get_weather for weather queries and get_news "
        "for the latest city news. Answer using tool results."
    ),
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                "get_weather": {
                    "allowed_decisions": ["approve", "reject"]
                },
                "get_news": {
                    "allowed_decisions": ["approve", "reject"]
                }
            }
        )
    ],
    checkpointer=checkpointer
)


# ============================================================
# RESPONSE HANDLING
# ============================================================

def extract_text(content):
    """Convert model response content into displayable text."""

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []

        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
            else:
                parts.append(str(item))

        return "\n".join(parts)

    return str(content)


def handle_result(result):
    """Save completed answers or retain pending approval."""

    interrupts = result.get("__interrupt__", ())

    if interrupts:
        st.session_state.pending_interrupt = interrupts[0]
        return

    st.session_state.pending_interrupt = None

    final_message = result["messages"][-1]
    answer = extract_text(final_message.content)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })


# ============================================================
# CHAT HISTORY
# ============================================================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ============================================================
# CHAT INPUT
# ============================================================

user_input = st.chat_input(
    "Ask about weather or news of a city...",
    disabled=st.session_state.pending_interrupt is not None
)

if user_input:

    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("🤖 Agent is thinking..."):

            try:
                result = Agent.invoke(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": user_input
                            }
                        ]
                    },
                    config=config
                )

                handle_result(result)

                if st.session_state.pending_interrupt is None:
                    st.markdown(
                        st.session_state.messages[-1]["content"]
                    )

            except Exception as exc:
                st.error(f"Agent error: {exc}")


# ============================================================
# APPROVAL PANEL
# ============================================================

pending = st.session_state.pending_interrupt

if pending is not None:

    st.divider()
    st.subheader("🛡️ Human Approval Required")

    # LangGraph interrupt payload
    interrupt_data = pending.value

    action_requests = interrupt_data["action_requests"]

    st.warning(
        "The AI agent wants to execute a tool. "
        "Review the request before allowing execution."
    )

    for action in action_requests:
        st.markdown(f"**Tool:** `{action['name']}`")
        st.json(action["args"])

    col1, col2 = st.columns(2)

    with col1:
        approve = st.button(
            "✅ Approve",
            use_container_width=True,
            key="approve_tool"
        )

    with col2:
        reject = st.button(
            "❌ Deny",
            use_container_width=True,
            key="reject_tool"
        )

    if approve or reject:

        if approve:
            decisions = [
                {"type": "approve"}
                for _ in action_requests
            ]
        else:
            decisions = [
                {
                    "type": "reject",
                    "message": "The user denied this tool execution."
                }
                for _ in action_requests
            ]

        try:
            with st.spinner("🤖 Resuming agent..."):

                result = Agent.invoke(
                    Command(
                        resume={
                            "decisions": decisions
                        }
                    ),
                    config=config
                )

                handle_result(result)

            st.rerun()

        except Exception as exc:
            st.error(f"Unable to resume agent: {exc}")


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("🌍 City Assistant")

    st.markdown("""
    - 🌤️ Current weather
    - 📰 Latest city news
    - 🤖 AI-powered tool selection
    - 🛡️ Human approval before execution
    """)

    st.divider()
    st.subheader("Example Questions")

    st.markdown("""
    - What's the weather in Jaipur?
    - Give me the latest news about Delhi.
    - What's the weather in Mumbai?
    - Tell me the latest news in Bengaluru.
    - What's the weather and news in Pune?
    """)

    st.divider()

    if st.button("🗑️ Clear Chat", use_container_width=True):

        st.session_state.messages = []
        st.session_state.pending_interrupt = None
        st.session_state.thread_id = str(uuid.uuid4())

        st.rerun()
