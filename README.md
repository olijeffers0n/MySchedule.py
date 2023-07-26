# MySchedule.py

## Description
This is an API wrapper for the McDonald's *MySchedule* website.

## Usage:

Install with:
```
pip install MySchedule.py
```

### Getting Shifts

```python
from schedule import ScheduleAPI
from datetime import datetime

api = ScheduleAPI("USERID", "PASSWORD")
api.login()
print(api.get_shifts_for_date(datetime.now()))
```
This will print out the shifts for the current week.


### Getting Timecard
```py
from schedule.api import ScheduleAPI, PunchType

api = ScheduleAPI("USERID", "PASSWORD")
api.login()

timecard = api.get_timecard()

for shift in timecard:
    print(f"{shift.date} Breakdown:")
    print(f"Duration Clocked In: {shift.time_clocked_in}")
    print(f"Duration Clocked Out: {shift.time_clocked_out}")
```
This will print a breakdown of each shift's timecard and how long you were clocked in and out for.