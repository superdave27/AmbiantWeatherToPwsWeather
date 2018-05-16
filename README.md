# AmbiantWeatherToPwsWeather
python script to ETL data from ambiantweather.net to pwsweather.com to use a AW weather station with Rachio

Written for:
Python 3.6.5
Requires the requests lib

Publishers:
PWSweather.com 
AmbientWeather.net

About:
This script pulls data from the ambient weather api and sends it to PWS.
This script is intended to help support Rachio Sprinklers with a local ambient Weather Station

Usage:
Set the following variables for your usage:
ambAppkey = from ambient weather, need to send a request to support
ambApiKey = from the ambientweather.net user interface
pwsStation = not the name but the ID when you set up your station
pwsPassword = your PWS weather account password
intervalMinutes = minutes delay between pushes
loglevel = change to ERROR to get less data, INFO, for a quick "it worked log", or DEBUG for tons of data

After you set the variables, execute the script, it will continue to run until killed

Author:
Steven Kuzmich
