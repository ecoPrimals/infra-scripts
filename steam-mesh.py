#!/usr/bin/env python3
"""steam-mesh.py — Steam as organism lubricant
HTTP daemon on :8085 — coordinates Steam across all gates

Endpoints:
  GET  /mesh          — full mesh status (which gates have Steam, what's installed)
  GET  /vr            — VR library status across mesh
  GET  /stream?from=X — find best gate to stream from
  POST /install       — queue install on a gate (via pony express)
  GET  /remoteplay    — Remote Play configuration guide
"""
import http.server
import json
import subprocess
import socket
from datetime import datetime
from urllib.parse import urlparse, parse_qs

PORT = 8085

VR_GAMES = {
    552440: {"name": "The Talos Principle VR", "size_gb": 6, "year": 2017},
    617830: {"name": "SUPERHOT VR", "size_gb": 4, "year": 2017},
    555880: {"name": "Sairento VR", "size_gb": 12, "year": 2018},
    489380: {"name": "QuiVR", "size_gb": 2, "year": 2017},
    477270: {"name": "Lightblade VR", "size_gb": 1, "year": 2016},
    747350: {"name": "Hellblade Senua VR", "size_gb": 25, "year": 2018},
    486780: {"name": "Fruit Ninja VR", "size_gb": 1, "year": 2016},
    342180: {"name": "Arizona Sunshine", "size_gb": 12, "year": 2016},
    250820: {"name": "SteamVR", "size_gb": 5, "year": 2016},
}

GATES = {
    "eastGate":  {"ip": "192.168.4.244", "gpu": "RTX 4070",  "vram": 12, "role": "BRAIN"},
    "northGate": {"ip": "192.168.4.147", "gpu": "RTX 5090",  "vram": 32, "role": "HEART"},
    "ironGate":  {"ip": "192.168.4.237", "gpu": "RTX 5070",  "vram": 12, "role": "IRON MTN"},
    "southGate": {"ip": "192.168.4.148", "gpu": "RTX 4060",  "vram": 8,  "role": "SOUTH POLE"},
    "swiftGate": {"ip": "192.168.4.100", "gpu": "RTX 3070",  "vram": 8,  "role": "POLARIS H2"},
    "deckGate":  {"ip": "192.168.4.176", "gpu": "RDNA 2",    "vram": 1,  "role": "DISPLAY"},
    "frameGate": {"ip": "192.168.4.181", "gpu": "Adreno 750", "vram": 0, "role": "FACE"},
}

STEAM_PORTS = {
    "client": 27060,
    "remote_play": 27036,
    "remote_play_tcp": 27037,
    "web": 8080,
}

def probe_gate(name, info):
    """Quick probe a gate for Steam presence."""
    ip = info["ip"]
    result = {"name": name, **info, "alive": False, "steam": False, "remote_play": False}
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((ip, 22))  # SSH as alive check
        s.close()
        result["alive"] = True
    except:
        try:
            ret = subprocess.run(["ping", "-c", "1", "-W", "1", ip],
                               capture_output=True, timeout=2)
            result["alive"] = ret.returncode == 0
        except:
            pass
    
    if result["alive"]:
        for port_name, port in [("steam", 27060), ("remote_play", 27036)]:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                s.connect((ip, port))
                s.close()
                result[port_name] = True
            except:
                pass
    
    return result

class SteamMeshHandler(http.server.BaseHTTPRequestHandler):
    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def do_GET(self):
        url = urlparse(self.path)
        params = parse_qs(url.query)

        if url.path == "/mesh":
            gates = {name: probe_gate(name, info) for name, info in GATES.items()}
            steam_active = [n for n, g in gates.items() if g["steam"]]
            rp_active = [n for n, g in gates.items() if g["remote_play"]]
            self._json(200, {
                "timestamp": datetime.now().isoformat(),
                "family": "gaia@gaming",
                "members": ["gaia", "Tamison", "Napalm", "AvatarLeo (pending)"],
                "gates": gates,
                "steam_active": steam_active,
                "remote_play_active": rp_active,
                "total_vr_games": len(VR_GAMES),
            })

        elif url.path == "/vr":
            self._json(200, {
                "source": "Napalm (HTC Vive era, ~2016-2018)",
                "family": "gaia@gaming",
                "games": VR_GAMES,
                "total_size_gb": sum(g["size_gb"] for g in VR_GAMES.values()),
                "recommended_host": "northGate (RTX 5090, 32GB VRAM)",
                "stream_targets": ["deckGate", "frameGate", "swiftGate"],
                "install_script": "infra/scripts/steam-vr-install.sh",
            })

        elif url.path == "/stream":
            source = params.get("from", [None])[0]
            gates_probed = {name: probe_gate(name, info) for name, info in GATES.items()}
            
            # Rank gates by streaming capability
            ranked = []
            for name, gate in gates_probed.items():
                if gate["alive"] and gate["remote_play"]:
                    score = gate["vram"] * 10 + (100 if gate["steam"] else 0)
                    ranked.append({"gate": name, "score": score, **gate})
            
            ranked.sort(key=lambda x: x["score"], reverse=True)
            self._json(200, {
                "best_source": ranked[0]["gate"] if ranked else "none",
                "ranked": ranked,
                "tip": "Use Steam Remote Play from the best source to your target device",
            })

        elif url.path == "/remoteplay":
            self._json(200, {
                "setup": {
                    "1_host": "Install VR games on northGate (RTX 5090) — run steam-vr-install.sh",
                    "2_enable": "Steam > Settings > Remote Play > Enable Remote Play",
                    "3_pair": "On target device: Steam > Remote Play > pair with host",
                    "4_play": "Games show 'Stream' button instead of 'Install'",
                },
                "optimization": {
                    "codec": "HEVC (H.265) preferred over H.264 for VR latency",
                    "resolution": "Match target display (Frame=1080p, Deck=800p)",
                    "bitrate": "50+ Mbps for VR (10G spine handles this easily)",
                    "network": "Wired preferred. 10G spine = ~1.67ms latency. Perfect for streaming.",
                },
                "vr_streaming": {
                    "note": "VR streaming adds latency. For best experience:",
                    "option_1": "Play VR directly on northGate (tethered headset)",
                    "option_2": "Stream flat games to Deck/Frame, play VR on host",
                    "option_3": "Use SteamVR + Virtual Desktop for wireless VR",
                },
            })

        else:
            self._json(404, {"error": "unknown", "endpoints": ["/mesh", "/vr", "/stream", "/remoteplay"]})

    def log_message(self, fmt, *args):
        print(f"[steam-mesh] {self.client_address[0]} {fmt % args}")

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), SteamMeshHandler)
    print(f"🎮 Steam Mesh Lubricant on :{PORT}")
    print(f"   /mesh       — full mesh probe")
    print(f"   /vr         — VR library info")
    print(f"   /stream     — best streaming source")
    print(f"   /remoteplay — setup guide")
    server.serve_forever()
