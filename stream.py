import streamlit as st
import pandas as pd
from google import genai
from amadeus import Client, ResponseError

# 1. AUTHENTICATION
# On Streamlit Cloud: Add these to Settings -> Secrets
# On Local: Add to .streamlit/secrets.toml
gemini_key = st.secrets.get("GEMINI_API_KEY")
amadeus_id = st.secrets.get("AMADEUS_CLIENT_ID")
amadeus_secret = st.secrets.get("AMADEUS_CLIENT_SECRET")

# 2. HELPER FUNCTION: Dynamic City Lookup
def get_city_code(am_client, city_name):
    """Fetches the 3-letter IATA code for any city name entered."""
    if not am_client or not city_name:
        return None
    try:
        response = am_client.reference_data.locations.get(
            keyword=city_name.upper(),
            subType='CITY'
        )
        if response.data:
            # Returns the most relevant IATA code
            return response.data[0]['iataCode']
    except ResponseError:
        return None
    return None

# 3. WEBSITE CONFIGURATION
st.set_page_config(page_title="AI Travel Companion", page_icon="✈️", layout="wide")
st.title("🌍 AI Travel Companion")

# Sidebar for User Inputs
with st.sidebar:
    st.header("Trip Details")
    dest_input = st.text_input("Destination City", "Goa")
    
    budget_raw = st.text_input("Budget (INR)", "50000")
    try:
        budget_val = int(''.join(filter(str.isdigit, budget_raw)))
    except ValueError:
        budget_val = 50000
        
    days = st.slider("Trip Duration (Days)", 1, 14, 3)
    travelers = st.selectbox("Travelers", ["Solo", "2 Adults", "Family", "Friends"])

# 4. INITIALIZE CLIENTS
genai_client = genai.Client(api_key=gemini_key) if gemini_key else None
amadeus_client = None

if amadeus_id and amadeus_secret:
    try:
        amadeus_client = Client(client_id=amadeus_id, client_secret=amadeus_secret)
    except Exception as e:
        st.sidebar.error(f"Amadeus Auth Error: {e}")

# Perform Dynamic Lookup
city_code = get_city_code(amadeus_client, dest_input)

if city_code:
    st.sidebar.success(f"Validated City Code: {city_code}")
else:
    st.sidebar.warning("Could not find city code. Market data may fail.")

# 5. MAIN ACTION BUTTON
if st.button("Generate My Travel Experience"):
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🤖 AI Personalized Itinerary")
        if genai_client:
            def stream_plan():
                prompt = (f"Create a detailed {days}-day itinerary for {travelers} "
                          f"to {dest_input} with a total budget of ₹{budget_val}. "
                          "Focus on popular landmarks and hidden gems.")
                response = genai_client.models.generate_content_stream(
                    model="gemini-2.0-flash", contents=prompt
                )
                for chunk in response:
                    yield chunk.text
            st.write_stream(stream_plan)
        else:
            st.error("Gemini API key is missing.")

    with col2:
        # DATA VISUALIZATION
        st.subheader("📊 Price Benchmarking")
        bench_data = {
            'Category': ['Budget', 'Your Plan', 'Mid-Range', 'Luxury'],
            'Amount (₹)': [25000, budget_val, 75000, 150000]
        }
        chart_df = pd.DataFrame(bench_data)
        st.bar_chart(data=chart_df, x='Category', y='Amount (₹)', color="#ff4b4b")
        
        st.markdown("---")
        
        # LIVE MARKET DATA
        st.subheader("💰 Live Market Options")
        if amadeus_client and city_code:
            try:
                hotels = amadeus_client.reference_data.locations.hotels.by_city.get(cityCode=city_code)
                if hotels.data:
                    st.info(f"Top stays found in {city_code}:")
                    for hotel in hotels.data[:5]:
                        st.write(f"🏨 {hotel.get('name', 'Hotel').title()}")
                else:
                    st.warning(f"No specific hotel listings found for {city_code}.")
            except ResponseError as error:
                st.error(f"Market Data Error: {error.response.result['errors'][0]['detail']}")
        else:
            st.warning("Market data unavailable (Check city name or API keys).")

st.markdown("---")
st.caption(f"Developed by Mathanagopal | Travel Companion")
