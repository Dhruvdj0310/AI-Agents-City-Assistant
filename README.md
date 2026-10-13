# AI Agents City Assistant

An AI-powered city assistant built with Python, LangChain, LangGraph, Google Gemini, Streamlit, OpenWeather, and Tavily. It helps users ask about current weather and recent city news through a conversational interface.

## Features

- **Weather updates:** Retrieves current weather information using the OpenWeather API.
- **City news:** Searches for recent city-related news using Tavily.
- **Conversational AI:** Uses Google Gemini through LangChain to understand user requests and coordinate tools.
- **Human-in-the-loop tool approval:** Lets the user review and approve or deny tool execution in the Streamlit app.
- **Chat interface:** Provides a Streamlit chat UI and a way to clear the conversation.
- **CLI version:** Includes a terminal-based assistant in `Agents.py`.

## Project Structure

```text
Project-Agent/
├── Agents.py
├── Agents_app.py
├── requirements.txt
├── .gitignore
└── .env  # Local only; never upload to GitHub
```

## Tech Stack

- Python
- Streamlit
- LangChain
- LangGraph
- Google Gemini (`langchain-google-genai`)
- OpenWeather API
- Tavily Search API
- `python-dotenv`
- Requests

## Prerequisites

- Python version compatible with the dependencies
- Google Gemini API key
- OpenWeather API key
- Tavily API key

## Setup and Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Dhruvdj0310/AI-Agents-City-Assistant.git
   cd AI-Agents-City-Assistant
   ```

   If your GitHub repository uses a different name, replace the URL and folder name accordingly.

2. **Create and activate a virtual environment**

   Windows:

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

   macOS/Linux:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a local `.env` file in the project root with your own API keys:

   ```env
   GOOGLE_API_KEY=your_google_api_key
   OPENWEATHER_API_KEY=your_openweather_api_key
   TAVILY_API_KEY=your_tavily_api_key
   ```

   Never commit `.env` or real API keys to GitHub. Keep `.env` listed in `.gitignore`. If a key has already been exposed, revoke or rotate it in the provider dashboard.

## Run the Application

### Streamlit web app

```bash
streamlit run Agents_app.py
```

Open the local URL printed by Streamlit in your browser.

### Command-line assistant

```bash
python Agents.py
```

## How It Works

1. The user asks a question about a city.
2. The agent determines whether it needs the weather or news tool.
3. The selected tool fetches information from its API.
4. In the Streamlit app, tool execution can be reviewed through the human-approval flow.
5. The assistant uses the tool result to respond.

## Notes

- API responses depend on provider availability and usage limits.
- Keep API keys private and never commit local environment files.
- If you encounter a model-not-found error, verify that the model name in the source code is available to your Google AI API account.

## Author

**Dhruv Jain**

- GitHub: [Dhruvdj0310](https://github.com/Dhruvdj0310)
- LinkedIn: [Dhruv Jain](https://www.linkedin.com/in/dhruv-jain-0b3761258/)
