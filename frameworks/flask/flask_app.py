from flask import Flask, request, render_template
from use_cases.find_best_flight import bellman_ford
from use_cases.calculate_route_duration import convert_duration_to_minutes
import folium
from repositories.amadeus_flight_repository import AmadeusFlightRepository
from repositories.openflights_airport_repository import OpenFlightsAirportRepository

def create_app(flight_repository, airport_repository, find_best_flight_use_case, calculate_route_duration_use_case):
    app = Flask(__name__)

    @app.route('/', methods=['GET', 'POST'])
    def home():
        if request.method == 'POST':
            origin = request.form['origin']
            destination = request.form['destination']
            departure_date = request.form['date']

            flight_data = flight_repository.get_flight_data(origin, destination, departure_date)

            routes = []
            if 'data' in flight_data:
                for flight in flight_data['data']:
                    itineraries = flight['itineraries']
                    price = flight['price']['total']
                    currency = flight['price']['currency']
                    for itinerary in itineraries:
                        duration = itinerary['duration']
                        segments = itinerary['segments']
                        stops = len(segments) - 1
                        formatted_duration = convert_duration_to_minutes(duration)
                        route = {
                            'duration': formatted_duration,
                            'stops': stops,
                            'price': price,
                            'currency': currency,
                            'segments': segments
                        }
                        routes.append(route)

            if not routes:
                return render_template('index.html', error="No flights found")

            best_route = bellman_ford(routes, origin)

            world_map = folium.Map(location=[20, 0], zoom_start=2)

            for segment in best_route['segments']:
                origin_iata = segment['departure']['iataCode']
                destination_iata = segment['arrival']['iataCode']

                lat1, lon1 = airport_repository.get_airport_coordinates(origin_iata)
                lat2, lon2 = airport_repository.get_airport_coordinates(destination_iata)

                if lat1 and lon1 and lat2 and lon2:
                    folium.PolyLine([(lat1, lon1), (lat2, lon2)], color='green', weight=5, tooltip="Best route").add_to(world_map)

                # Add circle markers for origin and destination airports
                folium.CircleMarker(
                    location=[lat1, lon1],
                    radius=8,
                    color='blue',
                    fill=True,
                    fill_color='blue',
                    fill_opacity=0.7,
                    tooltip=f'Origin: {origin_iata}'
                ).add_to(world_map)

                folium.CircleMarker(
                    location=[lat2, lon2],
                    radius=8,
                    color='red',
                    fill=True,
                    fill_color='red',
                    fill_opacity=0.7,
                    tooltip=f'Destination: {destination_iata}'
                ).add_to(world_map)

            map_html = world_map._repr_html_()

            return render_template('search.html', origin=origin, destination=destination, routes=routes, map_html=map_html)

        return render_template('index.html')

    return app
