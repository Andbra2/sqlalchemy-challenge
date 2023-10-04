# Import the dependencies.
from flask import Flask, jsonify
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base


# Create a Flask app
app = Flask(__name__)

# Create an engine to connect to the Hawaii weather database
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect the database tables into classes
Base = automap_base()
Base.prepare(engine, reflect=True)
Measurement = Base.classes.measurement
Station = Base.classes.station

# Define a function to get the date one year ago from the most recent date in the database
def date_one_year_ago():
    session = Session(engine)
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    one_year_ago = datetime.strptime(most_recent_date, "%Y-%m-%d") - timedelta(days=365)
    session.close()
    return one_year_ago.strftime("%Y-%m-%d")

# Define the homepage route
@app.route("/")
def welcome():
    return """
    <h1>Welcome to Honolulu, Hawaii Climate API!</h1>
    <p>Explore the weather data with the following available routes:</p>
    <ul>
        <li><a href="/api/v1.0/precipitation">Precipitation</a>: /api/v1.0/precipitation</li>
        <li><a href="/api/v1.0/stations">Stations</a>: /api/v1.0/stations</li>
        <li><a href="/api/v1.0/tobs">Temperature Observations</a>: /api/v1.0/tobs</li>
        <li>For temperature data from a specific start date, use: /api/v1.0/start_date (format: yyyy-mm-dd)</li>
        <li>For temperature data within a date range, use: /api/v1.0/start_date/end_date (format: yyyy-mm-dd)</li>
    </ul>
    """

# Define the precipitation route
@app.route("/api/v1.0/precipitation")
def get_precipitation():
    session = Session(engine)
    prcp_data = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= date_one_year_ago()).all()
    session.close()
    prcp_dict = {date: prcp for date, prcp in prcp_data}
    return jsonify(prcp_dict)

# Define the stations route
@app.route("/api/v1.0/stations")
def get_stations():
    session = Session(engine)
    stations = session.query(Station.station).all()
    session.close()
    station_list = [station[0] for station in stations]
    return jsonify(station_list)

# Define the temperature observations route
@app.route("/api/v1.0/tobs")
def get_tobs():
    session = Session(engine)
    tobs_data = session.query(Measurement.date, Measurement.tobs).filter(Measurement.date >= date_one_year_ago()).all()
    session.close()
    tobs_list = [{"date": date, "tobs": tobs} for date, tobs in tobs_data]
    return jsonify(tobs_list)

# Define the temperature statistics route for a specific start date or date range
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def get_temperature_stats(start, end=None):
    session = Session(engine)
    if end:
        temp_stats = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs))\
            .filter(Measurement.date >= start, Measurement.date <= end).all()
    else:
        temp_stats = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs))\
            .filter(Measurement.date >= start).all()
    session.close()
    
    if temp_stats:
        min_temp, avg_temp, max_temp = temp_stats[0]
        result = {
            "start_date": start,
            "end_date": end,
            "min_temperature": min_temp,
            "average_temperature": avg_temp,
            "max_temperature": max_temp
        }
        return jsonify(result)
    else:
        return jsonify({"error": "Temperature data not found for the given date(s)."}), 404

if __name__ == "__main__":
    app.run(debug=True)
