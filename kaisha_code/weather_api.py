import requests
import sqlite3


DB_NAME = "database.db"
import os
print("DB PATH:", os.path.abspath(DB_NAME))

API_KEY = "zpka_f178601ddd9f4fbc9eac72977020ad79_0b813b45"


# Function 1: 
def get_location_key(city_name):
    api_key = API_KEY
    url = "http://dataservice.accuweather.com/locations/v1/cities/search"

    params = {"apikey": api_key, "q": city_name}
    response = requests.get(url, params=params)
    data = response.json()

    print("STATUS CODE:", response.status_code)
    print("LOCATION RESPONSE:", data)

    # If AccuWeather returns an error dict
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

    print("WEATHER RESPONSE:", data)

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
            FOREIGN KEY (location_id) REFERENCES locations(id)
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
    location_id = cur.fetchone()[0]

   
    cur.execute("SELECT COUNT(*) FROM weather_conditions")
    current_count = cur.fetchone()[0]

    if current_count >= 25:
        print("Limit reached: Only storing 25 weather entries per run.")
        conn.close()
        return

    # -----------------------------
    # 3. INSERT weather data
    # -----------------------------
    cur.execute("""
        INSERT INTO weather_conditions (location_id, temperature, humidity,
                                        weather_text, is_daytime, observation_time)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        location_id,
        weather_dict["temperature"],
        weather_dict["humidity"],
        weather_dict["weather_text"],
        weather_dict["is_daytime"],
        weather_dict["observation_time"]
    ))

    conn.commit()
    conn.close()
    print(f"Weather data for {city_name} stored successfully!")



# ------------------------------------------------------------
# MAIN (test runner)
# ------------------------------------------------------------
if __name__ == "__main__":
    # Example test to insert 1 city
    city = "Ann Arbor"

    create_tables()

    loc_key, country = get_location_key(city)

if not loc_key:
    print("Stopping — no location key.")
else:
    weather_info = get_weather_data(loc_key)
    store_weather_data(city, weather_info, loc_key, country)
