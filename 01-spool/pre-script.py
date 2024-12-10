import os
from datetime import datetime

filename = os.path.join(os.path.dirname(__file__), "pyboard/uploadtime.py" )
now = datetime.utcnow()
with open(filename, "w") as file:
    file.write(f"seconds = {now.second}\n")
    file.write(f"minutes = {now.minute}\n")
    file.write(f"hours = {now.hour}\n")
    file.write(f"day_of_week = {now.weekday()}\n")
    file.write(f"date = {now.day}\n")
    file.write(f"month = {now.month}\n")
    file.write(f"year = {now.year-2000}\n")