from interfaces.aiport_repository import AirportRepository
import requests


class OpenFlightsAirportRepository(AirportRepository):
    def __init__(self):
        self.airports_url = 'https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat'

    def get_airport_coordinates(self, iata_code):
        response = requests.get(self.airports_url)
        airports_data = response.text.splitlines()

        for airport in airports_data:
            fields = airport.split(',')
            if fields[4].strip('"') == iata_code:
                lat = float(fields[6])
                lon = float(fields[7])
                return lat, lon
        return None, None

    # Nueva función para buscar aeropuertos por ciudad o país
    def search_airports(self, query):
        response = requests.get(self.airports_url)
        airports_data = response.text.splitlines()

        results = []
        for airport in airports_data:
            fields = airport.split(',')
            city = fields[2].strip('"').lower()
            country = fields[3].strip('"').lower()
            name = fields[1].strip('"')
            iata_code = fields[4].strip('"')

            # Filtrar por ciudad o país
            if query.lower() in city or query.lower() in country:
                results.append({
                    'name': name,
                    'city': city.capitalize(),
                    'country': country.capitalize(),
                    'iata': iata_code
                })

        return results
