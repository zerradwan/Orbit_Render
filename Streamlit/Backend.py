# backend.py
from fastapi import FastAPI
from pydantic import BaseModel
from sgp4.api import Satrec, jday
import numpy as np
import datetime

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TLERequest(BaseModel):
    tle_lines: list[str]  # 3 lines: name, line1, line2
    duration_minutes: int = 120
    step_minutes: int = 1

def propagate_orbit(name: str, line1: str, line2: str, duration=120, step=1):
    sat = Satrec.twoline2rv(line1, line2)
    start = datetime.datetime.utcnow()
    times = np.arange(0, duration, step)

    positions = []
    for minute in times:
        t = start + datetime.timedelta(minutes=int(minute))
        jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second + t.microsecond*1e-6)
        e, r, v = sat.sgp4(jd, fr)
        if e == 0:  # success
            positions.append({
                "time": t.isoformat(),
                "x": r[0],
                "y": r[1],
                "z": r[2]
            })
    return positions

@app.post("/orbit")
def get_orbit(req: TLERequest):
    name, line1, line2 = req.tle_lines
    orbit_data = propagate_orbit(name, line1, line2,
                                 duration=req.duration_minutes,
                                 step=req.step_minutes)
    return {
        "name": name,
        "positions": orbit_data
    }
