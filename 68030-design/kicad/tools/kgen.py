"""Small KiCad 9 schematic generator (S-expression writer) used to build the m68030-sbc schematic.
Coordinates are schematic mm (Y down). Library pin coordinates are Y-up and are transformed here."""
import uuid as _uuid, math, copy, os, re, hashlib
from sexp import parse, dump, Sym, find, findall, q

STOCK = "/usr/share/kicad/symbols"
PROJECT = "m68030-sbc"
_ns = _uuid.UUID("6b1d2c1e-7a55-4f0e-9d6a-68030c0ffee0")
def U(*key):
    """deterministic uuid from a key (stable across regenerations)"""
    return str(_uuid.uuid5(_ns, "/".join(str(k) for k in key)))

def snap(v, g=1.27):
    return round(round(v / g) * g, 4)

# ---------------------------------------------------------------- libraries
class Libs:
    def __init__(self, extra):
        self.paths = {}          # nickname -> file
        self.cache = {}
        for f in os.listdir(STOCK):
            if f.endswith(".kicad_sym"):
                self.paths[f[:-10]] = os.path.join(STOCK, f)
        self.paths.update(extra)
    def _lib(self, nick):
        if nick not in self.cache:
            e = parse(open(self.paths[nick]).read())
            self.cache[nick] = {x[1]: x for x in e if isinstance(x, list) and x and x[0] == "symbol"}
        return self.cache[nick]
    def flat(self, lib_id):
        nick, name = lib_id.split(":", 1)
        lib = self._lib(nick)
        s = copy.deepcopy(lib[name])
        ext = find(s, "extends")
        if ext:
            parent = self.flat(nick + ":" + ext[1])
            parent = copy.deepcopy(parent)
            pname = parent[1].split(":", 1)[1]
            # child properties override parent's
            cprops = {p[1]: p for p in findall(s, "property")}
            out = [Sym("symbol"), name]
            for item in parent[2:]:
                if isinstance(item, list) and item[0] == "property" and item[1] in cprops:
                    out.append(cprops.pop(item[1]))
                elif isinstance(item, list) and item[0] == "symbol":
                    item[1] = item[1].replace(pname, name, 1)
                    out.append(item)
                else:
                    out.append(item)
            # insert any remaining child props before first sub-symbol
            idx = next(i for i, x in enumerate(out) if isinstance(x, list) and x[0] == "symbol")
            for p in cprops.values():
                out.insert(idx, p); idx += 1
            s = out
        s[1] = lib_id
        return s
    def pins(self, lib_id):
        """returns {number: dict(name,x,y,ang,len,type,unit)} ; unit 0 = common"""
        s = self.flat(lib_id)
        res = {}
        base = lib_id.split(":", 1)[1]
        for sub in findall(s, "symbol"):
            m = re.match(r".*_(\d+)_(\d+)$", sub[1])
            unit, style = int(m.group(1)), int(m.group(2))
            if style > 1:
                continue
            for p in findall(sub, "pin"):
                at = find(p, "at")
                num = find(p, "number")[1]
                res.setdefault(num, []).append(dict(name=find(p, "name")[1], x=float(at[1]), y=float(at[2]),
                                                   ang=float(at[3]) if len(at) > 3 else 0.0,
                                                   len=float(find(p, "length")[1]), type=str(p[1]), unit=unit,
                                                   hidden=("hide" in [str(z) for z in p]) or bool(find(p, "hide"))))
        return res

# ---------------------------------------------------------------- geometry
def xform(px, py, X, Y, rot, mirror=None):
    """lib point (Y-up) -> schematic point for symbol at X,Y rot (deg, CCW on screen)."""
    x, y = px, -py
    if mirror == "y":
        x = -x
    elif mirror == "x":
        y = -y
    r = math.radians(rot)
    c, s = round(math.cos(r)), round(math.sin(r))
    xr = x * c + y * s
    yr = -x * s + y * c
    return (round(X + xr, 4), round(Y + yr, 4))

def outward(ang, rot, mirror=None):
    """unit vector (screen) pointing away from the symbol body for a pin with lib angle ang"""
    a = math.radians(ang)
    dx, dy = -round(math.cos(a)), -round(math.sin(a))   # lib, Y-up
    x, y = dx, -dy
    if mirror == "y":
        x = -x
    elif mirror == "x":
        y = -y
    r = math.radians(rot)
    c, s = round(math.cos(r)), round(math.sin(r))
    return (x * c + y * s, -x * s + y * c)

def dir_angle(d):
    return {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[(int(d[0]), int(d[1]))]

def eff(size=1.27, justify=None, hide=False, bold=False):
    f = [Sym("font"), [Sym("size"), size, size]]
    if bold:
        f.append([Sym("bold"), Sym("yes")])
    e = [Sym("effects"), f]
    if justify:
        e.append([Sym("justify")] + [Sym(j) for j in justify.split()])
    if hide:
        e.append([Sym("hide"), Sym("yes")])
    return e

# ---------------------------------------------------------------- sheet
class Sheet:
    counters = {"#PWR": 0, "#FLG": 0}
    def __init__(self, proj, name, title, page, paper="A3", root=False):
        self.proj, self.name, self.title, self.page, self.paper = proj, name, title, page, paper
        self.root = root
        self.uuid = U("sheetfile", name)
        self.items = []
        self.symbols = []
        self.used = {}
        self.wires = []      # (x1,y1,x2,y2)
        self.buses = []
        self.points = []     # connection points of pins/labels (for junction calc)
        self.refs = {}
        self.inst_path = None   # set by project
        self.hlabels = []    # (name, shape)
        self.comments = []
    # ---- symbols
    def sym(self, lib_id, ref, value, x, y, rot=0, mirror=None, unit=1, fp="", ds="", fields=None,
            dnp=False, ref_at=None, val_at=None, hide_val=False, in_bom=True, desc="", just=None, hide_ref=False, field_ang=None):
        L = self.proj.libs
        if lib_id not in self.used:
            self.used[lib_id] = L.flat(lib_id)
        pins = L.pins(lib_id)
        x, y = snap(x), snap(y)
        power = ref.startswith("#")
        s = dict(lib_id=lib_id, ref=ref, value=value, x=x, y=y, rot=rot, mirror=mirror, unit=unit, fp=fp, ds=ds,
                 fields=fields or {}, dnp=dnp, pins=pins, ref_at=ref_at, val_at=val_at, hide_val=hide_val,
                 in_bom=in_bom and not power, desc=desc, power=power, just=just, hide_ref=hide_ref)
        if just is None and not power and lib_id.split(":")[1] in ("R", "C", "C_Polarized", "L", "Fuse", "D_Schottky", "D_TVS", "D_Zener", "LED", "Crystal") :
            horiz = (rot in (90, 270)) != (lib_id.split(":")[1] in ("D_Schottky", "D_TVS", "D_Zener", "LED", "Crystal"))
            if horiz and ref_at is None:
                s["ref_at"] = (x, y - 2.54 if lib_id.split(":")[1] not in ("D_Schottky","D_TVS","D_Zener","LED","Crystal") else y - 3.81)
                s["val_at"] = (x, y + 2.54 if lib_id.split(":")[1] not in ("D_Schottky","D_TVS","D_Zener","LED","Crystal") else y + 3.81)
                s["just"] = "center"
        s["field_ang"] = field_ang if field_ang is not None else (90 if rot in (90, 270) else 0)
        self.symbols.append(s)
        return Part(self, s)
    def power(self, net, x, y, rot=0):
        lib = {"GND": "power:GND", "+5V": "power:+5V", "+3V3": "power:+3V3", "VIN": "power:+VDC",
               "PWR_FLAG": "power:PWR_FLAG"}[net]
        if net == "PWR_FLAG":
            Sheet.counters["#FLG"] += 1
            ref = "#FLG%02d" % Sheet.counters["#FLG"]
            val = "PWR_FLAG"
        else:
            Sheet.counters["#PWR"] += 1
            ref = "#PWR%03d" % Sheet.counters["#PWR"]
            val = net if net != "VIN" else "VIN"
        p = self.sym(lib, ref, val, x, y, rot)
        self.points.append((snap(x), snap(y)))
        return p
    # ---- primitives
    def wire(self, *pts):
        pts = [(snap(a), snap(b)) for a, b in pts]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            if (x1, y1) != (x2, y2):
                self.wires.append((x1, y1, x2, y2))
        return pts[-1]
    def bus(self, *pts):
        pts = [(snap(a), snap(b)) for a, b in pts]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            self.buses.append((x1, y1, x2, y2))
    def bus_entry(self, x, y, dx, dy):
        self.items.append([Sym("bus_entry"), [Sym("at"), snap(x), snap(y)], [Sym("size"), dx, dy],
                           [Sym("stroke"), [Sym("width"), 0], [Sym("type"), Sym("default")]],
                           [Sym("uuid"), U(self.name, "be", x, y)]])
    def label(self, name, x, y, ang=0, size=1.27):
        x, y = snap(x), snap(y)
        just = {0: "left bottom", 180: "right bottom", 90: "left bottom", 270: "right bottom"}[ang]
        self.items.append([Sym("label"), name, [Sym("at"), x, y, ang], eff(size, just),
                           [Sym("uuid"), U(self.name, "lbl", name, x, y)]])
        self.points.append((x, y))
    def hlabel(self, name, shape, x, y, ang=0):
        x, y = snap(x), snap(y)
        just = {0: "left", 180: "right", 90: "left", 270: "right"}[ang]
        self.items.append([Sym("hierarchical_label"), name, [Sym("shape"), Sym(shape)], [Sym("at"), x, y, ang],
                           eff(1.27, just), [Sym("uuid"), U(self.name, "hl", name, x, y)]])
        self.points.append((x, y))
        self.hlabels.append((name, shape))
    def nc(self, x, y):
        self.items.append([Sym("no_connect"), [Sym("at"), snap(x), snap(y)], [Sym("uuid"), U(self.name, "nc", x, y)]])
    def text(self, s, x, y, size=1.27, bold=False, ang=0):
        self.items.append([Sym("text"), s, [Sym("exclude_from_sim"), Sym("no")], [Sym("at"), snap(x, 0.635), snap(y, 0.635), ang],
                           eff(size, "left top", bold=bold), [Sym("uuid"), U(self.name, "txt", s[:40], x, y)]])
    def box(self, x1, y1, x2, y2, title=None):
        self.items.append([Sym("rectangle"), [Sym("start"), x1, y1], [Sym("end"), x2, y2],
                           [Sym("stroke"), [Sym("width"), 0], [Sym("type"), Sym("dash")]],
                           [Sym("fill"), [Sym("type"), Sym("none")]], [Sym("uuid"), U(self.name, "box", x1, y1)]])
        if title:
            self.text(title, x1 + 1.27, y1 + 1.27, 2.0, bold=True)
    # ---- split wires where a pin/label/power point lies on a wire interior
    def _split(self):
        cps = set(self.points)
        for sy in self.symbols:
            for num, lst in sy["pins"].items():
                for p in lst:
                    if p["unit"] in (0, sy["unit"]):
                        cps.add(xform(p["x"], p["y"], sy["x"], sy["y"], sy["rot"], sy["mirror"]))
        for x1, y1, x2, y2 in self.wires:
            cps.add((x1, y1)); cps.add((x2, y2))
        out = []
        for x1, y1, x2, y2 in self.wires:
            cuts = [(x1, y1), (x2, y2)]
            for (px, py) in cps:
                if x1 == x2 == px and min(y1, y2) < py < max(y1, y2):
                    cuts.append((px, py))
                elif y1 == y2 == py and min(x1, x2) < px < max(x1, x2):
                    cuts.append((px, py))
            cuts = sorted(set(cuts), key=lambda q: (q[0] - x1) ** 2 + (q[1] - y1) ** 2)
            for a, b in zip(cuts, cuts[1:]):
                out.append((a[0], a[1], b[0], b[1]))
        # dedupe
        seen = set(); res = []
        for w in out:
            k = tuple(sorted([(w[0], w[1]), (w[2], w[3])]))
            if k not in seen:
                seen.add(k); res.append(w)
        self.wires = res
    # ---- junction computation
    def _junctions(self):
        pts = {}
        def add(p, k=1):
            pts[p] = pts.get(p, 0) + k
        for x1, y1, x2, y2 in self.wires:
            add((x1, y1)); add((x2, y2))
        pinpts = set()
        for s in self.symbols:
            for num, lst in s["pins"].items():
                for p in lst:
                    if p["unit"] not in (0, s["unit"]):
                        continue
                    pinpts.add(xform(p["x"], p["y"], s["x"], s["y"], s["rot"], s["mirror"]))
        for p in pinpts:
            if p in pts:
                add(p)
        J = set()
        for p, n in pts.items():
            if n >= 3:
                J.add(p)
        # endpoint on interior of another wire
        for p in list(pts):
            for x1, y1, x2, y2 in self.wires:
                if (x1, y1) == p or (x2, y2) == p:
                    continue
                if x1 == x2 == p[0] and min(y1, y2) < p[1] < max(y1, y2):
                    J.add(p)
                elif y1 == y2 == p[1] and min(x1, x2) < p[0] < max(x1, x2):
                    J.add(p)
        return sorted(J)
    # ---- output
    def sexpr(self):
        P = self.proj
        e = [Sym("kicad_sch"), [Sym("version"), 20250114], [Sym("generator"), "eeschema"],
             [Sym("generator_version"), "9.0"], [Sym("uuid"), P.root_uuid if self.root else self.uuid],
             [Sym("paper"), self.paper]]
        tb = [Sym("title_block"), [Sym("title"), self.title], [Sym("date"), P.date], [Sym("rev"), P.rev],
              [Sym("company"), P.company]]
        for i, c in enumerate(self.comments[:9]):
            tb.append([Sym("comment"), i + 1, c])
        e.append(tb)
        ls = [Sym("lib_symbols")]
        for lid in sorted(self.used):
            ls.append(self.used[lid])
        e.append(ls)
        self._split()
        for (x, y) in self._junctions():
            e.append([Sym("junction"), [Sym("at"), x, y], [Sym("diameter"), 0], [Sym("color"), 0, 0, 0, 0],
                      [Sym("uuid"), U(self.name, "j", x, y)]])
        for it in self.items:
            if it[0] in ("no_connect",):
                e.append(it)
        for it in self.items:
            if it[0] == "bus_entry":
                e.append(it)
        for (x1, y1, x2, y2) in self.wires:
            e.append([Sym("wire"), [Sym("pts"), [Sym("xy"), x1, y1], [Sym("xy"), x2, y2]],
                      [Sym("stroke"), [Sym("width"), 0], [Sym("type"), Sym("default")]],
                      [Sym("uuid"), U(self.name, "w", x1, y1, x2, y2)]])
        for (x1, y1, x2, y2) in self.buses:
            e.append([Sym("bus"), [Sym("pts"), [Sym("xy"), x1, y1], [Sym("xy"), x2, y2]],
                      [Sym("stroke"), [Sym("width"), 0], [Sym("type"), Sym("default")]],
                      [Sym("uuid"), U(self.name, "b", x1, y1, x2, y2)]])
        for it in self.items:
            if it[0] not in ("no_connect", "bus_entry"):
                e.append(it)
        for s in self.symbols:
            e.append(self._sym_sexpr(s))
        for sh in getattr(self, "sheets", []):
            e.append(sh)
        if self.root:
            e.append([Sym("sheet_instances"), [Sym("path"), "/", [Sym("page"), "1"]]])
        e.append([Sym("embedded_fonts"), Sym("no")])
        return e
    def _sym_sexpr(self, s):
        x, y, rot = s["x"], s["y"], s["rot"]
        o = [Sym("symbol"), [Sym("lib_id"), s["lib_id"]], [Sym("at"), x, y, rot]]
        if s["mirror"]:
            o.append([Sym("mirror"), Sym(s["mirror"])])
        o += [[Sym("unit"), s["unit"]], [Sym("exclude_from_sim"), Sym("no")],
              [Sym("in_bom"), Sym("yes" if s["in_bom"] else "no")], [Sym("on_board"), Sym("yes")],
              [Sym("dnp"), Sym("yes" if s["dnp"] else "no")]]
        o.append([Sym("uuid"), U(self.name, "sym", s["ref"], s["unit"])])
        ra = s["ref_at"] or (x + 2.54, y - 1.27)
        va = s["val_at"] or (x + 2.54, y + 1.27)
        if s["power"]:
            ra = (x, y + 2.54)
            up = s["value"] != "GND"          # +5V/+3V3/VIN/PWR_FLAG point up at rot 0, GND points down
            d = {0: (0, -1), 90: (-1, 0), 180: (0, 1), 270: (1, 0)}[rot]
            if not up:
                d = (-d[0], -d[1])
            va = (x + d[0] * 5.08, y + d[1] * (6.35 if s["lib_id"] == "power:+VDC" else 3.81))
        rj = (s["just"] or "left") if not s["power"] else None
        if rj == "center": rj = None
        # KiCad composes field angle with symbol orientation; flip justification where it renders mirrored
        if not s["power"] and rj and ((rot == 90) or (rot == 180)):
            rj = {"left": "right", "right": "left"}.get(rj, rj)
        fa = s.get("field_ang", 0)
        o.append([Sym("property"), "Reference", s["ref"], [Sym("at"), snap(ra[0], .01), snap(ra[1], .01), fa], eff(1.27, rj, hide=s["power"] or s["hide_ref"])])
        vj = rj
        if s.get("val_just"):
            vj = s["val_just"]
            if rot in (90, 180):
                vj = {"left": "right", "right": "left"}.get(vj, vj)
        o.append([Sym("property"), "Value", s["value"], [Sym("at"), snap(va[0], .01), snap(va[1], .01), fa],
                  eff(1.27, vj, hide=s["hide_val"] or s["value"] == "PWR_FLAG" and False)])
        o.append([Sym("property"), "Footprint", s["fp"], [Sym("at"), x, y, 0], eff(1.27, hide=True)])
        o.append([Sym("property"), "Datasheet", s["ds"], [Sym("at"), x, y, 0], eff(1.27, hide=True)])
        o.append([Sym("property"), "Description", s["desc"], [Sym("at"), x, y, 0], eff(1.27, hide=True)])
        for k, v in s["fields"].items():
            o.append([Sym("property"), k, v, [Sym("at"), x, y, 0], eff(1.27, hide=True)])
        nums = set()
        for num, lst in s["pins"].items():
            for p in lst:
                if p["unit"] in (0, s["unit"]):
                    nums.add(num)
        for num in sorted(nums):
            o.append([Sym("pin"), num, [Sym("uuid"), U(self.name, "pin", s["ref"], s["unit"], num)]])
        path = self.inst_path
        o.append([Sym("instances"), [Sym("project"), PROJECT, [Sym("path"), path, [Sym("reference"), s["ref"]], [Sym("unit"), s["unit"]]]]])
        return o
    def write(self, d):
        fn = os.path.join(d, self.proj.root_name + ".kicad_sch" if self.root else self.name + ".kicad_sch")
        with open(fn, "w") as f:
            f.write(dump(self.sexpr()) + "\n")
        return fn

class Part:
    def __init__(self, sheet, s):
        self.sh, self.s = sheet, s
    def _find(self, num):
        s = self.s
        u = (0, s["unit"])
        byname = [p for lst in s["pins"].values() for p in lst if p["name"] == str(num) and p["unit"] in u]
        if byname:
            return byname[0]
        cand = [p for p in s["pins"].get(str(num), []) if p["unit"] in u]
        if not cand:
            raise KeyError("%s pin %s (unit %s)" % (s["ref"], num, s["unit"]))
        return cand[0]
    def pin(self, num):
        """(x,y) of connection point; name match (within unit) first, then pin number"""
        s = self.s
        p = self._find(num)
        return xform(p["x"], p["y"], s["x"], s["y"], s["rot"], s["mirror"])
    def pdir(self, num):
        s = self.s
        return outward(self._find(num)["ang"], s["rot"], s["mirror"])
    def allpins(self):
        s = self.s
        out = []
        for num, lst in s["pins"].items():
            for p in lst:
                if p["unit"] in (0, s["unit"]):
                    out.append((num, p))
        return out
    # convenience: stub + label / power / nc
    def to_label(self, num, net, length=2.54, hier=None):
        x, y = self.pin(num)
        dx, dy = self.pdir(num)
        ex, ey = x + dx * length, y + dy * length
        self.sh.wire((x, y), (ex, ey))
        if hier:
            self.sh.hlabel(net, hier, ex, ey, dir_angle((dx, dy)))
        else:
            self.sh.label(net, ex, ey, dir_angle((dx, dy)))
        return (ex, ey)
    def to_power(self, num, net, length=2.54):
        x, y = self.pin(num)
        dx, dy = self.pdir(num)
        ex, ey = x + dx * length, y + dy * length
        self.sh.wire((x, y), (ex, ey))
        rot = 0
        if net == "GND":
            rot = {(0, 1): 0, (0, -1): 180, (1, 0): 90, (-1, 0): 270}[(dx, dy)]
        else:
            rot = {(0, -1): 0, (0, 1): 180, (1, 0): 270, (-1, 0): 90}[(dx, dy)]
        self.sh.power(net, ex, ey, rot)
        return (ex, ey)
    def to_nc(self, num):
        x, y = self.pin(num)
        self.sh.nc(x, y)
    def stub(self, num, length=2.54):
        x, y = self.pin(num)
        dx, dy = self.pdir(num)
        return self.sh.wire((x, y), (x + dx * length, y + dy * length))
