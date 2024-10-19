from interfaces.aiport_repository import AirportRepository
import requests

class OpenFlightsAirportRepository(AirportRepository):
    def get_airport_coordinates(self, iata_code):
        airports_url = 'https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat'
        response = requests.get(airports_url)
        airports_data = response.text.splitlines()

        for airport in airports_data:
            fields = airport.split(',')
            if fields[4].strip('"') == iata_code:
                lat = float(fields[6])
                lon = float(fields[7])
                return lat, lon
        return None, None
