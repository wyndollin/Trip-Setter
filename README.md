# Trip-Setter ✈️

A smart travel itinerary planner that creates personalized travel plans using AI. This web application helps users plan their trips by generating custom itineraries based on their preferences, including activities, dining options, and local language tips.

## Features

- 📅 Day-by-day itinerary planning
- 🎯 Personalized activity recommendations
- 👶 Kid-friendly suggestions
- 🍽️ Restaurant recommendations with allergy considerations
- 🗣️ Local language phrase suggestions
- 📧 Email delivery of itineraries

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

1. Clone the repository:
```bash
git clone https://github.com/wyndollin/Trip-Setter.git
cd Trip-Setter
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Configuration

The application requires the following API keys:
- OpenAI API key
- SendGrid API key

For security reasons, it's recommended to use environment variables for the API keys instead of hardcoding them in the source code.

## Usage

1. Run the Streamlit application:
```bash
streamlit run TJ_app2.py
```

2. Open your web browser and navigate to the provided local URL (typically http://localhost:8501)

3. Fill in the required information:
   - Email address
   - Phone number
   - Destination city and country
   - Trip dates
   - Interests/activities
   - Additional preferences (kids, allergies, etc.)

4. Click "Generate Travel Plan" to receive your personalized itinerary

## Security Notes

- Store API keys securely using environment variables
- Never commit API keys to version control
- Use appropriate error handling for API calls

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
