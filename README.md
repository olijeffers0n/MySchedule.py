# MySchedule.py

## Description
This is an API wrapper for the McDonald's *MySchedule* website.

## Usage:

Install with:
```
pip install MySchedule.py
```

Then you can use it like this:

```python
from schedule import ScheduleAPI
from datetime import datetime

api = ScheduleAPI("USERID", "PASSWORD")
api.login()
print(api.get_shifts_for_date(datetime.now()))
```

Which will print out the shifts for the current Week. 