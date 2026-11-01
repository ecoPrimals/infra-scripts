#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# stoichiometric-mass.py — Shannon entropy page mass calculator
#
# Computes information mass for Zola pages and writes weight into frontmatter.
# Mass = sqrt(words) × H × (1 + links/50) × (1 + citations/10) × richness
#
# where:
#   H        = Shannon entropy of word frequency distribution (bits)
#   richness = unique_words / total_words (vocabulary diversity)
#   links    = markdown link count (connectivity)
#   citations = evidence citation count (grounding)
#
# Stoichiometric: each page's weight is proportional to its information
# content relative to the corpus. The heaviest page gets weight 200.
# Shannon's π: probability distribution of words → entropy → mass.
#
# Usage:
#   python3 stoichiometric-mass.py /path/to/site/content [--dry-run]
#
# Kevin Mok / Tamison / ecoPrimal / attsi
# ORCID 0009-0004-2141-0321

import os
import sys
import math
import re
import collections

def shannon_entropy(text):
    """Shannon entropy of word frequency distribution (bits)."""
    words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
    if not words:
        return 0.0
    freq = collections.Counter(words)
    total = len(words)
    return -sum((c / total) * math.log2(c / total) for c in freq.values())


def page_mass(filepath):
    """Compute stoichiometric information mass for a page."""
    with open(filepath, 'r', errors='replace') as f:
        raw = f.read()

    fmt = detect_frontmatter(raw)
    if fmt == 'toml':
        parts = raw.split('+++')
        body = '+++'.join(parts[2:]) if len(parts) >= 3 else raw
    elif fmt == 'yaml':
        parts = raw.split('---')
        body = '---'.join(parts[2:]) if len(parts) >= 3 else raw
    else:
        body = raw

    words = re.findall(r'\b[a-zA-Z]{2,}\b', body.lower())
    wc = len(words)
    uw = len(set(words))
    links = len(re.findall(r'\[.*?\]\(.*?\)', body))
    cites = len(re.findall(
        r'(?:FOIA|LARA|MDOC|ICHAT|PACER|CFRS|MDE|docket|case\s+no)',
        body, re.I
    ))
    H = shannon_entropy(body)
    richness = uw / max(wc, 1)
    bulk = math.sqrt(wc)
    connectivity = 1 + links / 50.0
    grounding = 1 + cites / 10.0
    mass = bulk * H * connectivity * grounding * richness

    return {
        'words': wc, 'unique': uw, 'links': links, 'citations': cites,
        'H': round(H, 3), 'richness': round(richness, 3), 'mass': round(mass, 2),
    }


def detect_frontmatter(raw):
    stripped = raw.lstrip()
    if stripped.startswith('+++'):
        return 'toml'
    elif stripped.startswith('---'):
        return 'yaml'
    return None


def set_weight(filepath, weight):
    """Write weight into TOML or YAML frontmatter."""
    with open(filepath, 'r', errors='replace') as f:
        raw = f.read()

    fmt = detect_frontmatter(raw)
    if fmt == 'toml':
        sep = '+++'
        weight_line = f'weight = {weight}'
        weight_prefix = 'weight'
        date_prefix = 'date'
    elif fmt == 'yaml':
        sep = '---'
        weight_line = f'weight: {weight}'
        weight_prefix = 'weight:'
        date_prefix = 'date:'
    else:
        return False

    parts = raw.split(sep)
    if len(parts) < 3:
        return False

    lines = parts[1].split('\n')
    new_lines = []
    found = False
    for line in lines:
        if line.strip().startswith(weight_prefix):
            new_lines.append(weight_line)
            found = True
        else:
            new_lines.append(line)

    if not found:
        inserted = False
        for i, line in enumerate(new_lines):
            if line.strip().startswith(date_prefix):
                new_lines.insert(i + 1, weight_line)
                inserted = True
                break
        if not inserted:
            new_lines.append(weight_line)

    with open(filepath, 'w') as f:
        f.write(sep + '\n'.join(new_lines) + sep + sep.join(parts[2:]))
    return True


SORTED_SECTIONS = [
    'analysis', 'books', 'evidence', 'network', 'path', 'signal',
    'actors', 'braid', 'investigate', 'synthesis', 'coverage',
]


def main():
    content_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    dry_run = '--dry-run' in sys.argv

    os.chdir(content_dir)

    all_pages = []
    for section in SORTED_SECTIONS:
        if not os.path.isdir(section):
            continue
        for root, _, files in os.walk(section):
            for fname in files:
                if fname == '_index.md' or not fname.endswith('.md'):
                    continue
                fpath = os.path.join(root, fname)
                info = page_mass(fpath)
                info['file'] = fpath
                info['section'] = section
                all_pages.append(info)

    if not all_pages:
        print("No pages found.")
        return

    all_pages.sort(key=lambda x: x['mass'], reverse=True)
    max_mass = max(p['mass'] for p in all_pages)

    print(f"Pages: {len(all_pages)}")
    print(f"Mass range: {min(p['mass'] for p in all_pages):.1f} — {max_mass:.1f}")
    print(f"Mean H: {sum(p['H'] for p in all_pages) / len(all_pages):.3f} bits")
    print(f"Formula: sqrt(words) × H × (1+links/50) × (1+citations/10) × richness")
    print()

    print(f"{'Wt':>4} {'Mass':>8} {'H':>6} {'Words':>5} {'Lnk':>4} {'Cit':>3}  File")
    for p in all_pages[:15]:
        w = max(1, int(200 * p['mass'] / max_mass))
        print(f"{w:>4} {p['mass']:>8.1f} {p['H']:>6.3f} {p['words']:>5} {p['links']:>4} {p['citations']:>3}  {p['file']}")
    print("  ...")
    for p in all_pages[-5:]:
        w = max(1, int(200 * p['mass'] / max_mass))
        print(f"{w:>4} {p['mass']:>8.1f} {p['H']:>6.3f} {p['words']:>5} {p['links']:>4} {p['citations']:>3}  {p['file']}")

    if dry_run:
        print("\n[dry run — no files modified]")
        return

    updated = 0
    for p in all_pages:
        weight = max(1, int(200 * p['mass'] / max_mass))
        if set_weight(p['file'], weight):
            updated += 1

    print(f"\nUpdated {updated} pages with stoichiometric mass weights (1-200)")


if __name__ == '__main__':
    main()
