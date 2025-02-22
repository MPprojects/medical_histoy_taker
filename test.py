import google.generativeai as genai
import os

# Set API Key from environment variable
GENAI_API_KEY = "AIzaSyCLSaEQpLhdDDixFem4fNb1Bbrjy5N1O3Q"

if not GENAI_API_KEY:
    raise ValueError("Missing API Key. Set GENAI_API_KEY as an environment variable.")

# Configure the Gemini API
genai.configure(api_key=GENAI_API_KEY)

try:
    # Correct way to generate content
    model = genai.GenerativeModel("gemini-2.0-pro-exp-02-05") 
    response = model.generate_content("Just say: 'API key is working!'")

    print("Model is accessible ")
    print(response.text)
except Exception as e:
    print("Error:", str(e))
