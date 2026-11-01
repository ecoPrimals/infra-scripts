"""Fix the membrane bus to use catch-and-throw rotation.

Problem: 20 cortical stops, 2 slots per cycle. Only the first 2 ever run.
The 3 backscatters at positions 14-17 NEVER fire.

Fix: Round-robin offset per tier. Each cycle starts from where it left off.
- CATCH: pressure accumulates while you wait (gradient grows)
- THROW: when your turn comes AND gradient is ready, fire
- PING: this cycle catches state
- PONG: next cycle throws from the caught position

The latency between cycles is the resource, not the problem.
"""

import sys

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/opt/membrane/membrane-bus.py"

    with open(path) as f:
        content = f.read()

    old_dispatch = """    for stop in BUS:
        name = stop["name"]
        tier = stop["tier"]
        threshold = THRESHOLDS[tier]

        # Back pressure check
        if is_locked(name):
            log("  \\u25c4 %s (back pressure)" % name)
            skipped["backpressure"] += 1
            continue

        # Gradient check (vital always passes)
        g = gradient(stop["reads"], stop["writes"])
        if tier != "vital" and g < threshold:
            # Not enough pressure to flow
            continue

        # Aperture check \\u2014 narrow aperture limits lower-priority tiers
        tier_max = MAX_PER_TIER[tier]
        if apt < 0.3:
            tier_max = max(1, tier_max // 3)
        elif apt < 0.6:
            tier_max = max(1, tier_max // 2)

        if ran[tier] >= tier_max:
            log("  \\u25cb %s (aperture narrow, tier %s full)" % (name, tier))
            skipped["aperture"] += 1
            continue

        # Motor drips if aperture is open at all (floor 0.12). Was 0.4 \\u2014
        # on a 1-CPU VPS that brick-walled the colon.
        if tier == "motor" and apt < 0.10:
            log("  \\u25cb %s (motor deferred, aperture=%.2f)" % (name, apt))
            skipped["aperture"] += 1
            continue

        # FLOW
        run(name, stop["cmd"], timeout=stop["timeout"])
        ran[tier] += 1"""

    new_dispatch = """    # ═══ CATCH-AND-THROW ROTATION ═══
    # Group stops by tier for round-robin. Each tier remembers its offset.
    # CATCH = where we left off last cycle. THROW = start there this cycle.
    # The latency between cycles is the ping-pong — deliberate, not random.
    tier_stops = {"vital": [], "sensory": [], "cortical": [], "motor": []}
    for i, stop in enumerate(BUS):
        tier_stops[stop["tier"]].append((i, stop))

    offsets = state.get("tier_offsets", {"vital": 0, "sensory": 0, "cortical": 0, "motor": 0})

    for tier in ["vital", "sensory", "cortical", "motor"]:
        stops = tier_stops[tier]
        if not stops:
            continue
        threshold = THRESHOLDS[tier]
        tier_max = MAX_PER_TIER[tier]
        if apt < 0.3:
            tier_max = max(1, tier_max // 3)
        elif apt < 0.6:
            tier_max = max(1, tier_max // 2)

        # Motor gate — drip requires minimum aperture
        if tier == "motor" and apt < 0.10:
            for _, stop in stops:
                log("  ○ %s (motor deferred, aperture=%.2f)" % (stop["name"], apt))
                skipped["aperture"] += 1
            continue

        # CATCH: start from where we left off (round-robin offset)
        offset = offsets.get(tier, 0) % len(stops)
        rotated = stops[offset:] + stops[:offset]

        threw = 0  # how many we threw this cycle
        for _, stop in rotated:
            name = stop["name"]

            # Back pressure
            if is_locked(name):
                log("  ◄ %s (back pressure)" % name)
                skipped["backpressure"] += 1
                continue

            # Gradient check (vital always passes)
            g = gradient(stop["reads"], stop["writes"])
            if tier != "vital" and g < threshold:
                continue

            # Aperture: tier full?
            if ran[tier] >= tier_max:
                log("  ○ %s (aperture narrow, tier %s full)" % (name, tier))
                skipped["aperture"] += 1
                continue

            # THROW — planned, held, focused
            run(name, stop["cmd"], timeout=stop["timeout"])
            ran[tier] += 1
            threw += 1

        # PONG: advance offset by how many we threw (or at least 1 to avoid starvation)
        offsets[tier] = (offset + max(threw, 1)) % len(stops)

    state["tier_offsets"] = offsets"""

    if old_dispatch in content:
        content = content.replace(old_dispatch, new_dispatch)
        with open(path, "w") as f:
            f.write(content)
        print("OK: bus dispatch rewritten with catch-and-throw rotation")
    else:
        print("WARN: exact match not found. Checking for partial match...")
        if "for stop in BUS:" in content:
            idx = content.index("for stop in BUS:")
            block = content[idx:idx+100]
            print("Found 'for stop in BUS:' at offset %d" % idx)
            print("Context: %s" % repr(block[:80]))
        else:
            print("'for stop in BUS:' not found — dispatch may already be rewritten")

if __name__ == "__main__":
    main()
