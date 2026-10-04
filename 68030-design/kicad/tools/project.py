import os, json, sys
sys.path.insert(0, os.path.dirname(__file__))
from kgen import *

class Project:
    def __init__(self, outdir, root_name=PROJECT, date="2026-09-26", rev="A (draft)", company="Matthew Bettcher — 68030 Linux SBC"):
        self.outdir = outdir
        self.root_name = root_name
        self.date, self.rev, self.company = date, rev, company
        self.libs = Libs({"m68030-sbc": os.path.join(outdir, "lib", "m68030-sbc.kicad_sym")})
        self.root_uuid = U("root")
        self.root = Sheet(self, "root", "68030 Linux SBC — top level", 1, "A2", root=True)
        self.root.inst_path = "/" + self.root_uuid
        self.root.sheets = []
        self.subs = []
    def sub(self, name, title, page, paper="A3"):
        s = Sheet(self, name, title, page, paper)
        s.inst_path = "/%s/%s" % (self.root_uuid, U("sheetsym", name))
        self.subs.append(s)
        return s
    def place_sheet(self, sh, x, y, w, pins_left, pins_right, label_nets=True):
        """pins_*: list of (name, shape) or None(spacer)"""
        n = max(len(pins_left), len(pins_right))
        h = snap((n + 2) * 2.54, 2.54)
        su = U("sheetsym", sh.name)
        o = [Sym("sheet"), [Sym("at"), x, y], [Sym("size"), w, h], [Sym("exclude_from_sim"), Sym("no")],
             [Sym("in_bom"), Sym("yes")], [Sym("on_board"), Sym("yes")], [Sym("dnp"), Sym("no")],
             [Sym("fields_autoplaced"), Sym("yes")],
             [Sym("stroke"), [Sym("width"), 0.1524], [Sym("type"), Sym("solid")]],
             [Sym("fill"), [Sym("color"), 255, 255, 225, 1.0]], [Sym("uuid"), su],
             [Sym("property"), "Sheetname", sh.name, [Sym("at"), x, y - 0.7116, 0], eff(1.27, "left bottom", bold=True)],
             [Sym("property"), "Sheetfile", sh.name + ".kicad_sch", [Sym("at"), x, y + h + 0.5846, 0], eff(1.27, "left top")]]
        R = self.root
        for side, pins in (("L", pins_left), ("R", pins_right)):
            for i, p in enumerate(pins):
                if not p:
                    continue
                name, shape = p
                py = y + 2.54 * (i + 1)
                if side == "L":
                    px, ang, just, d = x, 180, "left", -1
                else:
                    px, ang, just, d = x + w, 0, "right", 1
                o.append([Sym("pin"), name, Sym(shape), [Sym("at"), px, py, ang], [Sym("uuid"), U("sheetpin", sh.name, name)],
                          eff(1.27, just)])
                if label_nets:
                    ex = px + d * 5.08
                    if "[" in name:
                        R.bus((px, py), (ex, py))
                    else:
                        R.wire((px, py), (ex, py))
                    R.label(name, ex, py, 0 if d > 0 else 180)
        o.append([Sym("instances"), [Sym("project"), PROJECT, [Sym("path"), "/" + self.root_uuid, [Sym("page"), str(sh.page)]]]])
        R.sheets.append(o)
        return h
    def write(self):
        d = self.outdir
        os.makedirs(d, exist_ok=True)
        files = [self.root.write(d)]
        for s in self.subs:
            files.append(s.write(d))
        with open(os.path.join(d, "sym-lib-table"), "w") as f:
            f.write('(sym_lib_table\n\t(version 7)\n\t(lib (name "m68030-sbc")(type "KiCad")(uri "${KIPRJMOD}/lib/m68030-sbc.kicad_sym")(options "")(descr "Project-local symbols (MC68030, MC68882, LM2678)"))\n)\n')
        with open(os.path.join(d, "fp-lib-table"), "w") as f:
            f.write('(fp_lib_table\n\t(version 7)\n\t(lib (name "m68030-sbc")(type "KiCad")(uri "${KIPRJMOD}/lib/m68030-sbc.pretty")(options "")(descr "Project-local footprints (PGA-128 and SIMM-72 derived from Mackerel-68k, MIT)"))\n)\n')
        pro = json.load(open("/usr/share/kicad/template/kicad.kicad_pro"))
        pro["meta"]["filename"] = self.root_name + ".kicad_pro"
        pro.setdefault("sheets", [])
        pro["sheets"] = [[self.root_uuid, "Root"]] + [[U("sheetsym", s.name), s.name] for s in self.subs]
        pro.setdefault("schematic", {})
        pro["schematic"].setdefault("annotation", {})["method"] = 1
        pro["schematic"]["annotation"]["sort_order"] = 0
        pro["schematic"]["annotation"]["numbering"] = 1
        with open(os.path.join(d, self.root_name + ".kicad_pro"), "w") as f:
            json.dump(pro, f, indent=2)
        return files
