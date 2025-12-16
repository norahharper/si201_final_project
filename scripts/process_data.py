import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "database.db")
)

OUTFILE = "calculated_results.txt"

def get_connection():
    return sqlite3.connect("data/database.db")


def calc_weather_summary():
    conn = get_connection()
    cur = conn.cursor()

    # JOIN: locations.id -> weather_conditions.location_id
    cur.execute("""
        SELECT
            l.city_name,
            l.country,
            COUNT(*) AS obs_count,
            ROUND(AVG(w.temperature), 2) AS avg_temp_c,
            ROUND(AVG(w.humidity), 2) AS avg_humidity,
            SUM(CASE WHEN w.is_daytime = 1 THEN 1 ELSE 0 END) AS daytime_obs
        FROM weather_conditions w
        JOIN locations l ON w.location_id = l.id
        GROUP BY l.city_name, l.country
        ORDER BY obs_count DESC, avg_temp_c DESC;
    """)
    rows = cur.fetchall()

    # overall summary too
    cur.execute("""
        SELECT
            COUNT(*) AS total_obs,
            ROUND(AVG(temperature), 2) AS overall_avg_temp_c,
            ROUND(AVG(humidity), 2) AS overall_avg_humidity
        FROM weather_conditions;
    """)
    overall = cur.fetchone()

    conn.close()

    return {
        "overall": overall,
        "by_city": rows
    }


def calc_aqi_summary():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COUNT(*) AS total_rows,
            ROUND(AVG(aqi), 2) AS avg_aqi,
            MIN(aqi) AS min_aqi,
            MAX(aqi) AS max_aqi
        FROM aqi_data;
    """)
    result = cur.fetchone()
    conn.close()
    return result


def calc_bird_summary():
    conn = get_connection()
    cur = conn.cursor()

    # Total number of bird observations
    cur.execute("SELECT COUNT(*) FROM bird_data;")
    total_rows = cur.fetchone()[0]

    # Top 10 bird species by number of observations
    cur.execute("""
        SELECT
            comName,
            COUNT(*) AS sightings
        FROM bird_data
        GROUP BY comName
        ORDER BY sightings DESC
        LIMIT 10;
    """)
    top_species = cur.fetchall()

    conn.close()
    return total_rows, top_species

def write_report(weather_summary, aqi_summary, bird_summary):
    with open(OUTFILE, "w") as f:
        f.write("SI201 Final Project — Calculated Results\n")
        f.write(f"Generated: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"Database: {DB_PATH}\n\n")

        # Weather overall
        total_obs, overall_avg_temp_c, overall_avg_humidity = weather_summary["overall"]
        f.write("WEATHER (JOIN: locations + weather_conditions) \n")
        f.write(f"Total weather observations: {total_obs}\n")
        f.write(f"Overall avg temperature (C): {overall_avg_temp_c}\n")
        f.write(f"Overall avg humidity: {overall_avg_humidity}\n\n")

        # Weather by city (top 10)
        f.write("Top 10 cities by number of weather observations:\n")
        f.write("city | country | obs_count | avg_temp_c | avg_humidity | daytime_obs\n")
        for row in weather_summary["by_city"][:10]:
            city, country, obs_count, avg_temp_c, avg_humidity, daytime_obs = row
            f.write(f"{city} | {country} | {obs_count} | {avg_temp_c} | {avg_humidity} | {daytime_obs}\n")
        f.write("\n")

        # AQI summary
        f.write("AQI\n")
        if aqi_summary:
            total_rows, avg_aqi, min_aqi, max_aqi = aqi_summary
            f.write(f"Total AQI rows: {total_rows}\n")
            f.write(f"Avg AQI: {avg_aqi}\n")
            f.write(f"Min AQI: {min_aqi}\n")
            f.write(f"Max AQI: {max_aqi}\n")
        else:
            f.write("AQI summary not available.\n")
        f.write("\n\n")

        # Bird summary
        f.write("BIRDS\n")
        if bird_summary:
            total_rows, top_species = bird_summary
            f.write(f"Total bird rows: {total_rows}\n")
            f.write("Top 10 species by sightings:\n")
            for species, sightings in top_species:
                f.write(f"{species}: {sightings}\n")
        else:
            f.write("Bird summary not available.\n")


def main():
    weather_summary = calc_weather_summary()

    aqi_summary = None
    bird_summary = None

    try:
        aqi_summary = calc_aqi_summary()
    except Exception as e:
        print("AQI summary error (we can fix after seeing schema):", e)

    try:
        bird_summary = calc_bird_summary()
    except Exception as e:
        print("Bird summary error (we can fix after seeing schema):", e)

    write_report(weather_summary, aqi_summary, bird_summary)
    print(f"Wrote results to: {OUTFILE}")


if __name__ == "__main__":
    main()
