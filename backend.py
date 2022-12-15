import urllib.parse, urllib.request, urllib.error, json
import api_keys
import datetime


# Utility function
def safe_get(url):
    try:
        return urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        print("The server couldn't fulfill the request." )
        print("Error code: ", e.code)
    except urllib.error.URLError as e:
        print("We failed to reach a server")
        print("Reason: ", e.reason)
    return None

# Utility function for prettying the json obj
# Expects the json obj as input; returns a pretty version
def pretty(obj):
    return json.dumps(obj, sort_keys=False, indent=2)


baseurl = "https://developer.nps.gov/api/v1/parks"

# Gets all the park codes for the national parks in NPS
# Param n - number of parks to get the codes for
# Returns a dictionary that looks like 
# { "park_code" : { "name":"park_full_name", "url":[url to an image about this park] } }
def get_parks(n, query='', state=''):
    params = { 'limit':n, 'api_key':api_keys.NPS_API_KEY }

    if query:
        params['q'] = query.replace(" ", "%20")

    if state:
        params['stateCode'] = state

    request_url = baseurl + '?' + urllib.parse.urlencode(params)
    response = safe_get(request_url)
    
    if response:
        response_data = json.loads(response.read())
        data = response_data['data']
        park_codes = {}

        for park in data:
            park_codes[park['parkCode']] = { "name":park['fullName'], "url":park['images'][0]['url']}

        return park_codes
    

# Gets the park info of particular park
# param parkCode - string parkCode that you can get from get_parks()
# Returns a dictionary with information about that park
# { 'url':string, 'fullName':string, 'description':string, 'lat':float, 'lng':float,
#   'activitiesFull':list of strings, 'images':[{ 'url':string, 'altText':string }], 'address':string,
#   'activitiesShort':list of 20, 'temperature':int(farenheit), 'humidity':int(%), 
#   'windSpeed':int(mph), 'AQI':int }
def get_park_info(parkCode):
    params = { 'parkCode':parkCode, 'limit':1, 'api_key':api_keys.NPS_API_KEY }
    request_url = baseurl + '?' + urllib.parse.urlencode(params)
    response = safe_get(request_url)

    if response:
        response_data = json.loads(response.read())
        data = response_data['data'][0]
        info = {}

        info['url'] = data['url']
        info['fullName'] = data['fullName']
        info['description'] = data['description']
        info['lat'] = float(data['latitude'])
        info['lng'] = float(data['longitude'])
        
        activities = []
        for activity in data['activities']:
            activities.append(activity['name'])
        info['activitiesFull'] = activities
        
        if len(activities) > 20:
            info['activitiesShort'] = activities[:19]
            info['activitiesShort'].append("And more!")
        else:
            info['activitiesShort'] = activities

        images = []
        for image in data['images']:
            images.append({ 'url':image['url'], 'altText':image['altText'] })
        info['images'] = images

        addrData = data['addresses'][0]
        address = "{}, {}, {} {}".format(
            addrData['line1'], addrData['city'], addrData['stateCode'], addrData['postalCode'])
        info['address'] = address

        info.update(get_weather(info['lat'], info['lng']))

        return info


# Gets the current weather and AQI data for a given latitude and longitude
# Uses AirVisual AQI API (returns data for nearest supported city)
# param lat - latitude (float)
# param lng - longitude (float)
# returns dictionary
# { 'temperature':int(farenheit), 'humidity':int(%), 'windSpeed':int(mph), 'AQI':int }
def get_weather(lat, lng):
    aqiBaseurl = "https://api.airvisual.com/v2/nearest_city"
    params = { 'lat':lat, 'lon':lng, 'key':api_keys.AQI_API_KEY }
    request_url = aqiBaseurl + '?' + urllib.parse.urlencode(params)
    response = safe_get(request_url)

    if response:
        response_data = json.loads(response.read())
        data = response_data['data']['current']
        weather = {}

        # Temperature given in C, so need to convert to F
        weather['temperature'] = int((data['weather']['tp'] * (9 / 5)) + 32)
        weather['humidity'] = data['weather']['hu']
        # Wind speed given in m/s, so need to convert to mph
        weather['windSpeed'] = int(data['weather']['ws'] * 2.23694)
        weather['AQI'] = data['pollution']['aqius']

        return weather



# Gets the weather forecasts and AQI data for a given latitude and longitude
# for the next five days using OpenWeather API
# param lat - latitude (float)
# param lng - longitude (float)
# returns dictionary { "{{day}}" : WeatherObject }
def get_forecasts(lat, lng):
    baseurl = "https://api.openweathermap.org/data/2.5/forecast"
    params = { 'lat':lat, 'lon':lng, 'appid':api_keys.OPW_API_KEY, 'units':'imperial' }
    request_url = baseurl + '?' + urllib.parse.urlencode(params)
    response = safe_get(request_url)

    if response:
        response_data = json.loads(response.read())
        # print(pretty(response_data))
        data = response_data['list']
        forecasts = {}

        for forecast in data:
            day = forecast['dt_txt'][:10]
            if day not in forecasts:
                forecasts[day] = WeatherObject(forecast)
        
        # print("\n\nForecasts:", forecasts)
        return forecasts


class WeatherObject:
    # Takes in a forecast object as defined in the OpenWeather API
    def __init__(self, forecastObj):
        date = forecastObj['dt_txt'][:10]
        self.date = datetime.datetime.strptime(date, "%Y-%m-%d")
        self.datef = self.date.strftime("%B %d, %Y")
        self.temp = int(forecastObj['main']['temp'])
        self.humidity = forecastObj['main']['humidity']
        self.windSpeed = int(forecastObj['wind']['speed'])
        self.description = forecastObj['weather'][0]['description']

    def __str__(self) -> str:
        date = "Date: " + self.datef
        desc = "\t" + self.description
        temp = "\tTemperature: {} F".format(self.temp)
        humidity = "\tHumidity: {}%".format(self.humidity)
        ws = "\tWind speed: {} MPH".format(self.windSpeed)
        
        return "\n".join([date, desc, temp, humidity, ws])


        

        



# Outputs the parkcodes to a .csv or .txt file
# param filename - name of output file; filetype must be .csv or .txt
# param n - number of parkcodes to output (defaults to 468 (max))
def output_parkcodes(filename, n=468):
    if filename[-3:] not in ['csv', 'txt']:
        print("ERROR: filetype must be 'csv' or 'txt'")
        return

    parkCodes = get_parks(n)
    with open(filename, 'w', encoding='utf-8') as f:
        for parkCode in parkCodes:
            if filename[-3:] == 'csv':
                f.write("{},{}\n".format(parkCode, parkCodes[parkCode]))
            else:
                f.write("{} : {}\n".format(parkCodes[parkCode], parkCode))


# Gets the park info for every park in parks and outputs to a html file
# param filename - name of file to output to
# param parks - list of parkCodes to access and display in output file
def output_parks(filename, parks):
    with open(filename, 'w') as f:
        for park in parks:
            parkInfo = get_park_info(park)
            weather = get_forecasts(parkInfo['lat'], parkInfo['lng'])

            f.write("<h1>{}</h1>\n".format(parkInfo['fullName']))
            f.write("<h3>{}</h3>\n".format(parkInfo['address']))
            f.write("<h3>Current temperature: {} degrees Farenheit</h3>\n".format(weather['temperature']))
            f.write("<h3>Current Air Quality: {}</h3>\n".format(weather['AQI']))
            f.write("<h3>Find out more information <a href='{}'>here</a></h3>\n".format(parkInfo['url']))
            f.write("<p>{}</p>\n".format(parkInfo['description']))

            activitiesStr = ""
            for activity in parkInfo['activities']:
                activitiesStr += activity + ", "
            f.write("<h4>Activities: {}</h4>\n".format(activitiesStr[:-2]))

            for image in parkInfo['images']:
                f.write("<img src='{}' alt='{}' height='150'/>\n".format(image['url'], image['altText']))
            
            f.write("<br/>\n")



if __name__ == '__main__':
    # Drumheller lat, long: 47.65388349936608, -122.30778621204907
    forecasts = get_forecasts(47.65388349936608, -122.30778621204907)

    print("\n===== FORECASTS =====")
    for forecast in forecasts:
        print(forecasts[forecast])

    # print(get_parks(10, "Yellowstone National Park"))

    # print("\nOutputting all park codes....")
    # # Output all 468 park codes to NPS_ParkCodes.txt
    # output_parkcodes("NPS_ParkCodes.txt")
    # print("DONE!\n")

    # # Mt Rainer, Yellowstone, Washington Monument, Glacier National Park
    # parks = ['mora', 'yell', 'wamo', 'glac']
    # print("Outputting parks to html file...")
    # output_parks("ParksOutput.html", parks)
    # print("DONE!\n")


