from flask import Flask, render_template, request, redirect
from backend import get_parks, get_park_info, get_forecasts, get_weather

app = Flask(__name__)
app.secret_key = "kaR20rhQL22"
MAX_PARKS = 468


@app.route("/")
def home_page():
    return render_template('home.html')

@app.route("/search", methods=["POST", "GET"])
def search_page():
    query = request.form['query'].strip()
    state = request.form['state'].strip()
    parks = get_parks(50, query, state.upper())

    if parks:
        return render_template('search.html', parks=parks, error=False)
    else:
        return render_template('search.html', error=True, query=query)



@app.route("/parkcodes")
def parkcodes_page():
    return render_template('parkcodes.html', parkCodes=get_parks(MAX_PARKS))

@app.route("/park", methods=["POST", "GET"])
def park_page():
    parks = get_parks(MAX_PARKS)
    parkCode = request.form['parkCode'].lower()
    # parkCode = str(request.args.get('parkCode'))

    if parkCode in parks:
        parkInfo = get_park_info(parkCode)
        forecasts, weather = 0, 0
        
        if parkInfo['lat'] and parkInfo['lng']:
            forecasts = get_forecasts(parkInfo['lat'], parkInfo['lng'])
            weather = get_weather(parkInfo['lat'], parkInfo['lng'])

        return render_template('park.html', parkInfo=parkInfo, parkCode=parkCode, forecasts=forecasts, weather=weather, error=False)
    else:
        return render_template('park.html', parkCode=parkCode, error=True)

@app.route("/parkbycode")
def parkbycode_page():
    parkCode = str(request.args.get('parkCode'))
    parkInfo = get_park_info(parkCode)
    forecasts, weather = 0, 0
        
    if parkInfo['lat'] and parkInfo['lng']:
        forecasts = get_forecasts(parkInfo['lat'], parkInfo['lng'])
        weather = get_weather(parkInfo['lat'], parkInfo['lng'])

    return render_template('park.html', parkInfo=parkInfo, parkCode=parkCode, forecasts=forecasts, weather=weather, error=False)


if __name__ == "__main__":
    app.run(debug=True)