import unittest
from unittest.mock import patch

from xmu_rollcall.verify import (
    find_timetable_number_code,
    rollcall_date_utc,
    send_code,
)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, detail_payload, timetable_payload=None):
        self.headers = {"Accept": "application/json"}
        self.detail_payload = detail_payload
        self.timetable_payload = timetable_payload or {"rollcalls": []}
        self.get_calls = []
        self.put_calls = []

    def get(self, url, **kwargs):
        self.get_calls.append((url, kwargs))
        if url.endswith("/student_rollcalls"):
            return FakeResponse(self.detail_payload)
        if url.endswith("/api/timetable_rollcalls"):
            return FakeResponse(self.timetable_payload)
        raise AssertionError(f"Unexpected GET URL: {url}")

    def put(self, url, **kwargs):
        self.put_calls.append((url, kwargs))
        return FakeResponse({}, status_code=200)


class TimetableNumberCodeTests(unittest.TestCase):
    def test_rollcall_date_is_converted_to_utc(self):
        self.assertEqual(
            rollcall_date_utc("2026-10-10T00:30:00+08:00"),
            "2026-10-09",
        )

    def test_matching_rollcall_is_required(self):
        payload = {
            "rollcalls": [
                {"id": 100, "number_code": "1111"},
                {"id": 200, "number_code": "2222"},
            ]
        }
        self.assertEqual(find_timetable_number_code(payload, 200), "2222")
        self.assertIsNone(find_timetable_number_code(payload, 300))

    @patch("xmu_rollcall.verify.time.sleep", return_value=None)
    def test_timetable_api_is_used_when_detail_code_is_null(self, _sleep):
        session = FakeSession(
            {"number_code": None},
            {
                "rollcalls": [
                    {"id": 424464, "number_code": "4373"},
                    {"id": 999999, "number_code": "0000"},
                ]
            },
        )

        result = send_code(
            session,
            rollcall_id=424464,
            course_id=102245,
            rollcall_time="2026-10-10T06:25:12Z",
        )

        self.assertTrue(result)
        self.assertEqual(len(session.get_calls), 2)
        timetable_url, timetable_kwargs = session.get_calls[1]
        self.assertTrue(timetable_url.endswith("/api/timetable_rollcalls"))
        self.assertEqual(
            timetable_kwargs["params"],
            [
                ("course_ids", "102245"),
                ("rollcall_date", "2026-10-10"),
            ],
        )
        self.assertEqual(
            session.put_calls[0][1]["json"]["numberCode"],
            "4373",
        )

    @patch("xmu_rollcall.verify.time.sleep", return_value=None)
    def test_existing_detail_code_stays_preferred(self, _sleep):
        session = FakeSession({"number_code": "2468"})

        result = send_code(
            session,
            rollcall_id=42,
            course_id=10,
            rollcall_time="2026-10-10T06:25:12Z",
        )

        self.assertTrue(result)
        self.assertEqual(len(session.get_calls), 1)
        self.assertEqual(
            session.put_calls[0][1]["json"]["numberCode"],
            "2468",
        )


if __name__ == "__main__":
    unittest.main()
