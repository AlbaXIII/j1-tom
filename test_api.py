import requests
import os
from dotenv import load_dotenv

load_dotenv()


API_KEY = os.getenv("API_SPORTS_KEY")

url = 'https://v3.football.api-sports.io/status'
headers = {
    'x-apisports-key': API_KEY
}

response = requests.get(url, headers=headers)
print(response.json())
