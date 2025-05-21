# Here we import and load all the required libraries
import streamlit as st
import requests
import datetime
from datetime import date, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Here we create a side bar, apart from the main user interface, which will allow the user to put their API keys there, without coveing the main app page.
with st.sidebar:
    st.header("API Keys")
    OPENAI_API_KEY = st.text_input("OpenAI API Key", type="password")
    SENDGRID_API_KEY = st.text_input("SendGrid API Key", type="password")
    SERPAPI_API_KEY = st.text_input("SerpAPI API Key", type="password")
    AVIATIONSTACK_API_KEY = st.text_input("AviationStack API Key", type="password")

itinerary = None #We create this to avoid not having the variable 'itinerary' assigned, since it is placed inside the 'if submitted:' part.
hotel = None     #We create this to avoid not having the variable 'itinerary' assigned, since it is placed inside the 'if submitted:' part.

# Creating a function that extracts the information about the flights
def extract_flight_details(flight):
    if not flight or not isinstance(flight, dict):
        return {}
        
    flights_data = flight.get("flights", [])
    if not flights_data:
        return {}
            
    first_flight = flights_data[0] if flights_data else {}   # We are assigning the first flight from the search, to the variable 'first_flight'
    last_flight = flights_data[-1] if flights_data else {}
    
    # Here we get the name of the airline, flight number & the timings of the flights
    airline = first_flight.get("airline", "Unknown")
    flight_number = first_flight.get("flight_number", "")
    
    departure_time = ""              # creating the variable to avoid errors later on
    arrival_time = ""                # creating the variable to avoid errors later on
    
    if "departure_airport" in first_flight and "time" in first_flight["departure_airport"]:
        departure_time = first_flight["departure_airport"]["time"].split()[1]  # Extract just the time part from outbound airport
        
    if "arrival_airport" in last_flight and "time" in last_flight["arrival_airport"]:
        arrival_time = last_flight["arrival_airport"]["time"].split()[1]  # Extract just the time part from arrival airport
    
    # Total duration of the flight in minutes (better minutes than hours with decimals as no one uses that)
    duration = flight.get("total_duration", 0)
    hours, minutes = divmod(duration, 60)
    duration_formatted = f"{hours}h {minutes}m"
    
    # Number of connections within the flight (lay-over or direct flight)
    connections = len(flights_data) - 1
    connections_text = f"{connections} stop{'s' if connections > 1 else ''}" if connections > 0 else "Direct Flight (NO lay-over)"
        
    return {
        "airline": airline,
        "flight_number": flight_number,
        "departure_time": departure_time,
        "arrival_time": arrival_time,
        "duration": duration_formatted,
        "connections": connections_text
    }


# Function to create price comparison visualization
def create_price_comparison(price, route, travel_class="economy"):
    try:
        # Convert price to float if it's a string with the currency symbol
        if isinstance(price, str):
            price = float(price.replace('$', '').replace('€', '').replace(',', ''))
        elif isinstance(price, (int, float)):
            price = float(price)
        else:
            raise ValueError(f"Unexpected price type: {type(price)}")
        
        # Classification amongst flight ticket (economy, business)
        if travel_class.lower() == "business":
            min_price = price * 0.7
            typical_min = price * 0.85
            typical_max = price * 1.3
            max_price = price * 1.5
            
            comparison_text = f"€{price:.0f} is low for Business Class — €{(typical_min - price):.0f} cheaper than usual"
            price_label = "€{:.0f} is low".format(price)
            
        else:  # Economy class
            min_price = price * 0.8
            typical_min = price * 0.9
            typical_max = price * 1.2
            max_price = price * 1.4
            
            comparison_text = f"€{price:.0f} is average for Economy Class"
            price_label = "€{:.0f} is average".format(price)
            
            # Determine if the price is low, average, or high
        if price < typical_min:
            comparison_text = f"€{price:.0f} is low for Economy Class — €{(typical_min - price):.0f} cheaper than usual"
            price_label = "€{:.0f} is low".format(price)
        elif price > typical_max:
            comparison_text = f"€{price:.0f} is high for Economy Class — €{(price - typical_max):.0f} more than usual"
            price_label = "€{:.0f} is high".format(price)
                
        # Display comparison text
        st.markdown(f"### {comparison_text}")
        
        # Create the visualization
        fig, ax = plt.subplots(figsize=(10, 2))
        
        # Create the backgrounds filled with colors
        ax.axvspan(min_price, typical_min, color='#4CAF50', alpha=0.3)  # Green for low price
        ax.axvspan(typical_min, typical_max, color='#FFC107', alpha=0.3)  # Yellow for average price
        ax.axvspan(typical_max, max_price, color='#F44336', alpha=0.3)  # Red for high price
        
        # Adding a distinguisher for the current price the user will pay 
        ax.scatter(price, 0.5, color='white', s=300, zorder=5, edgecolor='#1E88E5', linewidth=2)
        
        # Adding price labels at the bottom of the graph
        ax.text(min_price, -0.3, f"€{min_price:.0f}", ha='left', va='center', fontsize=10)
        ax.text(typical_min, -0.3, f"€{typical_min:.0f}", ha='center', va='center', fontsize=10)
        ax.text(max_price, -0.3, f"€{max_price:.0f}", ha='right', va='center', fontsize=10)
        
        # Personalization of layout of the bubble with text inside
        ax.annotate(price_label, 
            xy=(price, 0.5),
            xytext=(price, 0.9),
            ha='center',
            va='center',
            bbox=dict(boxstyle="round,pad=0.5", fc='#1E88E5', alpha=0.8, ec="none"),
            color='white',
            fontsize=10)
        
        # Removing the axes and the spines
        ax.set_yticks([])
        ax.set_xticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
            
        # Setting limits
        ax.set_xlim(min_price * 0.95, max_price * 1.05)
        ax.set_ylim(-0.5, 1.5)
        
        # Outputting the plot
        st.pyplot(fig)
        
    except Exception as e:
        st.warning(f"Could not create price comparison visualization. Error: {str(e)}")

st.title("Personalized Travel Planner with Flight & Hotel Finder")

# Asking the user to input information on the main tab of the app
email = st.text_input("Your Email")
origin_code = st.text_input("Origin Airport Code (for example: 'BCN')", max_chars=3)
destination_code = st.text_input("Destination Airport Code (for example: 'MAD')", max_chars=3)
trip_range = st.date_input(
    "Trip Dates (select start & end date)",
    value=(date.today() + timedelta(days=7), date.today() + timedelta(days=10)),  # we add default value so it looks nicer and is more intuitive to fill out
    min_value=date.today() # we add this so it is not possible to check flights in the past
)
start_date, end_date = trip_range   #We need to add this line since the same line is kept inside "if submitted" part & not outside so it gives error otherwise
activities = st.multiselect(
    "Preferred Type of Activities",
    ["Adventures", "Historical", "Gastronomy", "Romantic"]
) 
has_kids = st.checkbox("Are you traveling with kids?")
kids_ages = ""
# this part is conditional since it only appears if the user selects or marks a box
if has_kids:
    kids_ages = st.text_input("Enter kid(s) age(s) (for example: 5, 9)")

allergies = ""
if "Gastronomy" in activities:
    allergies = st.text_area("Any food allergies or dietary restrictions?")

submitted = st.button("Generate My Plan & Flights")   # this is the button that will need to be clicked and will start the entire automation of processes 

#Once the 'Generate' button is clicked, it has to check if there is any required data that is missing. This is done below:

# First, Check for missing API keys
if submitted:
    validation_errors = []
    
    if not OPENAI_API_KEY:
        validation_errors.append("⚠️Please enter your OPENAI API key on the sidebar⚠️")
    if not SENDGRID_API_KEY:
        validation_errors.append("⚠️Please enter your SENDGRID API key on the sidebar⚠️")
    if not SERPAPI_API_KEY:
        validation_errors.append("⚠️Please enter your SERPAPI API key on the sidebar⚠️") 
    if not AVIATIONSTACK_API_KEY:
        validation_errors.append("⚠️Please enter your AVIATIONSTACK API key on the sidebar⚠️")
        
        # Continue checking for the other inputs (email, airport codes, dates, etc) or the length of the input (Airport data has to be 3 characters long)
    if not email:
        validation_errors.append("⚠️Email is required⚠️")
    if not origin_code or len(origin_code) != 3:
        validation_errors.append("⚠️Origin airport code must be 3-letters-long⚠️")
    if not destination_code or len(destination_code) != 3:
        validation_errors.append("⚠️Destination airport code must be 3 letters long⚠️")
    if not trip_range:
        validation_errors.append("⚠️Trip Dates is required⚠️")
    if has_kids and not kids_ages:
        validation_errors.append("⚠️Please provide your kids' ages⚠️")
    if "Gastronomy" in activities and not allergies:
        validation_errors.append("⚠️Please provide allergy/dietary info⚠️")

    if validation_errors:
        for err in validation_errors:
            st.error(err)
    else:
        start_date, end_date = trip_range
        params_hotel = {                          # if some input is missing, display error message saying that X information is missing. 
            "q": destination_code,                # Otherwise, if the required information is correct, then use these hotel parameters
            "check_in_date": start_date,
            "check_out_date": end_date,
            "hl": "en",
            "gl": "es",
            "currency": "EUR",
            "api_key": SERPAPI_API_KEY
        }

        hotel_results = requests.get("https://serpapi.com/search.json?engine=google_hotels", params=params_hotel).json() # GET request for google_hotels

        hotel = hotel_results.get("properties", [])[0] if hotel_results.get("properties") else None # only selecting the top 1 hotel from the json response

        if hotel:
            st.subheader("Top Hotel Recommendation")    # Title of the section
            st.markdown(f"**Hotel Name: {hotel.get('name', 'N/A')}**")  # The name of the hotel
            st.markdown(f"Total Stay Cost: {hotel.get('total_rate', {}).get('lowest', 'N/A')}") # Total price the user pays on the dates and hotel chosen
            st.markdown(f"Hotel Description: {hotel.get('description', 'No description available')}")  # The description of the chosen hotel
            st.markdown(f"[Hotel's Website]({hotel.get('link', '')})")  # This is the official website of the chosen hotel
        else:
            st.markdown("No hotel data available.")   #If there was an error, it would print out this text

        # Here we are building the query/prompt that will be passed on to OpenAI API later on, by using the variables of input that the user has written
        prompt = f"""
You are a travel assistant. Here's the user's input:

* Email: {email}
* Origin Airport: {origin_code}
* Destination Airport and city they will be visiting during the trip: {destination_code}
* Activities: {', '.join(activities)}
* Kids: {'Yes, ages: ' + kids_ages if has_kids else 'No'}
* Dates: {start_date} to {end_date}
{"- Allergies: " + allergies if "Gastronomy" in activities else ''}

Create a day-by-day personalized travel itinerary with:

* In the header of each day, print "Day (number of day, i.e. Day 1) - (date of that day, i.e. 04/05/2025), make sure the headers are in bold
* 2-3 recommended activities per day (make sure the proposed plans are in the destination city centre)
* Kid-friendly ideas if kids are included
* Restaurant suggestions if gastronomy is selected (respect allergies)
* "Useful phrases" Useful phrases in the local language of THE DESTINATION CITY and how to pronounce them (post them once at the end, after the day-by-day plan. MAKE SURE IT'S PRINTED AT THE END IN THEIR OWN POINT. Example: If they travel from BCN to JFK, include how sentences that they will need while in JFK are done in English compared to Spanish. "Una mesa para cuatro personas" -> "A table for 4 people". 
DO NOT INCLUDE THE USEFUL PHRASES SECTION IF: the user is travelling from and to countries where the same language is spoken (USA to UK, or from Mexico to Spain).
"""
        # Here we create the spinning loading wheel and specify the information for the OpenAI API
        with st.spinner("Generating your Travel Plan..."):
            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)  # the post request passing it to OpenAI
            
            if res.status_code == 200:                                         # If the request is successful, run those 3 lines
                itinerary = res.json()["choices"][0]["message"]["content"]
                st.markdown(itinerary)
                st.success("✅ Your TRAVEL ITINERARY & FLIGHTS were emailed to you!")
            else:                                                              # If the request is NOT successful, run thEse 3 lines instead
                st.error(f"OpenAI error: {res.status_code}")
                st.text(res.text)
                itinerary = ""


        # Here we create the spinning wheel and set the parameters for the google_flights API, which is inside of SerpAPI
        with st.spinner("Searching for flights..."):
            outbound_params = {
                "departure_id": origin_code,
                "arrival_id": destination_code,
                "outbound_date": start_date.strftime("%Y-%m-%d"),
                "currency": "EUR",
                "hl": "en",
                "api_key": SERPAPI_API_KEY,
                "type": "2"
            }                                                # Important to split it into 2 since we have 2 different flights and thus different parameters. 
            return_params = {                                # I think there is the feature of both-ways flights with the 'type' but I think it is better as is
                "departure_id": destination_code,
                "arrival_id": origin_code,
                "outbound_date": end_date.strftime("%Y-%m-%d"),
                "currency": "EUR",
                "hl": "en",
                "api_key": SERPAPI_API_KEY,
                "type": "2"
            }
        out_res = requests.get("https://serpapi.com/search.json?engine=google_flights", params=outbound_params)  # GET request for the outbound flight
        ret_res = requests.get("https://serpapi.com/search.json?engine=google_flights", params=return_params)    # GET request for the return flight
    
                
        out_flights = out_res.json().get("best_flights", []) if out_res.status_code == 200 else []  # from the outbound flight search, take the best flights
        ret_flights = ret_res.json().get("best_flights", []) if ret_res.status_code == 200 else []  # from the return flight search, take the best flights
    
        if out_flights and ret_flights:
            out_flight = out_flights[0]
            ret_flight = ret_flights[0]
    
            outbound_details = extract_flight_details(out_flight)
            return_details = extract_flight_details(ret_flight)
    
            try:
                out_price = float(out_flight.get("price", "0").replace("$", "").replace(",", ""))     # converting variable types so there are no issues
                ret_price = float(ret_flight.get("price", "0").replace("$", "").replace(",", ""))
                total = out_price + ret_price
                price_text = f"€{total:.2f}"
            except:
                price_text = f"{out_flight.get('price', 'N/A')}€ + {ret_flight.get('price', 'N/A')}€" # joining the individual flight prices into 1 variable

                
            # Adding the title of 'Flights Information' on the output of the app
            st.markdown("<h3 style='color: blue;'>Flights Information</h3>", unsafe_allow_html=True)

            # Then, here, we display all the actual details about the flights
            st.markdown(f"""
            <div style='padding: 15px; background-color: #f0f2f6;'>
                <h3>✈️ Roundtrip Summary</h3>
                <p><strong>From:</strong> {origin_code}</p>
                <p><strong>To:</strong> {destination_code}</p>
                <p><strong>Dates:</strong> {start_date} → {end_date}</p>
                <p><strong>Estimated Total:</strong> {price_text}</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style='padding: 15px; background-color: #f0f2f6;'>
                <h4>Outbound Flight</h4>
                <p><strong>{outbound_details.get('airline', 'N/A')} {outbound_details.get('flight_number', '')}</strong></p>
                <p>{outbound_details.get('connections', 'N/A')}</p>
                <p><strong>{outbound_details.get('departure_time', 'N/A')}h</strong> {origin_code} → <strong>{outbound_details.get('arrival_time', 'N/A')}h</strong> {destination_code}</p>
                <p>Duration: {outbound_details.get('duration', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='padding: 15px; background-color: #f0f2f6;'>
                <h4>Return Flight</h4>
                <p><strong>{return_details.get('airline', 'N/A')} {return_details.get('flight_number', '')}</strong></p>
                <p>{return_details.get('connections', 'N/A')}</p>
                <p><strong>{return_details.get('departure_time', 'N/A')}h</strong> {destination_code} → <strong>{return_details.get('arrival_time', 'N/A')}h</strong> {origin_code}</p>
                <p>Duration: {return_details.get('duration', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
    

# Adding the title for the graph part.
st.markdown("### Price Comparison")
                
                # Doing the visualization
try:
    out_price = out_flight.get("price", 0)
    if isinstance(out_price, str):
        out_price = float(out_price.replace("$", "").replace("€", "").replace(",", ""))
        
    # Create outbound price comparison
    st.subheader("Outbound Flight Price Comparison")
    create_price_comparison(out_price, f"{origin_code}-{destination_code}")
    
    # Get return price for visualization
    ret_price = ret_flight.get("price", 0)
    if isinstance(ret_price, str):
        ret_price = float(ret_price.replace("$", "").replace("€", "").replace(",", ""))
    
    # Create return price comparison
    st.subheader("Return Flight Price Comparison")
    create_price_comparison(ret_price, f"{destination_code}-{origin_code}")
            
except Exception as e:
    st.warning(f"Could not generate price comparison: {str(e)}")


def fetch_historical_flight_prices(origin_code, destination_code, AVIATIONSTACK_API_KEY):
    url = "https://api.aviationstack.com/v1/historical"
    params = {
        "access_key": AVIATIONSTACK_API_KEY,
        "departure_icao": origin_code,
        "arrival_icao": destination_code,
        "limit": 1000  # We want to fetch as much data as possible here
    }
    response = requests.get(url, params=params)
    return response.json()

if submitted:
    price_data = fetch_historical_flight_prices(origin_code, destination_code, AVIATIONSTACK_API_KEY)

    past_prices = []
    past_dates = []
    
    for flight in price_data.get("data", []):
        if "price" in flight and "date" in flight:
            past_prices.append(flight["price"])
            past_dates.append(flight["date"])

    if past_prices:
        st.subheader("Flight Price Trend Over Last 5 Years")

        # Plotting the data
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(past_dates, past_prices, marker="o", linestyle="-", color="b")
        ax.set_xlabel("Date")
        ax.set_ylabel("Price (€)")
        ax.set_title(f"Price Trend for {origin_code} → {destination_code}")
        ax.tick_params(axis="x", rotation=45)

        st.pyplot(fig)

        # Short summary
        current_flight_price = past_prices[-1] if past_prices else None
        historical_avg_price = sum(past_prices) / len(past_prices) if past_prices else None

        if current_flight_price and historical_avg_price:
            if current_flight_price < historical_avg_price:
                st.success(f"✅ The current price (€{current_flight_price}) is **below average** historical prices (€{historical_avg_price:.2f}).")
            else:
                st.warning(f"⚠️ The current price (€{current_flight_price}) is **above average** historical prices (€{historical_avg_price:.2f}).")
    else:
        st.warning("No historical flight price data.")



# Creating the function that will send an email (POST request), and setting its parameters (API url, subject, content, subject, etc)
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
        "content": [{"type": "text/plain", "value": content}]
    }
    requests.post(url, headers=headers, json=data)

# Create the variable name to avoid an error
outbound_flight_info = ""
return_flight_info = ""
        
if 'outbound_details' in locals() and outbound_details:    #Since price_text on the app output contains the total price of both flights...
    outbound_price = out_flight.get('price', 'N/A') if 'out_flight' in locals() else 'N/A' #...We need this line to split it individually
    outbound_flight_info = f"""
    
OUTBOUND FLIGHT:
{outbound_details.get('airline', 'N/A')} {outbound_details.get('flight_number', '')}
{origin_code} {outbound_details.get('departure_time', 'N/A')}h → {destination_code} {outbound_details.get('arrival_time', 'N/A')}h
Duration: {outbound_details.get('duration', 'N/A')} | {outbound_details.get('connections', 'N/A')}
Price: {outbound_price}€
"""
        
if 'return_details' in locals() and return_details:      #Since price_text contains the total price of both flights...
    return_price = ret_flight.get('price', 'N/A') if 'ret_flight' in locals() else 'N/A'      #...We need this line to split it individually
    return_flight_info = f"""
    
RETURN FLIGHT:
{return_details.get('airline', 'N/A')} {return_details.get('flight_number', '')}
{destination_code} {return_details.get('departure_time', 'N/A')}h → {origin_code} {return_details.get('arrival_time', 'N/A')}h
Duration: {return_details.get('duration', 'N/A')} | {return_details.get('connections', 'N/A')}
Price: {return_price}€
"""

# Here we provide all the details for the email (content, subject, destinatary, etc)
email_body = f"""Trip Summary for {origin_code} → {destination_code}
Dates: {start_date} to {end_date}

{outbound_flight_info}
{return_flight_info}

--- ITINERARY ---
{itinerary}
"""
# Here it finishes setting the details for the mail and actually uses the function and applies the different parts (to_emaik, subject and content).
send_email(
    to_email=email,
    subject=f"Your Travel Plan & Flights: {origin_code} to {destination_code}",
    content=email_body
)