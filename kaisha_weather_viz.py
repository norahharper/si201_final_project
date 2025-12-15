import sqlite3
import os
import plotly.express as px

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "database.db"))

def plot_weather_avg_temp(limit=15):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT
            l.city_name,
            ROUND(AVG(w.temperature), 2) AS avg_temp_c
        FROM weather_conditions w
        JOIN locations l ON w.location_id = l.id
        GROUP BY l.city_name
        ORDER BY avg_temp_c DESC
        LIMIT ?;
    """, (limit,))

    rows = cur.fetchall()
    conn.close()

    cities = [r[0] for r in rows]
    temps = [r[1] for r in rows]

    fig = px.bar(
        x=cities,
        y=temps,
        title=f"Average Temperature (°C) by City — Top {limit}",
        labels={"x": "City", "y": "Average Temperature (°C)"}
    )
    fig.update_layout(xaxis_tickangle=-45)

    fig.write_html("weather_avg_temp.html")
    print("Saved: weather_avg_temp.html")


if __name__ == "__main__":
    plot_weather_avg_temp()
