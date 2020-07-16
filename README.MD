# PiWeather
Phase 3 Will remove the Abiant weather connection for personal local data and change to using a full NWS based weather display


Written for:
Python 3.6.5

Requires the requests lib

Publishers:
NWS.gov
AmbientWeather.net

About:
This script pulls data from the ambient weather api and NWS to display current conditions.

Usage:
Set the config usage:
ambAppkey = from ambient weather, need to send a request to support
ambApiKey = from the ambientweather.net user interface

intervalMinutes = 20

[NWS]
forecastLocation = #lat,long# You will need your latitued and longitude to get NWS forcast info.

Adjusting the code if needed:
loglevel = change to ERROR to get less data, INFO, for a quick "it worked log", or DEBUG for tons of data

After you set the variables, execute the script, it will continue to run until killed

Author:
Steven Kuzmich


