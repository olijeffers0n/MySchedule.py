from datetime import datetime
from typing import Dict, Any
import json


class Shift:

    def __init__(self, date, start_time, end_time, duration, raw):
        self._date = date
        self._start_time = start_time
        self._end_time = end_time
        self._duration = duration
        self._raw = raw

    @property
    def date(self) -> datetime:
        return self._date

    @property
    def start_time(self) -> str:
        return self._start_time

    @property
    def end_time(self) -> str:
        return self._end_time

    @property
    def duration(self) -> str:
        return self._duration

    @property
    def raw_data(self) -> Dict[str, Any]:
        return self._raw

    def __repr__(self):
        return "Shift("+json.dumps({
            "date": self.date.strftime("%d/%m/%Y"),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration
        }) + ")"
