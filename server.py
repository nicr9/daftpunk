from flask import Flask
from flask import json
from flask import Response
import redis

app = Flask(__name__)
r = redis.StrictRedis(host='localhost', port=6379, db=0)

@app.route("/")
def hello():
    return "Hello ld!"

@app.route('/properties/')
def show_properties():
    props = r.smembers('daftpunk:properties')

    data = []
    for n in props:
    	data.append({"id":n, "address": r.get('daftpunk:%s:address' % n)})

    resp = Response(json.dumps(data), status=200, mimetype='application/json')
    return resp

@app.route('/property/<id>')
def show_property(id):

    data = {"id":id, "address": r.get('daftpunk:%s:address' % id)}

    resp = Response(json.dumps(data), status=200, mimetype='application/json')
    return resp

if __name__ == "__main__":
    app.run(debug=True)