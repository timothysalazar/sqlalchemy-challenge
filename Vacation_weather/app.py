# Import the dependencies.
import datetime as dt
import numpy as np
import pandas as pd

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect, text, select

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
#session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")
def all():
    return """
    Available routes : <br/>
    <br/>
    - /api/v1.0/precipitation<br/>
    - /api/v1.0/stations<br/>
    - /api/v1.0/tobs<br/>
    - /api/v1.0/{start}*<br/>
    - /api/v1.0/{start}/{end}*<br/>
    <br/>
    and that's all!<br/>
    <br/>
    <br/>
    <br/>
    *user input
    """

## Precipitation page returns last 12 months of data
@app.route("/api/v1.0/precipitation")
def precip():
    with Session(bind=engine) as session:
        most_recent = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
        one_year_back = dt.datetime.strptime(most_recent, "%Y-%m-%d") - dt.timedelta(days=365)

        data = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= one_year_back).all()
    
    dictionary = []
    for date, prcp in data:
        datum = {} #empty dictionary
        datum["date"] = date
        datum["prcp"] = prcp
        dictionary.append(datum)

    return jsonify(dictionary)

## Stations page returns a list of the stations by name
@app.route("/api/v1.0/stations")
def stations():
    with Session(bind=engine) as session:
        data = session.query(Station.name).all()
    
    list_names = list(np.ravel(data))    
    return jsonify(list_names)

## tobs page returns the dates and temperatures for the last year of available data from most active station
@app.route("/api/v1.0/tobs")
def tobs():
    with Session(bind=engine) as session:
        activity = pd.read_sql("SELECT station, COUNT(date) FROM measurement GROUP BY station ORDER BY COUNT(date) DESC", engine.connect())
        most_recent = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
        one_year_back = dt.datetime.strptime(most_recent, "%Y-%m-%d") - dt.timedelta(days=365)
        date_string = one_year_back.strftime("%Y-%m-%d")
        data = pd.read_sql(f"SELECT date, tobs FROM measurement WHERE date >= '{date_string}' AND station = '{activity.station[0]}'", engine.connect())

    list_tobs = list(np.ravel(data))    
    return jsonify(list_tobs)

## <start> page returns the min, avg, and max temperature for all data from the user provided date to the last date in the dataset
@app.route("/api/v1.0/<start>")
def start_date_set(start):
    with Session(bind=engine) as session:
        date_string = pd.to_datetime(start).strftime("%Y-%m-%d")
        data = pd.read_sql(f"SELECT tobs, date FROM measurement WHERE date >= '{date_string}' ", engine.connect())

    min_temp = data['tobs'].min()
    max_temp = data['tobs'].max()
    avg_temp = data['tobs'].mean()

    output = {
        "start_date": date_string,
        "end_date": data['date'].max(),
        "min_temperature": min_temp,
        "max_temperature": max_temp,
        "avg_temperature": avg_temp
    }
    return jsonify(output)



## RUN DEVELOPMENT SERVER
if __name__  == "__main__":
    app.run(debug=True)

