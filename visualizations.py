import os
import sqlite3
import pandas as pd
import plotly.express as px

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "database.db"))


# -------------------------
# Kaisha: WEATHER visual (JOIN)
# tables: locations + weather_conditions
# -------------------------
def plot_weather_avg_temp(limit=15):
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query(
        """
        SELECT
            l.city_name AS city,
            ROUND(AVG(w.temperature), 2) AS avg_temp_c,
            COUNT(*) AS observations
        FROM weather_conditions w
        JOIN locations l ON w.location_id = l.id
        GROUP BY l.city_name
        ORDER BY avg_temp_c DESC
        LIMIT ?;
        """,
        conn,
        params=(limit,)
    )
    conn.close()

    fig = px.bar(
        df,
        x="city",
        y="avg_temp_c",
        title=f"Average Temperature (°C) by City — Top {limit}",
        labels={"city": "City", "avg_temp_c": "Average Temp (°C)"},
        hover_data={"observations": True}
    )
    fig.update_layout(xaxis_tickangle=-45)
    fig.write_html("weather_avg_temp.html")
    print("Saved: weather_avg_temp.html")


# -------------------------
# Norah: AQI visual
# table: aqi_data(city, aqi)
# -------------------------
def plot_aqi_top(limit=15):
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query(
        """
        SELECT
            city,
            aqi
        FROM aqi_data
        WHERE aqi IS NOT NULL
        ORDER BY aqi DESC
        LIMIT ?;
        """,
        conn,
        params=(limit,)
    )
    conn.close()

    fig = px.bar(
        df,
        x="city",
        y="aqi",
        title=f"AQI by City — Top {limit} (Higher = Worse)",
        labels={"city": "City", "aqi": "AQI"}
    )
    fig.update_layout(xaxis_tickangle=-45)
    fig.write_html("aqi_top.html")
    print("Saved: aqi_top.html")


# -------------------------
# Brandon: BIRDS visual (JOIN)
# tables: observations + species
# -------------------------
def plot_top_species_by_observations(limit=15):
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query(
        """
        SELECT
            s.comName AS species,
            COUNT(*) AS observation_count
        FROM observations o
        JOIN species s ON o.species_id = s.species_id
        GROUP BY s.comName
        ORDER BY observation_count DESC
        LIMIT ?;
        """,
        conn,
        params=(limit,)
    )
    conn.close()

    fig = px.bar(
        df,
        x="species",
        y="observation_count",
        title=f"Top {limit} Bird Species by Number of Observations",
        labels={"species": "Species (Common Name)", "observation_count": "Observations"}
    )
    fig.update_layout(xaxis_tickangle=-45)
    fig.write_html("birds_top_species.html")
    print("Saved: birds_top_species.html")


if __name__ == "__main__":
    plot_weather_avg_temp()
    plot_aqi_top()
    plot_top_species_by_observations()
