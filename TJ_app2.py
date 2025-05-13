import streamlit as st
import requests
import datetime
from datetime import date, timedelta

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
SENDGRID_API_KEY = st.secrets["SENDGRID_API_KEY"]   # Sendgrid api

def send_email(to_email, subject, content):
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "personalizations": [{
            "to": [{"email": to_email}],
            "subject": subject
        }],
        "from": {"email": "tripsetternoreply@gmail.com"},
        "content": [{
            "type": "text/plain",
            "value": content
        }]
    }

    response = requests.post(url, headers=headers, json=data)
    print(f"Email status: {response.status_code}")
    if response.status_code >= 400:
        print(f"SendGrid Error: {response.text}")

st.title("✈️ Travel Itinerary Planner ✈️")

email = st.text_input("Email")
phone = st.text_input("Phone Number")
city = st.text_input("Destination City, Country")
trip_range = st.date_input(
    "Select Trip Dates",
    value=(date.today(), date.today()),
    min_value=date.today(),
    help="Choose your trip start and end dates"
)

activities = st.multiselect(
    "Select Your Interests",
    ["adventures", "historical", "gastronomy", "romantic"]
)

has_kids = st.checkbox("Are you traveling with kids?")
kids_ages = ""
if has_kids:
    kids_ages = st.text_input("Enter age(s) of the kids (i.e. 5,16)")

allergies = ""
if "gastronomy" in activities:
    allergies = st.text_input("Do you have any allergies?")

if st.button("Generate Travel Plan"):
    prompt = f"""
You are a travel assistant. Here's the user's input:
- Email: {email}
- Phone: {phone}
- City: {city}
- Activities: {', '.join(activities)}
- Kids: {'Yes, ages: ' + kids_ages if has_kids else 'No'}
- Dates: {trip_range}
{"- Allergies: " + allergies if "gastronomy" in activities else ''}

Create a day-by-day personalized travel itinerary with:
- In the header of each day, print "Day (number of day, i.e. Day 1) - (date of that day, i.e. 04/05/2025)
- 2-3 recommended activities per day
- Kid-friendly ideas if kids are included
- Restaurant suggestions if gastronomy is selected (respect allergies)
- Useful phrases in the local language (post them once at the end, after the day-by-day plan. MAKE SURE IT'S PRINTED AT THE END IN THEIR OWN POINT)

End with: “This plan will be sent by email.”

Do not include instructions or code. Just return the trip plan.
"""

    with st.spinner("Generating your travel plan..."):
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }

        res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)

        if res.status_code == 200:
            result = res.json()["choices"][0]["message"]["content"]
            st.success("Here's your custom travel plan!")
            st.markdown(result)
            send_email(
                to_email=email,
                subject="Your Personalized Travel Itinerary ✈️",
                content=result
            )
        else:
            st.error(f"OpenAI request failed: {res.status_code}")
            st.text(res.text)
