def bellman_ford(routes, origin):
    dist = {}
    predecessors = {}

    # Initialize all airports in the graph
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

    # Distance to origin is 0
    dist[origin] = 0

    # Find maximum time and price for normalization
    max_time = max(float(route.get('duration', 0)) for route in routes if 'duration' in route)
    max_price = max(float(route.get('price', 0)) for route in routes if 'price' in route)

    print(f"max_time: {max_time}, max_price: {max_price}")  # This prints the max time and price

    # Relaxation of edges
    for _ in range(len(dist) - 1):
        for route in routes:
            for segment in route['segments']:
                source = segment['departure']['iataCode']
                destination = segment['arrival']['iataCode']

                # Convert 'duration' to minutes and 'price' to float
                duration = route.get('duration', 0)
                price = route.get('price', '0')

                # Convert duration and price to numbers
                weight = float(duration)
                price = float(price)

                print(f"Processing route: {source} -> {destination}, weight = {weight}, price = {price}")

                # Normalize time and price
                normalized_time = weight / max_time
                normalized_price = price / max_price

                # Adjusted formula: sum the normalized time and price
                combined_weight = normalized_time + normalized_price

                print(f"Route {source} -> {destination}: duration = {weight} min (normalized: {normalized_time}), price = {price} EUR (normalized: {normalized_price}), combined weight = {combined_weight}")

                if dist[source] + combined_weight < dist[destination]:
                    dist[destination] = dist[source] + combined_weight
                    predecessors[destination] = route

    # Get the best route with the least combined weight
    best_route = min(routes, key=lambda x: dist.get(x['segments'][-1]['arrival']['iataCode'], float('inf')))

    print("Best route selected:", best_route)  # This prints the best route selected
    return best_route
