#!/usr/bin/env python3
"""Check the X11 GUI's control table against the plugin TTL and the pedal face CSS.

The X11 GUI (plugins/taj-mahal/x11ui/) has its port numbers, ranges and knob
positions typed in by hand. This catches drift after a port or face change:

    python3 tools/check_x11ui.py

Exit code 0 = in step, 1 = mismatch (each one listed).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "plugins/taj-mahal/x11ui/nhe-taj-mahal_x11ui.c"
TTL = ROOT / "bundle/nhe-taj-mahal.lv2/nhe-taj-mahal.ttl"
CSS = ROOT / "bundle/nhe-taj-mahal.lv2/modgui/stylesheet-tajmahal.css"
CSS_PREFIX = "tm-"                      # .tm-<symbol> in the stylesheet
BUTTON_CLASS = {"lv2_enabled": "onoff"}  # symbols whose CSS class differs


def ttl_ports(text):
    ports = {}
    for block in re.split(r"\]\s*,\s*\[|lv2:port\s*\[", text)[1:]:
        idx = re.search(r"lv2:index\s+(\d+)", block)
        sym = re.search(r'lv2:symbol\s+"([^"]+)"', block)
        if not (idx and sym):
            continue
        num = lambda k: (lambda m: float(m.group(1)) if m else None)(
            re.search(r"lv2:%s\s+(-?[\d.]+)" % k, block))
        ports[int(idx.group(1))] = dict(symbol=sym.group(1), min=num("minimum"),
                                        max=num("maximum"), default=num("default"))
    return ports


def css_positions(text):
    pos = {}
    for cls, body in re.findall(r"\.%s([\w-]+)\s*\{([^}]*)\}" % CSS_PREFIX, text):
        left = re.search(r"left:\s*(-?\d+)px", body)
        top = re.search(r"top:\s*(-?\d+)px", body)
        entry = pos.setdefault(cls, {})
        if left:
            entry["x"] = int(left.group(1))
        if top:
            entry["y"] = int(top.group(1))
    return pos


def c_controls(text):
    rows = re.findall(r"\{\s*(KNOB|BUTTON)\s*,\s*(\d+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,"
                      r"\s*(-?[\d.]+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*\}", text)
    return [dict(kind=k, port=int(p), min=float(a), max=float(b), default=float(d),
                 x=int(x), y=int(y)) for k, p, a, b, d, x, y in rows]


def main():
    ports = ttl_ports(TTL.read_text())
    css = css_positions(CSS.read_text())
    controls = c_controls(SRC.read_text())
    problems = []

    if not controls:
        problems.append("no control table found in %s" % SRC.name)

    seen = set()
    for c in controls:
        p = ports.get(c["port"])
        if not p:
            problems.append("port %d: not in the TTL" % c["port"])
            continue
        seen.add(c["port"])
        sym = p["symbol"]
        for k in ("min", "max", "default"):
            if p[k] is not None and abs(p[k] - c[k]) > 1e-6:
                problems.append("%s (port %d): %s is %g in the GUI, %g in the TTL"
                                % (sym, c["port"], k, c[k], p[k]))
        cls = BUTTON_CLASS.get(sym, sym)
        where = dict(css.get("button", {}) if c["kind"] == "BUTTON" else {})
        where.update(css.get(cls, {}))
        if "x" not in where or "y" not in where:
            problems.append("%s: no .%s%s position in the stylesheet" % (sym, CSS_PREFIX, cls))
            continue
        if (where["x"], where["y"]) != (c["x"], c["y"]):
            problems.append("%s: GUI draws it at (%d,%d), the face has it at (%d,%d)"
                            % (sym, c["x"], c["y"], where["x"], where["y"]))

    # every control port in the TTL should be on the GUI
    for idx, p in sorted(ports.items()):
        if p["min"] is not None and idx not in seen:
            problems.append("%s (port %d): in the TTL but not on the X11 GUI" % (p["symbol"], idx))

    if problems:
        print("X11 GUI out of step with the plugin:")
        for line in problems:
            print("  - " + line)
        return 1
    print("X11 GUI in step: %d controls match the TTL and the face." % len(controls))
    return 0


if __name__ == "__main__":
    sys.exit(main())
