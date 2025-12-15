import requests
import sqlite3
import os

DB_NAME = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database.db"))
API_KEY = "zpka_f178601ddd9f4fbc9eac72977020ad79_0b813b45"


# Function 1: 
def get_location_key(city_name):
    api_key = API_KEY
    url = "http://dataservice.accuweather.com/locations/v1/cities/search"

    params = {"apikey": api_key, "q": city_name}
    response = requests.get(url, params=params)
    data = response.json()

    if isinstance(data, dict):
        print("AccuWeather error:", data)
        return None, None

    if not data:
        print("No location found for:", city_name)
        return None, None

    location_key = data[0]["Key"]
    country = data[0]["Country"]["LocalizedName"]

    return location_key, country


# Function 2
    
def get_weather_data(location_key):
    
    api_key = API_KEY
    url = f"http://dataservice.accuweather.com/currentconditions/v1/{location_key}"

    params = {
        "apikey": api_key,
        "details": "true"
    }

    response = requests.get(url, params=params)
    data = response.json()


    if not data:
        print("No weather data returned.")
        return None

    weather_info = data[0]

    weather_dict = {
        "temperature": weather_info["Temperature"]["Metric"]["Value"],
        "humidity": weather_info.get("RelativeHumidity"),
        "weather_text": weather_info["WeatherText"],
        "is_daytime": weather_info["IsDayTime"],
        "observation_time": weather_info["LocalObservationDateTime"]
    }

    return weather_dict

def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # locations table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city_name TEXT UNIQUE,
            country TEXT,
            location_key TEXT UNIQUE
        )
    """)

    # weather_conditions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weather_conditions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER,
            temperature REAL,
            humidity REAL,
            weather_text TEXT,
            is_daytime INTEGER,
            observation_time TEXT,
            FOREIGN KEY (location_id) REFERENCES locations(id),
            UNIQUE (location_id, observation_time)
        )
    """)

    conn.commit()
    conn.close()


# Function 3: store_weather_data

def store_weather_data(city_name, weather_dict, location_key, country):
    create_tables()

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO locations (city_name, country, location_key)
        VALUES (?, ?, ?)
    """, (city_name, country, location_key))
    conn.commit()

    cur.execute("SELECT id FROM locations WHERE location_key = ?", (location_key,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False
    location_id = row[0]

    cur.execute("""
        INSERT OR IGNORE INTO weather_conditions (
            location_id, temperature, humidity, weather_text, is_daytime, observation_time
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        location_id,
        weather_dict["temperature"],
        weather_dict["humidity"],
        weather_dict["weather_text"],
        int(weather_dict["is_daytime"]),
        weather_dict["observation_time"]
    ))

    conn.commit()
    inserted = cur.rowcount > 0
    conn.close()

    if inserted:
        print(f"Stored weather for {city_name}")
    else:
        print(f"Skipped duplicate weather row for {city_name}")

    return inserted

def get_existing_city_names():
    create_tables()
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT city_name FROM locations")
    existing = {row[0] for row in cur.fetchall()}
    conn.close()
    return existing


def get_next_city_batch(all_cities, batch_size=25):
    existing = get_existing_city_names()
    remaining = [city for city in all_cities if city not in existing]
    return remaining[:batch_size]

if __name__ == "__main__":
    ALL_CITIES = [
        "Ann Arbor", "Detroit", "Lansing", "Grand Rapids", "Kalamazoo", "Flint", "Saginaw", "Bay City", "Midland",
        "Traverse City", "Marquette", "Muskegon", "Holland", "Jackson", "Monroe", "Port Huron", "Pontiac",
        "Royal Oak", "Dearborn", "Novi", "Troy", "Livonia", "Warren", "Sterling Heights", "Bloomfield Hills",

        "Chicago", "Milwaukee", "Madison", "Minneapolis", "St. Paul", "Indianapolis", "Columbus", "Cleveland",
        "Cincinnati", "Pittsburgh", "Buffalo", "Rochester", "Syracuse", "Albany", "New York", "Newark",
        "Philadelphia", "Baltimore", "Washington", "Richmond", "Charlotte", "Raleigh", "Atlanta", "Nashville",
        "Louisville", "St. Louis", "Kansas City", "Omaha", "Denver", "Salt Lake City", "Phoenix", "Tucson",
        "Las Vegas", "Los Angeles", "San Diego", "San Jose", "San Francisco", "Sacramento", "Portland", "Seattle",
        "Spokane", "Boise", "Albuquerque", "El Paso", "Dallas", "Fort Worth", "Austin", "San Antonio", "Houston",
        "New Orleans", "Baton Rouge", "Jacksonville", "Orlando", "Tampa", "Miami",

        "Boston", "Providence", "Hartford", "New Haven", "Bridgeport", "Norfolk", "Virginia Beach",
        "Charleston", "Savannah", "Birmingham", "Memphis", "Knoxville", "Chattanooga", "Little Rock",
        "Oklahoma City", "Tulsa", "Wichita", "Des Moines", "Sioux Falls", "Fargo", "Billings", "Cheyenne",
        "Reno", "Fresno", "Oakland", "Long Beach", "Anaheim", "Santa Ana", "Irvine", "Bakersfield", 

        "San Bernardino", "Riverside", "Santa Monica", "Pasadena", "Burbank",
        "Glendale", "Pomona", "Ontario", "Corona", "Temecula",
        "Modesto", "Stockton", "Salinas", "Santa Cruz", "Gilroy",
        "Redwood City", "Palo Alto", "Mountain View", "Sunnyvale", "Cupertino",
        "Fremont", "Hayward", "Union City", "San Mateo", "Daly City",
        "South San Francisco", "San Bruno", "Millbrae", "Burlingame", "Foster City",
        "Menlo Park", "Los Gatos", "Campbell", "Milpitas", "Santa Clara",
        "Redlands", "Yucaipa", "Upland", "Rancho Cucamonga", "Claremont",
        "La Verne", "Pomona", "Monrovia", "Arcadia", "Azusa", "Covina"

    ]

    batch = get_next_city_batch(ALL_CITIES, batch_size=25)

    if not batch:
        print("No new cities left to insert (you may already have all cities in ALL_CITIES).")
        raise SystemExit

    successful_inserts = 0

    for city in batch:
        loc_key, country = get_location_key(city)
        if not loc_key:
            continue

        weather_info = get_weather_data(loc_key)
        if not weather_info:
            continue

        inserted = store_weather_data(city, weather_info, loc_key, country)
        if inserted:
            successful_inserts += 1

        if successful_inserts >= 25:
            break

    print(f"Run complete. Inserted {successful_inserts} new weather rows this run.")
    print("Re-run the script to insert the next batch of up to 25 cities.")