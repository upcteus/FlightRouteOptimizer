from interfaces.flight_repository import FlightRepository
import requests
import os

class AmadeusFlightRepository(FlightRepository):
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    def get_amadeus_token(self):
        url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.api_secret
        }
        response = requests.post(url, headers=headers, data=data)
        return response.json().get("access_token")

    def get_flight_data(self, origin, destination, departure_date):
        token = self.get_amadeus_token()
        url = f"https://test.api.amadeus.com/v2/shopping/flight-offers?originLocationCode={origin}&destinationLocationCode={destination}&departureDate={departure_date}&adults=1"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        return response.json()
