from flask import Flask, request, render_template_string
import folium
import requests
from dotenv import load_dotenv
import os

app = Flask(__name__)

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener las claves de API desde el archivo .env
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')

# Función para obtener el token de autenticación de Amadeus
def get_amadeus_token():
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": API_KEY,
        "client_secret": API_SECRET
    }
    response = requests.post(url, headers=headers, data=data)
    return response.json().get("access_token")

# Función para consultar vuelos disponibles entre dos aeropuertos
def get_flight_data(origin, destination, departure_date):
    token = get_amadeus_token()
    url = f"https://test.api.amadeus.com/v2/shopping/flight-offers?originLocationCode={origin}&destinationLocationCode={destination}&departureDate={departure_date}&adults=1"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.json()

# Función para obtener las coordenadas de un aeropuerto basado en su código IATA usando OpenFlights
def get_airport_coordinates(iata_code):
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

# Función para convertir duración en formato 'PTxHxM' o manejar si es un entero
def convert_duration_to_minutes(duration):
    # Verificar si 'duration' es una cadena
    if isinstance(duration, str):
        hours = 0
        minutes = 0
        if 'H' in duration:
            hours = int(duration.split('H')[0].replace('PT', ''))
            if 'M' in duration:
                minutes = int(duration.split('H')[1].replace('M', ''))
        elif 'M' in duration:
            minutes = int(duration.replace('PT', '').replace('M', ''))
        return hours * 60 + minutes
    elif isinstance(duration, int):
        # Si 'duration' ya es un entero (minutos), simplemente lo devolvemos
        return duration
    else:
        # Si 'duration' no es un entero ni una cadena válida, devolver 0
        print(f"Error: Duración no es una cadena ni un entero válido, es de tipo {type(duration)}")
        return 0

# Función para normalizar valores
def normalize(value, max_value):
    if max_value == 0 or max_value is None:
        print(f"Advertencia: valor máximo es 0 o None para {value}, no se puede normalizar")
        return 0
    return value / max_value

# Implementación del algoritmo de Bellman-Ford con normalización y depuración
def bellman_ford(routes, origin):
    dist = {}
    predecessors = {}

    # Inicializar todos los aeropuertos en el grafo
    for route in routes:
        for segment in route['segments']:
            departure = segment['departure']['iataCode']
            arrival = segment['arrival']['iataCode']
            if departure not in dist:
                dist[departure] = float('inf')
                predecessors[departure] = None
            if arrival not in dist:
                dist[arrival] = float('inf')
                predecessors[arrival] = None

    # Distancia al origen es 0
    dist[origin] = 0

    # Encontrar el tiempo máximo y el precio máximo para normalizar
    max_time = max(float(route.get('duration', 0)) for route in routes if 'duration' in route)
    max_price = max(float(route.get('price', 0)) for route in routes if 'price' in route)

    print(f"max_time: {max_time}, max_price: {max_price}")

    # Relajación de las aristas
    for _ in range(len(dist) - 1):
        for route in routes:
            for segment in route['segments']:
                source = segment['departure']['iataCode']
                destination = segment['arrival']['iataCode']

                # Convertir 'duration' a minutos y 'price' a float
                duration = route.get('duration', 0)  # Si no hay duración, usar 0
                price = route.get('price', '0')  # Si no hay precio, usar '0'

                # Convertir duración y precio a números
                try:
                    weight = float(duration)  # Convertir duración a minutos
                    price = float(price)  # Asegurar que el precio sea convertido a número
                except ValueError:
                    # Si no se puede convertir a número, continuar con la siguiente ruta
                    print(f"Error: No se pudo convertir el tiempo o precio a número en la ruta de {source} a {destination}")
                    continue

                print(f"Procesando ruta: {source} -> {destination}, weight = {weight}, price = {price}")

                # Normalización del tiempo y el precio
                normalized_time = normalize(weight, max_time)
                normalized_price = normalize(price, max_price)

                # Fórmula ajustada: sumamos el tiempo y el precio normalizados
                combined_weight = normalized_time + normalized_price

                # Mensaje de depuración para ver el cálculo de la ruta
                print(f"Ruta {source} -> {destination}: duración = {weight} min (normalizado: {normalized_time}), precio = {price} EUR (normalizado: {normalized_price}), peso combinado = {combined_weight}")

                if dist[source] + combined_weight < dist[destination]:
                    dist[destination] = dist[source] + combined_weight
                    predecessors[destination] = route

    # Obtener la mejor ruta con el menor peso combinado
    best_route = min(routes, key=lambda x: dist.get(x['segments'][-1]['arrival']['iataCode'], float('inf')))

    # Imprimir los resultados para depuración
    print("Mejor ruta seleccionada:", best_route)
    return best_route



@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        origin = request.form['origin']
        destination = request.form['destination']
        departure_date = request.form['date']

        flight_data = get_flight_data(origin, destination, departure_date)

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

        best_route = bellman_ford(routes, origin)

        world_map = folium.Map(location=[20, 0], zoom_start=2)

        for segment in best_route['segments']:
            origin_iata = segment['departure']['iataCode']
            destination_iata = segment['arrival']['iataCode']

            lat1, lon1 = get_airport_coordinates(origin_iata)
            lat2, lon2 = get_airport_coordinates(destination_iata)

            if lat1 and lon1 and lat2 and lon2:
                folium.PolyLine([(lat1, lon1), (lat2, lon2)], color='green', weight=5, tooltip="Mejor ruta").add_to(world_map)

                # Añadir marcador para el aeropuerto de salida
                folium.CircleMarker(
                    location=[lat1, lon1],
                    radius=5,
                    color='blue',
                    fill=True,
                    fill_color='blue',
                    fill_opacity=0.7,
                    tooltip=f'Aeropuerto: {origin_iata}'
                ).add_to(world_map)

                # Añadir marcador para el aeropuerto de llegada
                folium.CircleMarker(
                    location=[lat2, lon2],
                    radius=5,
                    color='red',
                    fill=True,
                    fill_color='red',
                    fill_opacity=0.7,
                    tooltip=f'Aeropuerto: {destination_iata}'
                ).add_to(world_map)

        map_html = world_map._repr_html_()

        return render_template_string('''
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Mapa de vuelos y detalles</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        background-color: #f5f7fa;
                        margin: 0;
                        padding: 20px;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                    }

                    #map-container {
                        width: 100%;
                        height: 50vh;
                        margin-top: 20px;
                    }

                    table {
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 20px;
                    }

                    th, td {
                        padding: 10px;
                        border: 1px solid #ddd;
                        text-align: left;
                    }

                    th {
                        background-color: #f2f2f2;
                    }

                    h1 {
                        margin-bottom: 20px;
                    }

                    ul {
                        padding-left: 20px;
                    }
                </style>
            </head>
            <body>
                <h1>Rutas de {{ origin }} a {{ destination }}</h1>
                <div id="map-container">
                    {{ map_html|safe }}
                </div>

                <table>
                    <tr>
                        <th>Duración (min)</th>
                        <th>Escalas</th>
                        <th>Precio</th>
                        <th>Aerolínea</th>
                        <th>Detalles</th>
                    </tr>
                    {% for route in routes %}
                    <tr>
                        <td>{{ route.duration }} min</td>
                        <td>{{ route.stops }}</td>
                        <td>{{ route.price }} {{ route.currency }}</td>
                        <td>
                            {% for segment in route.segments %}
                                {{ segment['carrierCode'] }}<br>
                            {% endfor %}
                        </td>
                        <td>
                            <ul>
                                {% for segment in route.segments %}
                                <li>Vuelo de {{ segment['departure']['iataCode'] }} a {{ segment['arrival']['iataCode'] }} - {{ segment['departure']['at'] }} a {{ segment['arrival']['at'] }}</li>
                                {% endfor %}
                            </ul>
                        </td>
                    </tr>
                    {% endfor %}
                </table>
            </body>
            </html>
        ''', origin=origin, destination=destination, routes=routes, map_html=map_html)

    return render_template_string('''
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Buscar vuelos</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f5f7fa;
                    padding: 20px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                }

                form {
                    display: flex;
                    flex-direction: column;
                    width: 300px;
                }

                label, input {
                    margin-bottom: 10px;
                }

                button {
                    padding: 10px;
                    background-color: #007BFF;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                }

                button:hover {
                    background-color: #0056b3;
                }
            </style>
        </head>
        <body>
            <h1>Buscar vuelos</h1>
            <form method="POST">
                <label for="origin">Aeropuerto de origen (IATA):</label>
                <input type="text" id="origin" name="origin" required>

                <label for="destination">Aeropuerto de destino (IATA):</label>
                <input type="text" id="destination" name="destination" required>

                <label for="date">Fecha de salida (YYYY-MM-DD):</label>
                <input type="text" id="date" name="date" required>

                <button type="submit">Buscar</button>
            </form>
        </body>
        </html>
    ''')

if __name__ == '__main__':
    app.run(debug=True)
