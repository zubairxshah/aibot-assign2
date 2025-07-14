import google.generativeai as genai
import aiohttp
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import asyncio
import json

# Load environment variables
load_dotenv()

# Debug: Print API keys
# print("GEMINI_API_KEY:", os.getenv("GEMINI_API_KEY"))
# print("SERPER_API_KEY:", os.getenv("SERPER_API_KEY"))
# print("WEATHER_API_KEY:", os.getenv("WEATHER_API_KEY"))

# Configure Gemini client
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Pydantic schema for structured output
class AssistantResponse(BaseModel):
    answer: str
    source: str  # e.g., "Gemini", "Web Search", "Weather API"

# Predefined gym data for Karachi (from provided web results)
KARACHI_GYMS = """
Popular sports gyms in Karachi include:
1. **Powerhouse Gym – ARENA** (FEC – 01, Habib Ibrahim Rehmatullah Road, Main Karsaz): Offers state-of-the-art fitness equipment, indoor/outdoor sports, bowling alley, Rangoli Buffet, and a bar/cafe.[](https://www.yanrefitness.com/9-most-popular-gyms-in-karachi/)
2. **Shapes Active LifeStyle** (139 McNeil Road, Near Old Racecourse Ground): Features hi-tech cardio/resistance machines, Olympic-standard badminton/squash/table tennis courts, indoor pools, steam rooms, saunas, and Jacuzzis.[](https://www.yanrefitness.com/9-most-popular-gyms-in-karachi/)
3. **CORE Fitness** (14th Floor, Ocean Tower, Clifton): A 15,000-square-foot lifestyle hub with modern equipment, personal training, and a health café.[](https://www.yanrefitness.com/9-most-popular-gyms-in-karachi/)
4. **Structure Health & Fitness** (12/C 1-3rd Floor, Badar Commercial Ext, DHA): Boutique fitness center with state-of-the-art equipment, MMA, boxing, and CrossFit.[](https://www.graana.com/blog/best-gyms-in-karachi/)
5. **Platinum Fitness Center** (Emerald Tower, Clifton): Specializes in powerlifting, Olympic weightlifting, CrossFit, with meal plans starting at PKR 2,500.[](https://www.graana.com/blog/best-gyms-in-karachi/)
6. **Element Fitness Center** (Shaheed-e-Millat Road): Offers MMA, cardio kickboxing, Brazilian Jiu-Jitsu, Muay Thai, and yoga, with a large 1000 sq.ft. facility.[](https://www.graana.com/blog/best-gyms-in-karachi/)
7. **TriFit Fitness Club** (Sea View): Boutique luxury gym with modern equipment and group classes.[](https://trifit.com.pk/)
8. **Atmosphere Fitness** (Old Queens Road, Near II Chundrigrah Road): Features top-tier Life Fitness equipment, separate ladies’ gym, archery, and horse riding.[](https://atmosphere.com.pk/)
9. **VelocityX** (Tipu Sultan Road): Offers Zumba, Pilates, yoga, and specialized programs like Method X and Power Shred.[](https://pakistanijournal.com/top-10-best-gyms-in-karachi/)
10. **Body Evolution** (Bahadurabad): Premium gym with MMA classes, sauna, and a protein café.[](https://bodyevolution.net/)
"""

# Web search function using Serper API
async def web_search(query: str) -> str:
    try:
        serper_key = os.getenv("SERPER_API_KEY")
        if not serper_key:
            return "Web search error: API key not found"
            
        async with aiohttp.ClientSession() as session:
            url = "https://google.serper.dev/search"
            headers = {"X-API-KEY": serper_key, "Content-Type": "application/json"}
            payload = {"q": query, "num": 5}
            print(f"DEBUG: Serper API request - URL: {url}, Query: {query}")
            async with session.post(url, json=payload, headers=headers) as response:
                print(f"DEBUG: Serper API status: {response.status}")
                if response.status != 200:
                    response_text = await response.text()
                    print(f"DEBUG: Serper API error response: {response_text}")
                    return f"Web search error: Unable to fetch data (status {response.status})"
                data = await response.json()
                print(f"DEBUG: Serper API response: {data}")
                organic_results = data.get("organic", [])
                if not organic_results:
                    return "No search results found."
                results = []
                for i, result in enumerate(organic_results[:3]):
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    link = result.get("link", "")
                    results.append(f"**{i+1}. {title}**\n{snippet}\n🔗 {link}\n")
                return "\n".join(results)
    except Exception as e:
        print(f"DEBUG: Web search exception: {str(e)}")
        return f"Web search error: {str(e)}"

# Weather fetch function using WeatherAPI.com
async def get_weather(city: str) -> str:
    try:
        weather_key = os.getenv('WEATHER_API_KEY')
        if not weather_key:
            return "Weather error: API key not found"
        
        async with aiohttp.ClientSession() as session:
            url = f"http://api.weatherapi.com/v1/current.json?key={weather_key}&q={city}&aqi=no"
            print(f"DEBUG: Weather API URL: {url}")
            async with session.get(url) as response:
                print(f"DEBUG: Weather API status: {response.status}")
                if response.status != 200:
                    return f"Weather error: Unable to fetch data for {city} (status {response.status})"
                data = await response.json()
                print(f"DEBUG: Weather API response: {data}")
                if "error" in data:
                    return f"Weather error: {data['error']['message']}"
                temp = data["current"]["temp_c"]
                condition = data["current"]["condition"]["text"]
                return f"Weather in {city}: {temp}°C, {condition}"
    except Exception as e:
        print(f"DEBUG: Weather exception: {str(e)}")
        return f"Weather error: {str(e)}"

# Main agent function with structured output
async def run_agent(query: str, use_web_search: bool = False, use_weather: bool = False) -> str:
    print(f"DEBUG: Query='{query}', use_web_search={use_web_search}, use_weather={use_weather}")
    
    try:
        if use_weather:
            city = query.strip()
            print(f"DEBUG: Getting weather for city: '{city}'")
            weather_info = await get_weather(city)
            print(f"DEBUG: Weather info: {weather_info}")
            if "error" in weather_info.lower():
                return json.dumps({"answer": "I'm sorry, I couldn't retrieve weather information", "source": "Weather API"}, indent=2)
            return json.dumps({"answer": weather_info, "source": "Weather API"}, indent=2)
            
        elif use_web_search:
            print(f"DEBUG: Performing web search for: '{query}'")
            if "gym" in query.lower() and "karachi" in query.lower():
                search_results = KARACHI_GYMS
                source = "Predefined Gym Data"
                print("DEBUG: Using predefined gym data")
            else:
                search_results = await web_search(query)
                source = "Web Search"
                print(f"DEBUG: Web search results: {search_results[:200]}...")
            
            if "error" in search_results.lower():
                return json.dumps({"answer": "I'm sorry, I couldn't retrieve search results", "source": source}, indent=2)
            return json.dumps({"answer": search_results, "source": source}, indent=2)
        
        else:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = await model.generate_content_async(query)
            response_text = response.text if response.text else "No response from Gemini"
            return json.dumps({"answer": response_text, "source": "Gemini"}, indent=2)
            
    except Exception as e:
        print(f"DEBUG: Exception occurred: {str(e)}")
        return json.dumps({"answer": f"Error: {str(e)}", "source": "Error"}, indent=2)