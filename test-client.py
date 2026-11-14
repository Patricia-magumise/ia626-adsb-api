import requests, json



BASE = "http://127.0.0.1:5000"

tests = [
    ("getData - valid", "/getData",
     {"key": "123", "start": "2022-11-23 05:28:10", "end": "2022-11-23 05:28:15"}, 1),
    ("getData - bad key", "/getData",
     {"key": "1234", "start": "2022-11-23 05:28:10", "end": "2022-11-23 05:28:15"}, 0),
    ("getData - missing end", "/getData",
     {"key": "123", "start": "2022-11-23 05:28:10"}, 0),
    ("getData - bad date format", "/getData",
     {"key": "123", "start": "11/23/2022", "end": "2022-11-23 05:28:15"}, 0),

    ("countInPolygon - valid", "/countInPolygon",
     {"key": "123", "polygon": "-74 42,-75 39,-74 41,-74 42"}, 1),
    ("countInPolygon - unclosed ring (auto-closed)", "/countInPolygon",
     {"key": "123", "polygon": "-74 42,-75 39,-74 41"}, 1),
    ("countInPolygon - bad polygon", "/countInPolygon",
     {"key": "123", "polygon": "abc"}, 0),
    ("countInPolygon - no key", "/countInPolygon",
     {"polygon": "-74 42,-75 39,-74 41,-74 42"}, 0),

    ("getAvgSpeedByFlight - with dates", "/getAvgSpeedByFlight",
     {"key": "123", "start": "2022-11-23 05:00:00", "end": "2022-11-23 08:00:00"}, 1),
    ("getAvgSpeedByFlight - no dates", "/getAvgSpeedByFlight",
     {"key": "123"}, 1),
    ("getAvgSpeedByFlight - start after end", "/getAvgSpeedByFlight",
     {"key": "123", "start": "2022-11-23 08:00:00", "end": "2022-11-23 05:00:00"}, 0),
]

passed = 0
for desc, endpoint, params, expected in tests:
    r = requests.get(BASE + endpoint, params=params) 
    resp = r.json()
    ok = resp["code"] == expected
    passed += ok
    extra = ""
    if "num_results" in resp:
        extra = f"{resp['num_results']} records"
    elif "count" in resp:
        extra = f"count={resp['count']}"
    print(f"[{'PASS' if ok else 'FAIL'}] {desc}: code={resp['code']} "
          f"msg='{resp['msg']}' sqltime={resp['sqltime']} {extra}")

print(f"\n{passed}/{len(tests)} tests passed")
