from typing import Dict, Any, List
from fitparse import FitFile

# Extract a compact summary from a FIT file: distance(km), duration(s), avg_hr, max_hr
# Best-effort with missing fields.
def parse_fit_file(path: str) -> Dict[str, Any]:
    try:
        fitfile = FitFile(path)
        total_timer = 0.0
        total_distance = 0.0
        hr_values: List[int] = []
        for record in fitfile.get_messages("record"):
            data = {d.name: d.value for d in record}
            if "timestamp" in data and "last_timestamp" in data:
                pass
            if (d := data.get("distance")) is not None:
                total_distance = max(total_distance, float(d))
            if (s := data.get("speed")) is not None:
                # speed m/s; skip
                pass
            if (hr := data.get("heart_rate")) is not None:
                try:
                    hr_values.append(int(hr))
                except Exception:
                    pass
        # Sessions for totals
        for sess in fitfile.get_messages("session"):
            data = {d.name: d.value for d in sess}
            if (t := data.get("total_timer_time")) is not None:
                total_timer = float(t)
            if (dist := data.get("total_distance")) is not None:
                total_distance = float(dist)
        km = total_distance / 1000.0 if total_distance else 0.0
        avg_hr = int(sum(hr_values) / len(hr_values)) if hr_values else None
        max_hr = max(hr_values) if hr_values else None
        return {
            "distance_km": round(km, 2),
            "duration_s": int(total_timer) if total_timer else None,
            "avg_hr": avg_hr,
            "max_hr": max_hr,
        }
    except Exception as e:
        return {"error": str(e)}
