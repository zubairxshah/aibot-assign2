import streamlit as st
import asyncio
from agent_config.gemini_agent import run_agent
import json

# Set page config
st.set_page_config(
    page_title="AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# Title and description
st.title("🤖 AI Assistant")
st.markdown("Ask me anything! I can search the web, get weather information, or chat with you.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process the query
    user_query = prompt
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
    
    # Process query
    query = user_query[7:].strip() if user_query.lower().startswith("search:") else user_query[10:].strip() if user_query.lower().startswith("weather in") else user_query
    
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Run the async function with proper event loop handling
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                response = loop.run_until_complete(run_agent(query, use_web_search=use_web_search, use_weather=use_weather))
            except RuntimeError:
                # If there's still an issue, create a new event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(run_agent(query, use_web_search=use_web_search, use_weather=use_weather))
            
            # Format response
            try:
                response_json = json.loads(response)
                formatted_response = f"**Answer:** {response_json['answer']}\n\n*Source: {response_json['source']}*"
            except json.JSONDecodeError:
                formatted_response = response
            
            st.markdown(formatted_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": formatted_response})

# Sidebar with instructions
with st.sidebar:
    st.header("How to use:")
    st.markdown("""
    - **Weather**: Type "weather in [city]" (e.g., "weather in Karachi")
    - **Web Search**: Type "search: [query]" or use keywords like restaurants, hotels, etc.
    - **General Chat**: Ask any question for AI assistance
    
    **Examples:**
    - weather in New York
    - search: best restaurants in Karachi
    - restaurants in Lahore
    - What is artificial intelligence?
    """)
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()