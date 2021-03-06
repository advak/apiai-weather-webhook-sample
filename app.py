#!/usr/bin/env python
# comment
#another comment 1

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):
    if req.get("result").get("action") != "yahooWeatherForecast":
        return {}
    baseurl = "https://query.yahooapis.com/v1/public/yql?"
    yql = makeYqlQuery(req)
    yql_query, date_period = yql[0], yql[1]
    if yql_query is None:
        return {}
    yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json"
    result = urlopen(yql_url).read()
    data = json.loads(result)
    res = makeWebhookResult(data, date_period)
    return res


def makeYqlQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    date_period = parameters.get("date-period")
    # time = parameters.get("date")
    if city is None:
        return None

    return ("select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "') and u='c' limit 3", date_period)


def makeWebhookResult(data, date_period):
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    if date_period == 'now':
        date_offset = 0
    elif date_period == 'tomorrow':
        date_offset = 1
    elif date_period == 'in two days':
        date_offset = 2
    else:
        date_offset = 0

    tomorrow_forcast = item.get('forecast')[date_offset]
    tomorrow_text = tomorrow_forcast.get('text')
    tomorrow_high = tomorrow_forcast.get('high')
    tomorrow_low = tomorrow_forcast.get('low')

    condition = item.get('condition')
    if condition is None:
        return {}

    # print(json.dumps(item, indent=4))

    # speech = "Today in " + location.get('city') + ', ' + location.get('country') + ": " + condition.get('text') + \
    #          ", the temperature is " + condition.get('temp') + " " + units.get('temperature')
    speech = date_period + " in " + location.get('city') + ', ' + location.get('country') + ": " + tomorrow_text + \
             ", the high temperature will be " + tomorrow_high + units.get('temperature') + " the low temperature will be " + tomorrow_low + units.get('temperature')

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
