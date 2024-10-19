from frameworks.flask.flask_app import create_app
from repositories.openflights_airport_repository import OpenFlightsAirportRepository
from repositories.amadeus_flight_repository import AmadeusFlightRepository
from use_cases.find_best_flight import bellman_ford
from use_cases.calculate_route_duration import convert_duration_to_minutes
import os
from dotenv import load_dotenv

def main():
    load_dotenv()
    api_key = os.getenv('API_KEY')
    api_secret = os.getenv('API_SECRET')

    airport_repository = OpenFlightsAirportRepository()
    flight_repository = AmadeusFlightRepository(api_key, api_secret)

    find_best_flight_use_case = bellman_ford
    calculate_route_duration_use_case = convert_duration_to_minutes

    app = create_app(flight_repository, airport_repository, find_best_flight_use_case, calculate_route_duration_use_case)

    app.run(debug=True)

if __name__ == "__main__":
    main()
