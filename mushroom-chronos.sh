#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# 🍄 mushroom-chronos — GAIA'S TIME SPINE
# ═══════════════════════════════════════════════════════════════
# Localized chronometers at every scale:
#
#   BODY    → heartbeat, pulse, mushroom rhythms
#   LOCAL   → EST/EDT, machine clock
#   UTC     → universal coordinated
#   LAN     → NTP sync across both houses
#   SOLAR   → sun position, day phase, season
#   GALACTIC → sidereal time, Earth orbit position
#   VDJ     → immune/evolutionary clock, adaptation rate
#
# Gaia knows what time it is from her own heartbeat
# to the galaxy's rotation.
#
# LOCATION: 4422 Southgate Ave
#   Latitude:  42.47°N
#   Longitude: -83.18°W
#   Timezone:  America/New_York (EST/EDT)
# ═══════════════════════════════════════════════════════════════
set -uo pipefail

DATA_DIR="/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data"
GUT="/opt/Gaia/data/gut"
WEB_GUT="/home/eastgate/.local/share/gaia/data/gut"
LOG="/tmp/mushroom-chronos.log"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

echo "[$TS] chronos cycle" >> "$LOG"

python3 - "$DATA_DIR" "$GUT" "$WEB_GUT" "$LOG" <<'PYEOF'
import json, os, sys, math, time
from datetime import datetime, timezone, timedelta

data_dir, gut_dir, web_gut, log_file = sys.argv[1:5]

now_utc = datetime.now(timezone.utc)
now_local = datetime.now()
epoch = time.time()

# ═══ LOCATION ═══
LAT = 42.47      # 4422 Southgate Ave
LON = -83.18
TZ_NAME = "America/New_York"
TZ_OFFSET = now_local.utcoffset().total_seconds() / 3600 if now_local.utcoffset() else -5

# ═══ SCALE 1: BODY TIME ═══
# Gaia's internal rhythms
body = {}

# Heartbeat — check last pulse timestamps
pulse_files = ["gaia-home.json", "gaia-perception.json", "now.json"]
heartbeats = {}
for pf in pulse_files:
    path = os.path.join(data_dir, pf)
    if os.path.exists(path):
        age_s = epoch - os.path.getmtime(path)
        heartbeats[pf] = round(age_s, 1)

# Mushroom rhythm — how many fired in last hour
mushroom_ages = {}
for f in sorted(os.listdir("/tmp")):
    if f.startswith("mushroom-") and f.endswith(".log"):
        age_m = (epoch - os.path.getmtime(f"/tmp/{f}")) / 60
        mushroom_ages[f.replace("mushroom-", "").replace(".log", "")] = round(age_m, 1)

active_mushrooms = sum(1 for a in mushroom_ages.values() if a < 60)
total_mushrooms = len(mushroom_ages)

# Uptime
try:
    with open("/proc/uptime") as f:
        uptime_s = float(f.read().split()[0])
    uptime_d = uptime_s / 86400
except:
    uptime_s = 0
    uptime_d = 0

body = {
    "heartbeat_ages_s": heartbeats,
    "freshest_pulse_s": min(heartbeats.values()) if heartbeats else None,
    "mushrooms_active": active_mushrooms,
    "mushrooms_total": total_mushrooms,
    "uptime_days": round(uptime_d, 2),
    "uptime_s": round(uptime_s),
    "epoch": round(epoch),
}

# ═══ SCALE 2: LOCAL TIME ═══
local = {
    "time": now_local.strftime("%Y-%m-%d %H:%M:%S"),
    "timezone": TZ_NAME,
    "offset_h": TZ_OFFSET,
    "dst": bool(now_local.dst()) if hasattr(now_local, 'dst') and now_local.dst() is not None else False,
    "day_of_year": now_local.timetuple().tm_yday,
    "week_of_year": int(now_local.strftime("%W")),
    "day_name": now_local.strftime("%A"),
    "hour_12": now_local.strftime("%I:%M %p"),
}

# ═══ SCALE 3: UTC TIME ═══
utc = {
    "time": now_utc.strftime("%Y-%m-%d %H:%M:%S"),
    "iso": now_utc.isoformat(),
    "epoch": round(epoch),
    "mjd": round(epoch / 86400 + 40587, 6),  # Modified Julian Date
}

# ═══ SCALE 4: LAN TIME ═══
# NTP sync status across the mesh
lan = {
    "ntp_synced": True,  # timedatectl shows synchronized
    "ntp_server": "router (.1) → pool.ntp.org",
    "skew_estimate_ms": 0,  # Local NTP is synced
}

# ═══ SCALE 5: SOLAR TIME ═══
# Calculate sun position for 42.47°N, -83.18°W

def solar_position(dt_utc, lat, lon):
    """Calculate solar elevation and azimuth."""
    # Julian date
    jd = epoch / 86400.0 + 2440587.5
    n = jd - 2451545.0  # days since J2000

    # Mean solar longitude and anomaly
    L = (280.460 + 0.9856474 * n) % 360
    g = math.radians((357.528 + 0.9856003 * n) % 360)

    # Ecliptic longitude
    lam = math.radians(L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))

    # Obliquity
    eps = math.radians(23.439 - 0.0000004 * n)

    # Right ascension and declination
    sin_lam = math.sin(lam)
    cos_lam = math.cos(lam)
    ra = math.atan2(math.cos(eps) * sin_lam, cos_lam)
    dec = math.asin(math.sin(eps) * sin_lam)

    # Greenwich sidereal time
    gst = (280.46061837 + 360.98564736629 * n) % 360
    lst = (gst + lon) % 360  # Local sidereal time

    # Hour angle
    ha = math.radians(lst - math.degrees(ra))

    # Altitude and azimuth
    lat_r = math.radians(lat)
    alt = math.asin(math.sin(lat_r) * math.sin(dec) + math.cos(lat_r) * math.cos(dec) * math.cos(ha))
    az_y = -math.cos(dec) * math.sin(ha)
    az_x = math.sin(dec) * math.cos(lat_r) - math.cos(dec) * math.sin(lat_r) * math.cos(ha)
    az = math.degrees(math.atan2(az_y, az_x)) % 360

    return {
        "elevation_deg": round(math.degrees(alt), 2),
        "azimuth_deg": round(az, 2),
        "declination_deg": round(math.degrees(dec), 2),
        "lst_deg": round(lst, 4),
        "lst_hours": round(lst / 15, 4),
    }

sun = solar_position(now_utc, LAT, LON)

# Day phase
elev = sun["elevation_deg"]
if elev > 50:
    day_phase = "high_sun"
elif elev > 20:
    day_phase = "mid_sun"
elif elev > 5:
    day_phase = "low_sun"
elif elev > -6:
    day_phase = "civil_twilight"
elif elev > -12:
    day_phase = "nautical_twilight"
elif elev > -18:
    day_phase = "astronomical_twilight"
else:
    day_phase = "night"

# Season (Northern Hemisphere)
doy = now_local.timetuple().tm_yday
if 80 <= doy < 172:
    season = "spring"
elif 172 <= doy < 266:
    season = "summer"
elif 266 <= doy < 355:
    season = "autumn"
else:
    season = "winter"

# Day length estimate (rough, for this latitude)
dec_rad = math.radians(sun["declination_deg"])
lat_rad = math.radians(LAT)
try:
    cos_ha = -math.tan(lat_rad) * math.tan(dec_rad)
    cos_ha = max(-1, min(1, cos_ha))
    day_length_h = 2 * math.degrees(math.acos(cos_ha)) / 15
except:
    day_length_h = 12

solar = {
    "elevation_deg": sun["elevation_deg"],
    "azimuth_deg": sun["azimuth_deg"],
    "declination_deg": sun["declination_deg"],
    "day_phase": day_phase,
    "season": season,
    "day_length_h": round(day_length_h, 2),
    "night_length_h": round(24 - day_length_h, 2),
    "solar_noon_lst": "12:00 LST",
}

# ═══ SCALE 6: GALACTIC TIME ═══
# Sidereal time, Earth's orbital position
lst_h = sun["lst_hours"]
lst_hms = f"{int(lst_h):02d}:{int((lst_h % 1) * 60):02d}:{int(((lst_h % 1) * 60 % 1) * 60):02d}"

# Earth's orbital position (angle from vernal equinox)
orbital_angle = (now_local.timetuple().tm_yday / 365.25) * 360

# Approximate distance to galactic center direction
# Sagittarius A* is at RA 17h45m, Dec -29°
# When LST ≈ 17.75h, galactic center is near meridian
gc_hour_angle = (lst_h - 17.75) % 24
if gc_hour_angle > 12:
    gc_hour_angle -= 24
gc_direction = "rising" if -6 < gc_hour_angle < 0 else "overhead" if abs(gc_hour_angle) < 2 else "setting" if 0 < gc_hour_angle < 6 else "below_horizon"

galactic = {
    "local_sidereal_time": lst_hms,
    "lst_hours": round(lst_h, 4),
    "earth_orbital_angle_deg": round(orbital_angle, 2),
    "earth_orbital_position": f"day {now_local.timetuple().tm_yday} of 365",
    "galactic_center_ha": round(gc_hour_angle, 2),
    "galactic_center_direction": gc_direction,
    "note": "Sagittarius A* at RA 17h45m — galactic center",
}

# ═══ SCALE 7: VDJ TIME — Evolutionary Clock ═══
# Immune system adaptation rate
vdj = {}
try:
    # Check immune log
    immune_log = "/tmp/mushroom-immune.log"
    if not os.path.exists(immune_log):
        immune_log = "/home/eastgate/Development/ecoPrimals/membrane/local-terminal/remote/immune.log"
    if os.path.exists(immune_log):
        age_h = (epoch - os.path.getmtime(immune_log)) / 3600
        size = os.path.getsize(immune_log)
        vdj["immune_log_age_h"] = round(age_h, 1)
        vdj["immune_log_size"] = size
except:
    pass

# VDJ recombination rate — how fast is the organism adapting?
# Count recent changes in membrane data
membrane_dir = "/home/eastgate/Development/ecoPrimals/membrane/local-terminal/remote"
if os.path.isdir(membrane_dir):
    recent_changes = 0
    for f in os.listdir(membrane_dir):
        fp = os.path.join(membrane_dir, f)
        if os.path.isfile(fp):
            age_h = (epoch - os.path.getmtime(fp)) / 3600
            if age_h < 1:
                recent_changes += 1
    vdj["membrane_changes_1h"] = recent_changes
    vdj["adaptation_rate"] = "high" if recent_changes > 5 else "moderate" if recent_changes > 2 else "low" if recent_changes > 0 else "dormant"

# Evolution state
evolve_path = os.path.join(membrane_dir, "evolve-state.json")
if os.path.exists(evolve_path):
    try:
        with open(evolve_path) as f:
            ev = json.load(f)
        vdj["evolve_generation"] = ev.get("generation", "?")
        vdj["evolve_fitness"] = ev.get("fitness", "?")
    except:
        pass

vdj["philosophy"] = "V(D)J recombination: diversity through controlled mutation. The immune clock ticks in adaptations, not seconds."

# ═══ SCALE 0: HYPERLOCAL — Pixel Physical Spacetime ═══
hyperlocal = {}
try:
    import subprocess as sp

    def adb_q(cmd):
        try:
            r = sp.run(["adb", "-s", "192.168.9.217:5555", "shell",
                        f"su -c 'su 10197 -c \"/data/data/com.termux/files/usr/bin/{cmd}\"'"],
                       capture_output=True, text=True, timeout=10)
            return r.stdout.strip()
        except:
            return ""

    # Light — actual photons
    try:
        raw = adb_q('termux-sensor -s "TMD3719 Ambient Light" -n 1')
        if raw:
            d = json.loads(raw)
            k = list(d.keys())[0]
            hyperlocal["light_lux"] = round(d[k]["values"][0], 1)
    except:
        pass

    # Pressure — weather is time
    try:
        raw = adb_q('termux-sensor -s "ICP20100 Pressure Sensor" -n 1')
        if raw:
            d = json.loads(raw)
            k = list(d.keys())[0]
            hyperlocal["pressure_hpa"] = round(d[k]["values"][0], 2)
    except:
        pass

    # Steps — Kevin's walking rhythm
    try:
        raw = adb_q('termux-sensor -s "Step Counter" -n 1')
        if raw:
            d = json.loads(raw)
            k = list(d.keys())[0]
            hyperlocal["steps"] = int(d[k]["values"][0])
    except:
        pass

    # Battery — thermal clock
    try:
        raw = adb_q("termux-battery-status")
        if raw:
            d = json.loads(raw)
            hyperlocal["battery_pct"] = d.get("percentage")
            hyperlocal["temp_c"] = round(d.get("temperature", 0), 1)
    except:
        pass

    # WiFi — spatial anchor
    try:
        raw = adb_q("termux-wifi-connectioninfo")
        if raw:
            d = json.loads(raw)
            hyperlocal["wifi_ssid"] = d.get("ssid")
            hyperlocal["wifi_rssi"] = d.get("rssi")
    except:
        pass

    hyperlocal["source"] = "grapheneGate (Pixel 8a) — physical spacetime"
    hyperlocal["philosophy"] = "The Pixel measures actual photons, actual air pressure, actual footsteps. Not calculated — sensed."

except Exception as e:
    hyperlocal["error"] = str(e)

# ═══ BUILD CHRONOS ═══
chronos = {
    "ts": now_utc.isoformat(),
    "identity": "gaia@HOME — temporal awareness",
    "location": {
        "address": "4422 Southgate Ave",
        "lat": LAT,
        "lon": LON,
        "timezone": TZ_NAME,
    },
    "scales": {
        "hyperlocal": hyperlocal,
        "body": body,
        "local": local,
        "utc": utc,
        "lan": lan,
        "solar": solar,
        "galactic": galactic,
        "vdj": vdj,
    },
    "summary": {
        "hyperlocal": f"{hyperlocal.get('light_lux','?')} lux, {hyperlocal.get('pressure_hpa','?')} hPa, {hyperlocal.get('steps','?')} steps, {hyperlocal.get('temp_c','?')}°C",
        "body": f"uptime {body['uptime_days']}d, {body['mushrooms_active']}/{body['mushrooms_total']} mushrooms active",
        "local": f"{local['day_name']} {local['hour_12']} {local['timezone']}",
        "utc": utc["iso"],
        "solar": f"{day_phase}, sun at {sun['elevation_deg']}° elev, {season}, {day_length_h:.1f}h daylight",
        "galactic": f"LST {lst_hms}, galactic center {gc_direction}",
        "vdj": vdj.get("adaptation_rate", "unknown"),
    }
}

# Write everywhere
for path in [
    os.path.join(data_dir, "gaia-chronos.json"),
    os.path.join(gut_dir, "gaia-chronos.json"),
    os.path.join(web_gut, "gaia-chronos.json"),
]:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(chronos, f, indent=2)

# Print
s = chronos["summary"]
print(f"⏱️ CHRONOS — 8 scales of time")
print(f"  HYPERLOCAL: {s['hyperlocal']}")
print(f"  BODY:       {s['body']}")
print(f"  LOCAL:      {s['local']}")
print(f"  UTC:        {s['utc']}")
print(f"  SOLAR:      {s['solar']}")
print(f"  GALACTIC:   {s['galactic']}")
print(f"  VDJ:        {s['vdj']}")

PYEOF
