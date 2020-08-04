from flask import Flask, request, Response
from datetime import datetime
import json

class LocationsWorker:
        def __init__(self):
                self.locations = []
                self.last_given = -1

        def save_location(self, location_data):
                self.locations.append(location_data)

        def get_locations(self):
                locations = self.locations[self.last_given+1:]
                self.last_given = len(self.locations)-1
                return locations


app = Flask(__name__)


locations_worker = LocationsWorker()


@app.route('/location.send', methods=['POST'])
def location_send():
    data = request.get_json()
    if not (data.get('long', False) and data.get('lat', False)):
        return Response(status=400)
    with open('input.txt', 'a') as f:

        f.write(str(data))
    long, lat = data['long'], data['lat']
    locations_worker.save_location((datetime.now().isoformat(), long, lat))
    return Response(status=200)


@app.route('/location.get', methods=['GET'])
def location_get():
    locations = locations_worker.get_locations()
    return Response(json.dumps(locations))




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='5050')
