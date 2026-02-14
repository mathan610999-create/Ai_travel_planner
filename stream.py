import streamlit as st
import os
import pandas as pd
from dotenv import load_dotenv
from google import genai
from amadeus import Client, ResponseError

# 1. THE DETECTIVE: Force-load your .env keys
load_dotenv(override=True)

gemini_key = os.getenv("GEMINI_API_KEY")
amadeus_id = os.getenv("AMADEUS_CLIENT_ID")
amadeus_secret = os.getenv("AMADEUS_CLIENT_SECRET")

# 2. WEBSITE CONFIGURATION
st.set_page_config(page_title="AI Travel Startup", page_icon="✈️", layout="wide")
st.title("🌍 Travel companion")

# Sidebar for User Inputs
with st.sidebar:
    st.header("Trip Details")
    dest = st.text_input("Destination City", "Goa")
    city_code = st.text_input("City Code (IATA)", "GOI").upper()
    
    # Clean the budget input for numerical analysis
    budget_raw = st.text_input("Budget (e.g., 50000)", "50000")
    try:
        budget_val = int(''.join(filter(str.isdigit, budget_raw)))
    except ValueError:
        budget_val = 50000
        
    days = st.slider("Trip Duration (Days)", 1, 14, 3)
    travelers = st.selectbox("Travelers", ["Solo", "2 Adults", "Family", "Friends"])

# 3. INITIALIZE CLIENTS
genai_client = genai.Client(api_key=gemini_key) if gemini_key else None
amadeus_client = None
if amadeus_id and amadeus_secret:
    try:
        amadeus_client = Client(client_id=amadeus_id, client_secret=amadeus_secret)
    except Exception:
        am_client_status = "Error"
else:
    am_client_status = "Missing Keys"

# 4. MAIN ACTION BUTTON
if st.button("Generate My Travel Experience"):
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🤖 AI Personalized Itinerary")
        if genai_client:
            def stream_plan():
                prompt = (f"Create a detailed {days}-day itinerary for {travelers} "
                          f"to {dest} with a total budget of ₹{budget_val}.")
                response = genai_client.models.generate_content_stream(
                    model="gemini-2.0-flash", contents=prompt
                )
                for chunk in response:
                    yield chunk.text
            st.write_stream(stream_plan)

    with col2:
        # DATA VISUALIZATION: Price Benchmarking
        st.subheader("📊 Price Benchmarking")
        # Comparing user input against market averages
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
                hotels = amadeus_client.reference_data.locations.hotels.by_city.get(cityCode=city_code)
                if hotels.data:
                    for hotel in hotels.data[:5]:
                        st.info(f"🏨 {hotel.get('name', 'Hotel')}")
                else:
                    st.warning(f"No hotel data found for {city_code}.")
            except ResponseError:
                st.error("Market API error. Check city code or keys.")
        else:
            st.warning("Amadeus keys are missing. Comparison feature disabled.")

    # 5. LEAD GENERATION: Share & Intimate Partners
    st.markdown("---")
    st.subheader("📧 Share This Itinerary")
    
    # Pre-filled email details
    subject = f"Travel Inquiry: {days}-Day {dest} Trip"
    body = f"I am interested in a {days}-day trip to {dest} for {travelers} with a budget of ₹{budget_val}."
    mailto_url = f"mailto:mathan610999@gmail.com?subject={subject.replace(' ', '%20')}&body={body.replace(' ', '%20')}"
    
    st.markdown(f'''
        <a href="{mailto_url}" target="_blank" style="text-decoration:none;">
            <div style="background-color:#ff4b4b;color:white;padding:15px;text-align:center;border-radius:10px;font-weight:bold;">
                📩 Click to Email Itinerary to Parents / Travel Agent
            </div>
        </a>
    ''', unsafe_allow_html=True)

st.caption(f"Developed by Mathanagopal | Travel Companion")