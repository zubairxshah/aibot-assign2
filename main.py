import chainlit as cl
from agent_config.gemini_agent import run_agent
import json

@cl.on_chat_start
async def start():
    await cl.Message(content="Hello! I'm your Gemini-powered AI assistant. Ask me anything! Use 'search:' for web search or 'weather in' for weather info.").send()

@cl.on_message
async def main(message: cl.Message):
    user_query = message.content
    print(f"DEBUG MAIN: Original query: '{user_query}'")
    use_web_search = user_query.lower().startswith("search:")
    use_weather = user_query.lower().startswith("weather in")
    
    # Auto-detect search queries if not explicitly prefixed
    if not use_web_search and not use_weather:
        # Only trigger search for location-based queries or explicit search terms
        location_indicators = [" in ", " near ", " at "]
        search_keywords = ["restaurants", "hotels", "shops", "hospitals", "clinics", "gyms", "malls"]
        
        has_location = any(loc in user_query.lower() for loc in location_indicators)
        has_search_keyword = any(keyword in user_query.lower() for keyword in search_keywords)
        
        if (has_location and has_search_keyword) or user_query.lower().startswith(("find", "where", "best", "top", "list")):
            use_web_search = True
    
    print(f"DEBUG MAIN: use_web_search={use_web_search}, use_weather={use_weather}")
    query = user_query[7:].strip() if user_query.lower().startswith("search:") else user_query[10:].strip() if user_query.lower().startswith("weather in") else user_query
    print(f"DEBUG MAIN: Processed query: '{query}'")
    response = await run_agent(query, use_web_search=use_web_search, use_weather=use_weather)
    # Format JSON for display
    try:
        response_json = json.loads(response)
        formatted_response = f"Answer: {response_json['answer']}\nSource: {response_json['source']}"
    except json.JSONDecodeError:
        formatted_response = response
    await cl.Message(content=formatted_response).send()