import os
import requests

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain_core.messages import HumanMessage , ToolMessage
from rich import print
from tavily import TavilyClient
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call

#Weather Tool

@tool
def get_weather(city: str) -> str:
    """"Returns the current weather for the given city."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    data = response.json()

    if str(data.get("cod")) != "200":
        return f"Error: {data.get('message', 'Could not fetch weather')}"
    
    temp = data["main"]["temp"]
    desc = data["weather"][0]["description"]
    
    return f"Weather in {city}: {desc}, {temp}°C"

#News Tool

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
@tool
def get_news(city: str) -> str:
    """Returns the latest news for the given city."""
    response = tavily_client.search(
        query = f"latest news in {city}",
        search_depth = "basic",
        max_results = 3
    )
    results = response.get("results", [])
    if not results:
        return f"No news found for {city}."

    news_list = []

    for r in results:
        title = r.get("title", "No title")
        url = r.get("url", "")
        snippet = r.get("content", "")
        snippet = snippet[:100]
        news_list.append(
            f"- {title}\n  🔗 {url}\n  📝 {snippet[:100]}..."
        )
    return f"Latest news in {city}:\n\n" + "\n\n".join(news_list)

#LLM Setup
llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash")

@wrap_tool_call
def human_approval(request,handler): # request me agent ke tool call ki info hoti haii,handler actuall tool execution ko continue krta haiii
    """Ask a human approval for any tool call"""
    tool_name = request.tool_call['name']
    confirm = input(f"Do you want to execute the tool '{tool_name}'? (yes/no): ")
    if confirm.lower() == "no":
        return ToolMessage(
            content = "tool call denied by user",
            tool_call_id = request.tool_call['id']
        )
    return handler(request)  # Continue with the tool execution if approved




Agent = create_agent(
    llm,
    tools=[get_weather, get_news],
    system_prompt= " You are a helpful city assistant.",
    middleware=[human_approval]
    )





print("Agent is ready! Type 'exit' to quit.")


while True:
    user_input = input("User: ")
    if user_input.lower() == "exit":
        break
    result = Agent.invoke(
        {"messages": [{"role": "user", "content": user_input}]},
    )
    print(f"Agent: {result['messages'][-1].content[0]['text']}")

