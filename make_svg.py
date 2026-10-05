#!/usr/bin/env python3
"""Neofetch-style GitHub profile card generator.

Usage:
  python make_svg.py                    # basic card (NS banner art)
  python make_svg.py --photo me.jpg     # ASCII art from your photo (needs: pip install pillow)
  python make_svg.py --live             # also fetch live GitHub stats
"""
import sys, os, json, html, urllib.request

USER = "nekalsalaria"
W = 62            # right panel width in characters
CW = 8.4          # char width (px) of right panel, font-size 14
LH = 21           # right panel line height
ACOLS = 46        # ascii art columns

# ---------- edit your info here ----------
INFO = [
    ("head", "nekal@salaria"),
    ("kv", "Role", "SDE & Mentor"),
    ("kv", "Company", "REGex Software Services"),
    ("kv", "Location", "Jaipur, India"),
    ("kv", "Education", "B.Tech CSE, SKIT Jaipur"),
    ("blank",),
    ("kv", "Languages.Programming", "JavaScript, C++, C, SQL"),
    ("kv", "Languages.Frontend", "React.js, Tailwind CSS"),
    ("kv", "Languages.Backend", "Node.js, Express, Socket.IO"),
    ("kv", "Languages.Real", "Hindi, English"),
    ("blank",),
    ("kv", "Databases", "MongoDB, PostgreSQL"),
    ("kv", "Hobbies.Software", "DSA, Competitive Programming"),
    ("kv", "Hobbies.Teaching", "100+ Live Batches"),
    ("blank",),
    ("sec", "Contact"),
    ("kv", "Email.Personal", "nekalsingh987@gmail.com"),
    ("kv", "LinkedIn", "nekalsingh"),
    ("kv", "LeetCode", "nekalsingh987"),
    ("kv", "Website", "nikkuthecoder.site"),
    ("blank",),
    ("sec", "Stats"),
    ("kv", "LeetCode.Solved", "800+"),
    ("kv", "LeetCode.Rating", "1700+ (20+ contests)"),
    ("kv", "Students.Mentored", "1000+"),
    ("pair", "Repos", "{repos}", "Stars", "{stars}"),
    ("pair", "Commits", "{commits}", "Followers", "{followers}"),
]
# ------------------------------------------

C = dict(bg="#0d1117", key="#ffa657", val="#a5d6ff", dot="#484f58",
         head="#e6edf3", art="#7ee787", sec="#e6edf3")


def api(path):
    req = urllib.request.Request("https://api.github.com" + path,
                                 headers={"Accept": "application/vnd.github+json"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", "Bearer " + tok)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def live_stats():
    s = dict(repos="n/a", stars="n/a", commits="n/a", followers="n/a")
    try:
        u = api(f"/users/{USER}")
        s["repos"], s["followers"] = str(u["public_repos"]), str(u["followers"])
        stars, page = 0, 1
        while True:
            repos = api(f"/users/{USER}/repos?per_page=100&page={page}")
            stars += sum(r["stargazers_count"] for r in repos)
            if len(repos) < 100:
                break
            page += 1
        s["stars"] = str(stars)
        s["commits"] = f'{api(f"/search/commits?q=author:{USER}&per_page=1")["total_count"]:,}'
    except Exception as e:
        print("stats fetch failed:", e, file=sys.stderr)
    return s


def fallback_art():
    N = ["X...X", "XX..X", "X.X.X", "X..XX", "X...X", "X...X", "X...X"]
    S = [".XXXX", "X....", "X....", ".XXX.", "....X", "....X", "XXXX."]
    rows, k = [], 0
    for r in range(7):
        line_set = []
        for _ in range(5):
            line = ""
            for glyph in (N, S):
                for ch in glyph[r]:
                    for _ in range(4):
                        line += ("01"[k % 2] if ch == "X" else " ")
                        k += 1
                line += "    "
            line_set.append(line.rstrip())
        rows += line_set
    pad = (ACOLS - max(len(x) for x in rows)) // 2
    return [" " * max(pad, 0) + x for x in rows]


def photo_art(path):
    from PIL import Image, ImageOps
    ramp = " .:-=+*#%@"
    img = ImageOps.autocontrast(Image.open(path).convert("L"))
    h = int(img.height / img.width * ACOLS / 2.3)
    img = img.resize((ACOLS, h))
    px = img.load()
    return ["".join(ramp[px[x, y] * (len(ramp) - 1) // 255] for x in range(ACOLS)).rstrip()
            for y in range(h)]


def esc(t):
    return html.escape(t, quote=False)


def right_lines(stats):
    out = []  # each line: list of (text, color)
    for row in INFO:
        t = row[0]
        if t == "blank":
            out.append([(". ", C["dot"])])
        elif t == "head":
            out.append([(row[1] + " ", C["head"]), ("-" * (W - len(row[1]) - 1), C["dot"])])
        elif t == "sec":
            out.append([("- " + row[1] + " ", C["sec"]), ("-" * (W - len(row[1]) - 4), C["dot"])])
        elif t == "kv":
            k, v = row[1], row[2]
            n = W - (2 + len(k) + 1 + 1 + 1 + len(v))
            out.append([(". ", C["dot"]), (k + ":", C["key"]), (" " + "." * n + " ", C["dot"]), (v, C["val"])])
        elif t == "pair":
            k1, v1, k2, v2 = row[1], row[2].format(**stats), row[3], row[4].format(**stats)
            left = f"{k1}: {v1}"
            right = f"{k2}: {v2}"
            n = W - (2 + len(left) + 3 + len(right))
            out.append([(". ", C["dot"]), (k1 + ": ", C["key"]), (v1, C["val"]),
                        (" " + "." * max(n, 1) + " ", C["dot"]),
                        (k2 + ": ", C["key"]), (v2, C["val"])])
    return out


def build(stats, art):
    lines = right_lines(stats)
    H = 40 + len(lines) * LH + 10
    ax, rx = 28, 28 + ACOLS * 6 + 30
    width = int(rx + W * CW + 28)
    alh = (H - 50) / max(len(art), 1)
    alh = min(alh, 14)
    ay = 30 + ((H - 50) - alh * len(art)) / 2
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{H}" viewBox="0 0 {width} {H}">',
         f'<rect width="100%" height="100%" rx="14" fill="{C["bg"]}"/>',
         '<style>text{font-family:Consolas,"SF Mono","DejaVu Sans Mono",monospace;white-space:pre}'
         '.a{font-size:10px}.r{font-size:14px}'
         '@keyframes f{from{opacity:0}to{opacity:1}}'
         '.a,.r{animation:f .6s ease both}</style>']
    for i, line in enumerate(art):
        s.append(f'<text class="a" x="{ax}" y="{ay + i * alh:.1f}" fill="{C["art"]}" '
                 f'textLength="{len(line) * 6}" lengthAdjust="spacing" '
                 f'style="animation-delay:{i * 0.02:.2f}s">{esc(line)}</text>')
    for i, parts in enumerate(lines):
        y = 38 + i * LH
        n = sum(len(p[0]) for p in parts)
        spans = "".join(f'<tspan fill="{c}">{esc(t)}</tspan>' for t, c in parts)
        s.append(f'<text class="r" x="{rx}" y="{y}" textLength="{n * CW:.1f}" lengthAdjust="spacing" '
                 f'style="animation-delay:{0.3 + i * 0.04:.2f}s">{spans}</text>')
    s.append("</svg>")
    return "\n".join(s)


def main():
    args = sys.argv[1:]
    stats = live_stats() if "--live" in args else dict(repos="--", stars="--", commits="--", followers="--")
    here = os.path.dirname(os.path.abspath(__file__))
    cache = os.path.join(here, "ascii.txt")
    if "--photo" in args:
        art = photo_art(args[args.index("--photo") + 1])
        open(cache, "w").write("\n".join(art))
    elif os.path.exists(cache):
        art = open(cache).read().split("\n")
    else:
        art = fallback_art()
    open(os.path.join(here, "profile.svg"), "w").write(build(stats, art))
    print("profile.svg generated")


if __name__ == "__main__":
    main()
