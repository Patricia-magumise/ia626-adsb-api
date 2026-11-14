# IA626 – ADSB Flask API

A Flask API over the ADSB data in the `class_datapoints` table on the class MySQL server, with key-based auth and request logging.

## Files


`main.py` The purpose of this file is to show the Flask API (all endpoints, auth, logging) 
`test_client.py`This is the test client it sends valid and invalid requests to every endpoint 
`setup_tables.sql` It Creates `magumip_auth` and `magumip_api_logs`, inserts key `123` 
`config.example.yml`Template for `config.yml` (DB credentials, not committed) |

## Setup

```bash
pip install flask pymysql pyyaml requests
cp config.example.yml config.yml     

python main.py                        
http://127.0.0.1:5000
python test-client.py                  

```

## Endpoints

All requests require `key` (valid key: `123`). Dates use the format `YYYY-MM-DD HH:MM:SS`.

| Method | Example | Notes |

| `GET /getData` | `/getData?key=123&start=2022-11-23 05:28:10&end=2022-11-23 05:28:15` | Datapoints between start and end. Both required. Max 500 rows. |
| `GET /countInPolygon` | `/countInPolygon?key=123&polygon=-74 42,-75 39,-74 41,-74 42` | Count of datapoints inside the polygon (`lon lat` pairs). Ring closes automatically if needed. |
| `GET /getAvgSpeedByFlight` | `/getAvgSpeedByFlight?key=123&start=2022-11-23 05:00:00&end=2022-11-23 08:00:00` | Average ground speed (`gs`) per flight. Start and end optional. Max 500 rows. |

## Auth and logging

**Auth:** the `key` is checked against `magumip_auth.token`. A missing or unknown key returns `code: 0`, `msg: "auth error: ..."`.
**Logging:** every request, successful or not, writes one row to `magumip_api_logs` (endpoint, token, response such as `1 ok` or `0 auth error`, timestamp).

## JSON response schemas

Every response has these top-level keys: Key,Type,Meaning 

| `code` | integer | `1` = success, `0` = failed |
| `msg` | string | `"ok"`, or the reason the request failed |
| `req` | string | Method requested (`getData`, `countInPolygon`, `getAvgSpeedByFlight`) |
| `sqltime` | number | Seconds the SQL query took (`time.time()`); `0` if no query ran |

Failed requests return only these four keys.

### Common base (JSON Schema)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "base_response",
  "type": "object",
  "required": ["code", "msg", "req", "sqltime"],
  "properties": {
    "code":    { "type": "integer", "enum": [0, 1] },
    "msg":     { "type": "string" },
    "req":     { "type": "string" },
    "sqltime": { "type": "number", "minimum": 0 }
  }
}
```

### /getData

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "getData response",
  "allOf": [{ "$ref": "base_response" }],
  "type": "object",
  "properties": {
    "req":         { "const": "getData" },
    "start":       { "type": "string", "format": "date-time" },
    "end":         { "type": "string", "format": "date-time" },
    "num_results": { "type": "integer", "minimum": 0, "maximum": 500 },
    "results": {
      "type": "array",
      "maxItems": 500,
      "items": {
        "type": "object",
        "required": ["flight_num", "date_time", "lat", "lon"],
        "properties": {
          "flight_num": { "type": "string" },
          "date_time":  { "type": "string" },
          "gs":         { "type": ["number", "null"] },
          "lat":        { "type": "number" },
          "lon":        { "type": "number" }
        },
        "additionalProperties": true
      }
    }
  }
}
```

Each result also includes every other column in `class_datapoints`. The binary `geo_point` column is replaced by `lat` and `lon`.

Example:

```json
{
    "code": 1,
    "msg": "ok",
    "req": "getData",
    "sqltime": 0.00058,
    "start": "2022-11-23 05:28:10",
    "end": "2022-11-23 05:28:15",
    "num_results": 1,
    "results": [
        { "flight_num": "AAL123", "date_time": "2022-11-23 05:28:11", "gs": 450.5, "lon": -74.5, "lat": 40.5 }
    ]
}
```

### /countInPolygon

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "countInPolygon response",
  "allOf": [{ "$ref": "base_response" }],
  "type": "object",
  "properties": {
    "req":     { "const": "countInPolygon" },
    "polygon": { "type": "string", "description": "WKT polygon that was queried" },
    "count":   { "type": "integer", "minimum": 0 }
  }
}
```

Example:

```json
{ "code": 1, "msg": "ok", "req": "countInPolygon", "sqltime": 0.0003,
  "polygon": "POLYGON((-74.0 42.0,-75.0 39.0,-74.0 41.0,-74.0 42.0))", "count": 1 }
```

### /getAvgSpeedByFlight

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "getAvgSpeedByFlight response",
  "allOf": [{ "$ref": "base_response" }],
  "type": "object",
  "properties": {
    "req":         { "const": "getAvgSpeedByFlight" },
    "start":       { "type": ["string", "null"] },
    "end":         { "type": ["string", "null"] },
    "num_results": { "type": "integer", "minimum": 0, "maximum": 500 },
    "results": {
      "type": "array",
      "maxItems": 500,
      "items": {
        "type": "object",
        "required": ["flight_num", "avg_speed"],
        "properties": {
          "flight_num": { "type": "string" },
          "avg_speed":  { "type": ["number", "null"] }
        }
      }
    }
  }
}
```

Example:

```json
{ "code": 1, "msg": "ok", "req": "getAvgSpeedByFlight", "sqltime": 0.0004,
  "start": "2022-11-23 05:00:00", "end": "2022-11-23 08:00:00", "num_results": 2,
  "results": [ { "flight_num": "AAL123", "avg_speed": 455.5 },
               { "flight_num": "DAL456", "avg_speed": 300.0 } ] }
```

### Failed request example

```json
{ "code": 0, "msg": "auth error: invalid or missing key", "req": "getData", "sqltime": 0 }
```
