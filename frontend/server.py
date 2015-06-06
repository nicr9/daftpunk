from flask import Flask,json, Response, send_from_directory
import redis

app = Flask(__name__, static_url_path='')
r = redis.StrictRedis(host='localhost', port=6379, db=0)

@app.route('/')
def root():
    return send_from_directory('', 'index.html')

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)

@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('css', path)

@app.route('/bower_components/<path:path>')
def send_bower(path):
    return send_from_directory('bower_components', path)

@app.route('/properties/')
def show_properties():
    props = r.smembers('daftpunk:properties')

    data = []
    for n in props:
      print r.mget('daftpunk:%s:current_price' % n)
      if r.get('daftpunk:%s:current_price' % n):
        current_price = float(r.get('daftpunk:%s:current_price' % n).split(' ')[0])
      data.append({
            "id":n, 
            "address": r.get('daftpunk:%s:address' % n),
            "lat": r.get('daftpunk:%s:lat' % n),
            "long": r.get('daftpunk:%s:long' % n),
            "current_price": current_price,
            "price": r.mget('daftpunk:%s:price' % n)
        })

    resp = Response(json.dumps(data), status=200, mimetype='application/json')
    return resp

@app.route('/property/<id>')
def show_property(id):

  timestamps, prices = zip(*r.zrange('daftpunk:%s:price' % id, 0, -1, withscores=True))
  data = {
      "id":id, 
      "address": r.get('daftpunk:%s:address' % id),
      "lat": r.get('daftpunk:%s:lat' % id),
      "long": r.get('daftpunk:%s:long' % id),
      "description": r.get('daftpunk:%s:description' % id),
      "current_price": r.get('daftpunk:%s:current_price' % id),
      "timestamps": timestamps,
      "prices": prices
    }

  resp = Response(json.dumps(data), status=200, mimetype='application/json')
  return resp

if __name__ == "__main__":
  app.run(debug=True)