from flask import Flask, request
from flask_cors import CORS
import pandas as pd
import datetime
import shutil
import json
import shapely
import geopandas as gpd
import r5py

# Path: web.py
app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
c_dir = "GTFS_DATA"
transport_network = r5py.TransportNetwork(
    "data/Toronto.osm.pbf",
    [
        "TORONTO_GTFS.zip",
    ]
)

def best_route(
    origin,
    destination
):
    orig = shapely.Point(origin[1], origin[0])
    dest = shapely.Point(destination[1], destination[0])
    print(orig)
    print(dest)
    
    p_origins = gpd.GeoDataFrame(
        {
            "id": [1],
            "geometry": [orig]
        },
        crs="EPSG:4326",
    )

    destinations = gpd.GeoDataFrame(
            {
                "id": [1],
                "geometry": [dest]
            },
            crs="EPSG:4326",
    )

    travel_time_matrix_computer = r5py.DetailedItinerariesComputer(
        transport_network,
        origins=p_origins,
        destinations=destinations,
        departure=datetime.datetime(year=2022, month=9, day=11, hour=6, minute=35),
        transport_modes=[
            r5py.TransportMode.TRANSIT,
            r5py.TransportMode.WALK,
        ],
    )

    g = travel_time_matrix_computer.compute_travel_details()

    return g


def add_route(route_short_name,route_long_name):
    df = pd.read_csv(f'{c_dir}/routes.txt')
    last_route_id = df.tail(1)["route_id"]
    route_id = last_route_id[last_route_id.index[0]] + 1

    df.loc[len(df)] = [
        str(route_id), 
        2, 
        route_short_name, 
        route_long_name, 
        "", # route desc
        3 ,
        "", # route_url,
        "D5C82B", # route_color,
        "000000", # route_text_color
    ]

    return df, route_id

def add_trip(route_id):
    df = pd.read_csv(f'{c_dir}/trips.txt')
    last_trip_id = df.tail(1)["trip_id"]
    trip_id = last_trip_id[last_trip_id.index[0]] + 1

    last_block_id = df.tail(1)["block_id"]
    block_id = last_block_id[last_block_id.index[0]] + 1

    last_shape_id = df.tail(1)["shape_id"]
    shape_id = last_shape_id[last_shape_id.index[0]] + 1

    df.loc[len(df)] = [
        str(route_id),
        str(5), # service id
        str(trip_id),
        "Pool 2", # trip_headsign
        "", # trip_short_name
        1, # direction_id
        str(block_id),
        str(shape_id),
        0, # wheelchair accessible,
        0 # bikes allowed
    ]

    return df, trip_id, block_id, shape_id

def add_stops(route_coords, departure_time, arrival_time, trip_id):
    stop_times = pd.read_csv(f'{c_dir}/stop_times.txt')
    last_stop_id = stop_times.tail(1)["stop_id"]
    stop_id = last_stop_id[last_stop_id.index[0]] + 1

    stops = pd.read_csv(f'{c_dir}/stops.txt')
    last_stop_code = stops.tail(1)["stop_code"]
    stop_code = last_stop_code[last_stop_code.index[0]] + 1

    for i, cord in enumerate(route_coords):
        time_to_use = ""
        if i == 0:
            time_to_use = departure_time
        elif i == len(route_coords) - 1:
            time_to_use = arrival_time

        stop_times.loc[len(stop_times)] = [
            str(trip_id),
            time_to_use, # departure
            time_to_use, # arrival
            stop_id,
            str(i+1), # stop_sequence, goes from order but doesnt matter what number
            "", # stop_headsign
            0, # pickup_type
            0, # drop_off_type,
            "", # dist_traveled - not available
        ]
        stops.loc[len(stops)] = [
            stop_id,
            stop_code,
            f"Carpool stop {i}", # stops dont matter anyway eh
            "", # stop desc
            cord[1],
            cord[0],
            "", # zone_id
            "", # stop_url
            "", # location_type
            "", # parent_station
            "", # stop_timezone
            0, # wheelchair_boarding
        ]
        stop_code += 1
        stop_id += 1
        
    
    return stop_times, stops

def add_shapes(shape_id, coords):
    shapes = pd.read_csv(f'{c_dir}/shapes.txt')

    for i, cord in enumerate(coords):
        shapes.loc[len(shapes)] = [
            str(shape_id),
            cord[1],
            cord[0],
            str(i+1),
            "", # shape_dist_traveled
        ]
    
    return shapes

def save_route(to_put_in, start_time, end_time):
    route, route_id = add_route("Carpool", f"{start_time} Route")
    trip, trip_id, block_id, shape_id = add_trip(route_id)
    stop_times, stops = add_stops(to_put_in, start_time, end_time, trip_id)
    shapes = add_shapes(shape_id, to_put_in)

    route.to_csv(f"{c_dir}/routes.txt", index=False)
    trip.to_csv(f"{c_dir}/trips.txt", index=False)
    stop_times.to_csv(f"{c_dir}/stop_times.txt", index=False)
    stops.to_csv(f"{c_dir}/stops.txt", index=False)
    shapes.to_csv(f"{c_dir}/shapes.txt", index=False)

    shutil.make_archive("TORONTO_GTFS", 'zip', c_dir)

def convert(time_string):
    # Split the string into hours and minutes
    hours, minutes = map(int, time_string.split(":"))

    # Calculate the total seconds
    total_seconds = (hours * 3600) + (minutes * 60)

    return total_seconds

def process(t):
    p = str(datetime.timedelta(seconds=t)).split(":")
    if len(p[0]) == 1:
        p[0] = "0" + p[0]
    
    return ":".join(p)

def find_best_route(start, end):
    return []

def process_route(route):
    cd = []
    for cords in route:
        cd.append(
            [
                float(cords["lng"]),
                float(cords["lat"])
            ]
        )
    return cd


"""    try:
        departure_time = int(convert(departure_time))
        end_time = departure_time + int(travel_time)
        dt_string = process(departure_time)
        et_string = process(end_time)

        try:
            save_route(route, dt_string, et_string)
        except Exception as error:
            print("error saving route:", error)
    except Exception as e:
        print("error on save_route:", e)
        return False

    return True
"""
@app.route('/')
def index():
    return "Hello World!"

@app.route("/api/create_carpool", methods=["POST"])
def create_carpool():
    print(request.method)
    route_data = json.loads(request.data.decode())
    routeLine = process_route(route_data["routeCoordinates"])
    travel_time = int(route_data["estimatedTravelTimeSeconds"])
    departureTime = int(convert(route_data["time"]))
    end_time = departureTime + int(travel_time)

    if save_route(
        routeLine, 
        process(departureTime), 
        process(end_time)):
        return {"status": "success"}, 200
    else:
        return {"status": "failed"}, 500
    

@app.route("/api/best_route")
def best_route():
    coordinates = request.data
    best_route = best_route(coordinates)
    return find_best_route(coordinates)

if __name__ == "__main__":
    app.run(port=8000, debug=False)    