import datetime 
from math import acos, tan, sin, pi, cos

def minutes_to_time(minutes):
    hours = minutes//60
    minutes = minutes-hours*60
    return datetime.time(hour = hours, minute = minutes)

# -1 is a placeholder for indexing purposes.
_DAYS_IN_MONTH = [-1, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_DAYS_BEFORE_MONTH = [-1, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]

def get_sunrise_sunset(date, latitude, longitude, timezone, sunset):
    ## TODO could be more accurate using lepyear and timezone.
    day_of_year = _DAYS_BEFORE_MONTH[date.month] + date.day
    latitude = latitude*pi/180
    y = 2*pi/365*(day_of_year-1)
    eqtime = 229.18*(0.000075+0.001868*cos(y)-0.032077*sin(y)-0.014615*cos(2*y)-0.040849*sin(2*y))
    decl = 0.006918 - 0.399912*cos(y) + 0.070257*sin(y) - 0.006758*cos(2*y) + 0.000907*sin(2*y) - 0.002697*cos(3*y) + 0.00148*sin(3*y)
    ha = acos(cos(90.833*2*pi/360)/(cos(latitude)*cos(decl)) - tan(latitude)*tan(decl))
    if sunset:
        ha = -1*ha
    return minutes_to_time(int(720 - 4*(longitude + ha*180/pi) - eqtime + timezone))

def get_sunrise(date, latitude, longitude, timezone):
    return get_sunrise_sunset(date, latitude, longitude, timezone, False)

def get_sunset(date, latitude, longitude, timezone):
    return get_sunrise_sunset(date, latitude, longitude, timezone, True)

class time_change_rule:
    week = 0
    weekday = 0
    month = 0
    hour = 0
    timezone = 0
    
    def __init__(this, week, weekday, month, hour, timezone):
        this.week = week
        this.weekday = weekday
        this.month = month
        this.hour = hour
        this.timezone = timezone

    def next_change(this, now):
        next = this.get_timezone_datetime(now.year)
        if next <= now:
            next = this.get_timezone_datetime(now.year+1)
        return next

    def get_timezone_datetime(this, year):
        weekday_on_first = datetime.date(year, this.month, 1).weekday()
        weekday_first_week = (this.weekday-weekday_on_first+7)%7+1
        weekdays_in_month = [weekday_first_week]
        while True:
            try:
                next = weekdays_in_month[-1] + 7
                datetime.date(year, this.month, next)
                weekdays_in_month.append(next)
            except:
                break
        return datetime.datetime(year, this.month, weekdays_in_month[this.week], this.hour)

class timezone:
    dst = None
    st = None

    def __init__(this, dst, st):
        this.dst = dst
        this.st = st

    def get_current_tz(this, utc_time):
        #print("UTC:", utc_time)
        now = utc_time + datetime.timedelta(minutes=min(this.dst.timezone, this.st.timezone))
        #print("TZ:", now)

        if this.dst.next_change(now) < this.st.next_change(now):
            tz = this.st
        else:
            tz = this.dst

        return tz
        
    def get_local_time(this, utc_time):
        tz = this.get_current_tz(utc_time)
        return utc_time + datetime.timedelta(minutes=tz.timezone)





"""
print("======EXAMPLES======")
latitude = -43.532055
longitude = 172.636230
dst = time_change_rule(-1, 6, 9, 2, 780)
st = time_change_rule(0, 6, 4, 2, 720)
nz_tz = timezone(dst, st)
now = datetime.datetime(2022, 4, 3, 13, 1) # Now in UTC

print(_DAYS_BEFORE_MONTH)

print("UTC:    ", now)
tz = nz_tz.get_current_tz(now).timezone
print("TZ:     ", tz/60)
print("local:  ", nz_tz.get_local_time(now))
print("Sunrise:", get_sunrise(now, latitude, longitude, tz))
print("Sunset: ", get_sunset(now, latitude, longitude, tz))
"""