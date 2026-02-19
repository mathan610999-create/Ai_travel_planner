import streamlit as st
import os
import pandas as pd
from google import genai
from amadeus import Client, ResponseError

# 1. AUTHENTICATION: Use st.secrets for Cloud Deployment
# On your local machine, this will look for .streamlit/secrets.toml
# On Streamlit Cloud, you must paste these into the "Secrets" dashboard
gemini_key = st.secrets.get("GEMINI_API_KEY")
amadeus_id = st.secrets.get("AMADEUS_CLIENT_ID")
amadeus_secret = st.secrets.get("AMADEUS_CLIENT_SECRET")

# 2. WEBSITE CONFIGURATION
st.set_page_config(page_title="AI Travel Startup", page_icon="✈️", layout="wide")
st.title("🌍 Travel Companion")

# Sidebar for User Inputs
with st.sidebar:
    st.header("Trip Details")
    dest = st.text_input("Destination City Name", "Goa")
    # Added a note for the user about IATA codes
    city_code = st.text_input("City Code (3-letter IATA)", "GOI").upper().strip()
    
    budget_raw = st.text_input("Budget (INR)", "50000")
    try:
        budget_val = int(''.join(filter(str.isdigit, budget_raw)))
    except ValueError:
        budget_val = 50000
        
    days = st.slider("Trip Duration (Days)", 1, 14, 3)
    travelers = st.selectbox("Travelers", ["Solo", "2 Adults", "Family", "Friends"])

# 3. INITIALIZE CLIENTS
genai_client = genai.Client(api_key=gemini_key) if gemini_key else None

# Amadeus Client Initialization
amadeus_client = None
if amadeus_id and amadeus_secret:
    try:
        # The Amadeus SDK handles token refreshing automatically
        amadeus_client = Client(client_id=amadeus_id, client_secret=amadeus_secret)
    except Exception as e:
        st.sidebar.error(f"Amadeus Init Error: {e}")
else:
    st.sidebar.warning("Amadeus keys missing in Secrets.")

# 4. MAIN ACTION BUTTON
if st.button("Generate My Travel Experience"):
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🤖 AI Personalized Itinerary")
        if genai_client:
            try:
                def stream_plan():
                    prompt = (f"Create a detailed {days}-day itinerary for {travelers} "
                              f"to {dest} with a total budget of ₹{budget_val}. "
                              "Include specific landmarks and local food recommendations.")
                    response = genai_client.models.generate_content_stream(
                        model="gemini-2.0-flash", contents=prompt
                    )
                    for chunk in response:
                        yield chunk.text
                st.write_stream(stream_plan)
            except Exception as e:
                st.error(f"AI Generation Error: {e}")
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
        if amadeus_client:
            try:
                # Testing the connection by fetching hotels by city code
                hotels = amadeus_client.reference_data.locations.hotels.by_city.get(cityCode=city_code)
                if hotels.data:
                    st.success(f"Found {len(hotels.data[:5])} hotels in {city_code}:")
                    for hotel in hotels.data[:5]:
                        name = hotel.get('name', 'Unknown Hotel').title()
                        st.info(f"🏨 {name}")
                else:
                    st.warning(f"No hotel data found for code: {city_code}")
            except ResponseError as error:
                st.error(f"Market API Error: {error.response.result['errors'][0]['detail']}")
                st.info("Tip: Double-check that your IATA code is correct (e.g., MAA for Chennai).")
        else:
            st.warning("Amadeus comparison feature disabled.")

# Removed Email Section per request
st.markdown("---")
st.caption(f"Developed by Mathanagopal | Travel Companion")
