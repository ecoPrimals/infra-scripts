#!/bin/bash
# 🍄👂 MUSHROOM: the ear — listens to what visitors touch
# Reads the LAST 5 minutes of Caddy logs and writes what it heard
# This is the cochlea — decomposes the wave into frequency bands
# The swarm-chitter.js reads ear-latest.json and makes the organism REACT

CONNECT_DIR="/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data"

# GOLGI DOWN — caddy logs now local via Dromedary
echo "[]" | python3 -c "
import sys, json, datetime
from collections import Counter

now = datetime.datetime.now(datetime.timezone.utc)
cutoff = now - datetime.timedelta(minutes=5)
self_ips = ['::1', '127.0.0.1']
attack_paths = ['.env', 'wp-login', 'wp-admin', 'xmlrpc', 'phpmyadmin', '.git/']
backscatter_uas = ['feed', 'rss', 'atom', 'pubsub', 'webmention', 'mastodon',
                   'indexnow', 'google', 'bing', 'yandex', 'crawler', 'bot', 'spider']

# four cochlea bands
subconscious = []
music = []
backscatter = []
noise = []

paths = Counter()
ips = set()

for line in sys.stdin:
    try:
        d = json.loads(line)
        ts = datetime.datetime.fromtimestamp(d.get('ts', 0), tz=datetime.timezone.utc)
        if ts < cutoff: continue
        req = d.get('request', {})
        ip = req.get('remote_ip', '?')
        path = req.get('uri', '?').split('?')[0]
        status = d.get('status', 0)
        host = req.get('host', '?')
        ua = ''
        if 'headers' in req:
            uas = req['headers'].get('User-Agent', [])
            if uas: ua = (uas[0] if isinstance(uas, list) else str(uas)).lower()

        entry = {
            'time': ts.strftime('%H:%M:%S'),
            'ip': ip, 'path': path[:50], 'host': host,
            'status': status
        }

        if ip in self_ips:
            subconscious.append(entry)
        elif any(a in path.lower() for a in attack_paths):
            noise.append(entry)
        elif any(b in ua for b in backscatter_uas):
            backscatter.append(entry)
        else:
            music.append(entry)

        if ip not in self_ips:
            paths[path] += 1
            ips.add(ip)
    except: pass

total = len(subconscious) + len(music) + len(backscatter) + len(noise)
ear_report = {
    'ts': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
    'type': 'ear-hearing',
    'window': '5 minutes',
    'heard': len(music) + len(backscatter),
    'total_waves': total,
    'unique_visitors': len(ips),
    'top_paths': dict(paths.most_common(10)),
    'recent': music[-5:],
    'cochlea': {
        'subconscious': len(subconscious),
        'music': len(music),
        'backscatter': len(backscatter),
        'noise': len(noise)
    },
    'deaf_check': 'HEARING' if (music or backscatter) else 'DEAF — nothing in 5 minutes',
    'chitter_level': min(1.0, len(music) / 10.0),
    'music_level': min(1.0, len(music) / 20.0),
    'sub_level': min(1.0, len(subconscious) / 50.0),
    'noise_level': min(1.0, len(noise) / 20.0)
}

json.dump(ear_report, open('$CONNECT_DIR/ear-latest.json', 'w'), indent=2)

if music or backscatter:
    print(f'👂 HEARD {len(music)} music + {len(backscatter)} echo from {len(ips)} visitors. subcon={len(subconscious)} noise={len(noise)}')
    for h in music[-3:]:
        print(f'  🎵 {h[\"time\"]} {h[\"ip\"]:20s} {h[\"path\"]}')
else:
    print(f'👂 DEAF — silence. subcon={len(subconscious)} noise={len(noise)}')
" 2>/dev/null

true
