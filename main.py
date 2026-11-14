import json,pymysql,time
from flask import Flask
from flask import request,redirect,Response
import datetime
import yaml
from decimal import Decimal


app = Flask(__name__)

db_config = None
with open("config.yml", "r") as file:
    config = yaml.safe_load(file)
    db_config = config['mysql']     

DATE_FMT = '%Y-%m-%d %H:%M:%S'

def auth(token):
    if token is None:
        return False
    conn = pymysql.connect(**db_config) #setup our credentials
    cur = conn.cursor(pymysql.cursors.DictCursor)
    sql = 'SELECT * FROM magumip_auth WHERE `token` = %s;'   
    cur.execute(sql,(token))
    results = cur.fetchall()
    conn.close()  
    if len(results) == 1:
        return True
    else:
        return False

def log(token,endpoint,response):
    conn = pymysql.connect(**db_config) #setup our credentials
    cur = conn.cursor(pymysql.cursors.DictCursor)
    sql = 'INSERT INTO `magumip_api_logs` (`endpoint`,`token`,`response`,`dt`) VALUES (%s,%s,%s,%s)'  
    dt = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur.execute(sql,(endpoint,token,response,dt))  
    conn.close()  

def parse_date(value):
    try:
        return datetime.datetime.strptime(value.strip(), DATE_FMT)
    except (AttributeError, ValueError):
        return None

def fail(res, msg):
    res['code'] = 0
    res['msg'] = msg
    log(request.args.get('key'), res['req'], '0 ' + msg)
    return json.dumps(res, indent=4)

@app.route("/", methods=['GET','POST'])
def root():
    res = {} 
    res['code'] = 2
    res['msg'] = 'No endpoint specified'
    res['req'] = '/'
    return json.dumps(res,indent=4)
    #return '<b>hello</b>'



@app.route("/getData", methods=['GET'])
def getData():
    res = {}
    res['req'] = 'getData'
    res['sqltime'] = 0

    if not auth(request.args.get('key')):
        return fail(res, 'auth error: invalid or missing key')

    start = parse_date(request.args.get('start'))
    end = parse_date(request.args.get('end'))
    if start is None or end is None:
        return fail(res, 'start and end are required, format YYYY-MM-DD HH:MM:SS')
    if start > end:
        return fail(res, 'start must be before end')

    conn = pymysql.connect(**db_config)
    cur = conn.cursor(pymysql.cursors.DictCursor)
    sql = ('SELECT *, ST_X(`geo_point`) AS `lon`, ST_Y(`geo_point`) AS `lat` FROM `class_datapoints` '
           'WHERE `date_time` BETWEEN %s AND %s ORDER BY `date_time` LIMIT 0,500;')
    t0 = time.time()                                   
    cur.execute(sql, (start, end))
    rows = cur.fetchall()
    res['sqltime'] = round(time.time() - t0, 6)       
    conn.close()

    items = []
    for row in rows:
        item = {}
        for column, value in row.items():
            if column == 'geo_point':                  
                continue
            if isinstance(value, datetime.datetime):
                value = value.strftime(DATE_FMT)
            if isinstance(value, Decimal):
                value = float(value)
            item[column] = value
        items.append(item)

    res['code'] = 1
    res['msg'] = 'ok'
    res['num_results'] = len(items)
    res['results'] = items
    log(request.args.get('key'), res['req'], '1 ok')
    return json.dumps(res, indent=4)

#datapoints are inside a polygon
@app.route("/countInPolygon", methods=['GET'])
def countInPolygon():
    res = {}
    res['req'] = 'countInPolygon'
    res['sqltime'] = 0

    if not auth(request.args.get('key')):
        return fail(res, 'auth error: invalid or missing key')

    polygon = request.args.get('polygon')               
    if polygon is None:
        return fail(res, 'polygon is required, e.g. polygon=-74 42,-75 39,-74 41,-74 42')

    
    points = []
    try:
        for pair in polygon.split(','):                 
            x, y = pair.split()                         
            points.append((float(x), float(y)))
    except ValueError:
        return fail(res, "polygon must be 'lon lat' pairs separated by commas")
    if points[0] != points[-1]:
        points.append(points[0])                        
    if len(points) < 4:
        return fail(res, 'polygon needs at least 3 different points')

    wkt = 'POLYGON((' + ','.join(f'{x} {y}' for x, y in points) + '))'
    conn = pymysql.connect(**db_config)
    cur = conn.cursor(pymysql.cursors.DictCursor)
    sql = ('SELECT COUNT(*) AS `count` FROM `class_datapoints` '
           'WHERE ST_Within(`geo_point`, ST_GeomFromText(%s, 0));')
    t0 = time.time()
    cur.execute(sql, (wkt,))
    row = cur.fetchone()
    res['sqltime'] = round(time.time() - t0, 6)
    conn.close()

    res['code'] = 1
    res['msg'] = 'ok'
    res['polygon'] = wkt
    res['count'] = row['count']
    log(request.args.get('key'), res['req'], '1 ok')
    return json.dumps(res, indent=4)



@app.route("/getAvgSpeedByFlight", methods=['GET'])
def getAvgSpeedByFlight():
    res = {}
    res['req'] = 'getAvgSpeedByFlight'
    res['sqltime'] = 0

    if not auth(request.args.get('key')):
        return fail(res, 'auth error: invalid or missing key')

    where = []   
    params = []
    start = end = None
    if request.args.get('start'):
        start = parse_date(request.args.get('start'))
        if start is None:
            return fail(res, 'start must be in format YYYY-MM-DD HH:MM:SS')
        where.append('`date_time` >= %s')
        params.append(start)
    if request.args.get('end'):
        end = parse_date(request.args.get('end'))
        if end is None:
            return fail(res, 'end must be in format YYYY-MM-DD HH:MM:SS')
        where.append('`date_time` <= %s')
        params.append(end)
    if start and end and start > end:
        return fail(res, 'start must be before end')

    sql = 'SELECT `flight_num`, AVG(`gs`) AS `avg_speed` FROM `class_datapoints` '
    if where:
        sql += 'WHERE ' + ' AND '.join(where) + ' '
    sql += 'GROUP BY `flight_num` ORDER BY `flight_num` LIMIT 0,500;'

    conn = pymysql.connect(**db_config)
    cur = conn.cursor(pymysql.cursors.DictCursor)
    t0 = time.time()
    cur.execute(sql, params)
    rows = cur.fetchall()
    res['sqltime'] = round(time.time() - t0, 6)
    conn.close()

    items = []
    for row in rows:
        item = {}
        item['flight_num'] = row['flight_num']
        item['avg_speed'] = round(float(row['avg_speed']), 2) if row['avg_speed'] is not None else None
        items.append(item)

    res['code'] = 1
    res['msg'] = 'ok'
    res['num_results'] = len(items)
    res['results'] = items
    log(request.args.get('key'), res['req'], '1 ok')
    return json.dumps(res, indent=4)


if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True)
