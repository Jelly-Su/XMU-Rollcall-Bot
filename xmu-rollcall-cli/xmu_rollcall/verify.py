import uuid
import time
import math
import requests
from datetime import datetime, timezone

base_url = "https://lnt.xmu.edu.cn"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://ids.xmu.edu.cn/authserver/login",
}

def find_number_code(data, depth=0, max_depth=10):
    """Extract number_code from nested dict/list API responses.

    Args:
        data: Parsed JSON payload from Tronclass APIs.
        depth: Current recursive depth when traversing nested structures.
        max_depth: Maximum depth allowed for traversal to avoid pathological recursion.

    Returns:
        str or None: The first discovered number_code value, or None if not found.
    """
    if depth > max_depth:
        return None
    if isinstance(data, dict):
        number_code = data.get("number_code")
        if number_code is not None:
            return str(number_code)
        for value in data.values():
            nested_code = find_number_code(value, depth + 1, max_depth)
            if nested_code:
                return nested_code
    elif isinstance(data, list):
        for item in data:
            nested_code = find_number_code(item, depth + 1, max_depth)
            if nested_code:
                return nested_code
    return None

def rollcall_date_utc(rollcall_time):
    """Return the UTC date required by the timetable rollcall API."""
    try:
        parsed = datetime.fromisoformat(str(rollcall_time).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).date().isoformat()
    except (TypeError, ValueError):
        return datetime.now(timezone.utc).date().isoformat()


def find_timetable_number_code(data, rollcall_id):
    """Find a number code for one rollcall in a timetable API response."""
    if isinstance(data, dict):
        items = data.get("rollcalls") or data.get("data") or []
    elif isinstance(data, list):
        items = data
    else:
        return None

    for item in items:
        if not isinstance(item, dict):
            continue
        item_id = item.get("id", item.get("rollcall_id"))
        if str(item_id) != str(rollcall_id):
            continue
        number_code = item.get("number_code")
        if number_code is not None:
            return str(number_code)
    return None


def get_timetable_number_code(
    in_session, rollcall_id, course_id, rollcall_time, request_headers
):
    """Fetch a number code from the timetable endpoint used by newer servers."""
    if course_id is None:
        return None

    timetable_url = f"{base_url}/api/timetable_rollcalls"
    params = [
        ("course_ids", str(course_id)),
        ("rollcall_date", rollcall_date_utc(rollcall_time)),
    ]
    try:
        response = in_session.get(
            timetable_url,
            params=params,
            headers=request_headers,
            timeout=10,
        )
        if response.status_code != 200:
            print(
                "Failed to get number code from timetable API. "
                f"Status: {response.status_code}."
            )
            return None
        return find_timetable_number_code(response.json(), rollcall_id)
    except requests.RequestException as e:
        print(f"Failed to request timetable rollcall API: {e}")
    except ValueError as e:
        print(f"Failed to parse timetable rollcall API response: {e}")
    return None


def send_code(
    in_session, rollcall_id, course_id=None, rollcall_time=None
):
    code_url = f"{base_url}/api/rollcall/{rollcall_id}/student_rollcalls"
    answer_url = f"{base_url}/api/rollcall/{rollcall_id}/answer_number_rollcall"
    print("Trying number code from API...")
    t00 = time.time()
    request_headers = in_session.headers
    number_code = None

    try:
        code_response = in_session.get(
            code_url, headers=request_headers, timeout=10
        )
        if code_response.status_code == 200:
            number_code = find_number_code(code_response.json())
        else:
            print(
                "Number code detail API returned status "
                f"{code_response.status_code}; trying timetable API."
            )
    except requests.RequestException as e:
        print(f"Failed to request number code detail API: {e}")
    except ValueError as e:
        print(f"Failed to parse number code detail API response: {e}")

    if not number_code:
        print("Number code missing in detail API; trying timetable API...")
        number_code = get_timetable_number_code(
            in_session,
            rollcall_id,
            course_id,
            rollcall_time,
            request_headers,
        )

    if not number_code:
        t01 = time.time()
        print(
            "Failed to get number code from available APIs. "
            f"Time: {t01 - t00:.2f} s."
        )
        return False

    payload = {
        "deviceId": str(uuid.uuid4()),
        "numberCode": number_code
    }
    try:
        response = in_session.put(
            answer_url, json=payload, headers=request_headers, timeout=10
        )
        if response.status_code == 200:
            print(
                "Number code rollcall answered successfully.\n"
                "Number code: ",
                number_code,
            )
            time.sleep(5)
            t01 = time.time()
            print(f"Time: {t01 - t00:.2f} s.")
            return True
        t01 = time.time()
        print(
            "Failed to submit number code. "
            f"Status: {response.status_code}\nTime: {t01 - t00:.2f} s."
        )
        return False
    except requests.RequestException as e:
        t01 = time.time()
        print(
            f"Failed to submit number code: {e}\n"
            f"Time: {t01 - t00:.2f} s."
        )
        return False

def send_radar(in_session, rollcall_id):
    url = f"{base_url}/api/rollcall/{rollcall_id}/answer"

    lat_1, lat_2 = 24.3, 24.6
    lon_1, lon_2 = 118.0, 118.2

    def payload(lat, lon):
        return {
            "accuracy": 35,
            "altitude": 0,
            "altitudeAccuracy": None,
            "deviceId": str(uuid.uuid4()),
            "heading": None,
            "latitude": lat,
            "longitude": lon,
            "speed": None
        }

    res_1 = in_session.put(url, json=payload(lat_1, lon_1), headers=headers)
    data_1 = res_1.json()

    if res_1.status_code == 200:
        return True

    res_2 = in_session.put(url, json=payload(lat_2, lon_2), headers=headers)
    data_2 = res_2.json()

    if res_2.status_code == 200:
        return True

    distance_1 = data_1.get("distance")
    distance_2 = data_2.get("distance")

    def latlon_to_xy(lat, lon, lat0, lon0):
        R = 6371000
        x = math.radians(lon - lon0) * R * math.cos(math.radians(lat0))
        y = math.radians(lat - lat0) * R
        return x, y

    def xy_to_latlon(x, y, lat0, lon0):
        R = 6371000
        lat = lat0 + math.degrees(y / R)
        lon = lon0 + math.degrees(x / (R * math.cos(math.radians(lat0))))
        return lat, lon

    def circle_intersections(x1, y1, d1, x2, y2, d2):
        D = math.hypot(x2 - x1, y2 - y1)

        if D > d1 + d2 or D < abs(d1 - d2):
            return None

        a = (d1**2 - d2**2 + D**2) / (2 * D)
        h = math.sqrt(d1**2 - a**2)

        xm = x1 + a * (x2 - x1) / D
        ym = y1 + a * (y2 - y1) / D

        rx = -(y2 - y1) * (h / D)
        ry = (x2 - x1) * (h / D)

        p1 = (xm + rx, ym + ry)
        p2 = (xm - rx, ym - ry)
        return p1, p2

    def solve_two_points(lat1, lon1, lat2, lon2, d1, d2):
        lat0 = (lat1 + lat2) / 2
        lon0 = (lon1 + lon2) / 2
        x1, y1 = latlon_to_xy(lat1, lon1, lat0, lon0)
        x2, y2 = latlon_to_xy(lat2, lon2, lat0, lon0)

        sols = circle_intersections(x1, y1, d1, x2, y2, d2)
        if sols is None:
            return None

        p1 = xy_to_latlon(sols[0][0], sols[0][1], lat0, lon0)
        p2 = xy_to_latlon(sols[1][0], sols[1][1], lat0, lon0)
        return p1, p2

    resolutions = solve_two_points(lat_1, lon_1, lat_2, lon_2, distance_1, distance_2)
    if resolutions:
        ((sol_x_1, sol_y_1), (sol_x_2, sol_y_2)) = resolutions
    else:
        return False

    payload_1 = payload(sol_x_1, sol_y_1)
    payload_2 = payload(sol_x_2, sol_y_2)

    res_3 = in_session.put(url, json=payload_1, headers=headers)
    if res_3.status_code == 200:
        return True
    else:
        print(res_3.json())
        res_4 = in_session.put(url, json=payload_2, headers=headers)
        if res_4.status_code == 200:
            return True

    return False
