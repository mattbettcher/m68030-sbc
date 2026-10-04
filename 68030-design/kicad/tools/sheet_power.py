from build_common import *

def hang(sh, lib, ref, val, x, rail_y, fp, rot=0, bot="GND", pin_top=1, pin_bot=2, **kw):
    """vertical 2-pin part hanging below a horizontal rail at rail_y (top pin 2.54 below rail)"""
    p = sh.sym(lib, ref, val, x, rail_y + 6.35, rot, fp=fp, **kw)
    t = p.pin(pin_top)
    sh.wire(t, (x, rail_y))
    if bot:
        b = p.pin(pin_bot)
        sh.power(bot, b[0], b[1], 0)
    return p

def build_power(P):
    sh = P.sub("power", "Power: 9-24 V input, LM2678-5.0 buck, 3.3 V LDO", 2)
    sh.comments = ["LM2678 values: TI SNVS029L sect. 7.2.1.2, Vin(max) 24 V, Iload 4 A (spec 6.2)",
                   "Input: fuse -> P-FET reverse-polarity switch -> TVS on VIN",
                   "Load budget and rail list: spec.md sect. 6.1"]
    RY = 76.2
    sh.text("Input: 9-24 V DC barrel jack (centre +), T5A fuse, P-FET reverse-polarity protection, TVS", 25.4, 50.8, 1.5, bold=True)
    j2 = sh.sym("Connector:Barrel_Jack_Switch", "J2", "9-24V DC", 27.94, 78.74, fp="Connector_BarrelJack:BarrelJack_Horizontal",
                ref_at=(22.86, 71.12), val_at=(22.86, 86.36), fields={"Note": "centre positive, 2.1 or 2.5 mm per chosen jack [VERIFY footprint]"})
    p1, p2, p3 = j2.pin(1), j2.pin(2), j2.pin(3)
    sh.wire(p3, (38.1, p3[1])); sh.wire(p2, (38.1, p2[1])); sh.wire((38.1, p3[1]), (38.1, 86.36))
    sh.power("GND", 38.1, 86.36, 0)
    sh.wire((38.1, 86.36), (45.72, 86.36)); sh.power("PWR_FLAG", 45.72, 86.36, 180)
    f1 = sh.sym("Device:Fuse", "F1", "T5A 5x20", 53.34, RY, 90, fp="Fuse:Fuseholder_Cylinder-5x20mm_Schurter_0031_8201_Horizontal_Open",
                fields={"MPN": "5x20 mm time-lag 5 A glass fuse + Schurter 0031.8201 holder"})
    sh.wire(p1, f1.pin(1))
    q1 = sh.sym("Transistor_FET:SUD50P04-08", "Q1", "SUD50P04-08", 73.66, 78.74, 90, fp="Package_TO_SOT_SMD:TO-252-2",
                ds="https://www.vishay.com/docs/72130/sud50p04-08.pdf", fields={"MPN": "SUD50P04-08-GE3"},
                ref_at=(68.58, 68.58), val_at=(68.58, 71.12))
    sh.wire(f1.pin(2), q1.pin("D"))
    g = q1.pin("G")
    r201 = sh.sym("Device:R", "R201", "10k", 73.66, 93.98, 0, fp=R0603)
    sh.wire(g, r201.pin(1))
    sh.power("GND", *r201.pin(2), 0)
    d3 = sh.sym("Device:D_Zener", "D3", "MMSZ5242B", 83.82, 83.82, 270, fp="Diode_SMD:D_SOD-123",
                fields={"MPN": "MMSZ5242B (12 V)"}, ref_at=(86.36, 82.55), val_at=(86.36, 85.09))
    k, a = d3.pin("K"), d3.pin("A")
    sh.wire(k, (k[0], RY))
    sh.wire(a, (a[0], 88.9), (73.66, 88.9))
    s = q1.pin("S")
    # VIN rail
    sh.wire(s, (193.04, RY))
    sh.power("VIN", 99.06, RY, 0)
    sh.power("PWR_FLAG", 106.68, RY, 0)
    hang(sh, "Device:D_TVS", "D2", "SMBJ28CA", 116.84, RY, "Diode_SMD:D_SMB", rot=90, pin_top=2, pin_bot=1,
         fields={"MPN": "SMBJ28CA (28 V standoff, bidirectional)"}, ref_at=(119.38, 81.28), val_at=(119.38, 83.82))
    sh.sym("Connector:TestPoint", "TP201", "VIN", 127.0, RY, 0, fp=TP, ref_at=(129.03, 69.85), val_at=(129.03, 72.39))
    for i, (ref, val, lib, fp, mpn) in enumerate([("C201", "10u", "Device:C", C1210, "10 uF 50 V X7R 1210"),
                                                  ("C202", "10u", "Device:C", C1210, "10 uF 50 V X7R 1210"),
                                                  ("C203", "10u", "Device:C", C1210, "10 uF 50 V X7R 1210"),
                                                  ("C204", "100u", "Device:C_Polarized", "Capacitor_SMD:CP_Elec_10x10.5", "100 uF 50 V low-ESR aluminium, 10x10.5")]):
        x = 137.16 + i * 10.16
        hang(sh, lib, ref, val, x, RY, fp, fields={"Rating": mpn}, ref_at=(x + 2.54, 81.28), val_at=(x + 2.54, 83.82))
    sh.text("C201-C203: 50 V X7R 1210\nC204: 50 V electrolytic", 137.16, 93.98, 1.0)
    sh.text("Q1: body diode conducts first, then Vgs = -(VIN) turns the channel on;\nreversed input leaves Q1 off. D3 clamps |Vgs| to 12 V (Q1 Vgs max +/-20 V).\n"
            "D2 SMBJ28CA: bidirectional TVS, 28 V standoff; clamp at rated Ipp (~45 V)\nis at the LM2678 45 V abs-max [EST] - fuse F1 clears sustained faults.",
            25.4, 111.76, 1.27)
    sh.text("C201-C204: Irms rating must exceed Iload/2 = 2 A (SNVS029L step 5).\nDeviation from Table 7-7 (tantalum/aluminium): 3x 10 uF 50 V X7R 1210 +\n1x 100 uF 50 V low-ESR electrolytic for bulk/damping on hot-plug.",
            25.4, 129.54, 1.27)
    # ---------------- buck
    sh.text("5 V buck: LM2678S-5.0 (fixed 5 V, 260 kHz, 5 A switch)", 190.5, 50.8, 1.5, bold=True)
    u8 = sh.sym("m68030-sbc:LM2678S-5.0", "U8", "LM2678S-5.0", 203.2, 78.74, fp="Package_TO_SOT_SMD:TO-263-7_TabPin4",
                ds="https://www.ti.com/lit/ds/symlink/lm2678.pdf", fields={"MPN": "LM2678S-5.0/NOPB"},
                ref_at=(198.12, 67.31), val_at=(198.12, 69.85))
    sh.power("GND", *u8.pin("4"), 0)
    on = u8.pin("7")
    sj = sh.sym("Jumper:SolderJumper_2_Open", "SJ201", "DISABLE", 187.96, 86.36, 90, fp="Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
                ref_at=(176.53, 85.09), val_at=(176.53, 87.63))
    sh.wire(on, (187.96, on[1]), sj.pin("B"))
    sh.power("GND", *sj.pin("A"), 0)
    cb, vsw, fb = u8.pin("3"), u8.pin("1"), u8.pin("6")
    NX = 228.6
    c205 = sh.sym("Device:C", "C205", "10n", 220.98, 68.58, 90, fp=C0603)
    sh.wire(cb, (215.9, cb[1]), (215.9, 68.58), c205.pin(1))
    sh.wire(c205.pin(2), (NX, 68.58), (NX, vsw[1]))
    sh.wire(vsw, (NX, vsw[1]))
    d1 = sh.sym("Device:D_Schottky", "D1", "B540C", NX, 86.36, 270, fp="Diode_SMD:D_SMC", fields={"MPN": "B540C-13-F"},
                ref_at=(231.14, 85.09), val_at=(231.14, 87.63))
    sh.wire(d1.pin("K"), (NX, vsw[1]))
    sh.power("GND", *d1.pin("A"), 0)
    l1 = sh.sym("Device:L", "L1", "22uH", 243.84, vsw[1], 90, fp="Inductor_SMD:L_Bourns_SRP1770TA_16.9x16.9mm",
                fields={"MPN": "Bourns SRP1770TA-220M"})
    sh.wire((NX, vsw[1]), l1.pin(1))
    OY = vsw[1]
    sh.wire(l1.pin(2), (304.8, OY))
    sh.label("VBUCK", 254.0, OY, 0)
    sh.wire(fb, (220.98, fb[1])); sh.label("VBUCK", 220.98, fb[1], 0)
    for i, ref in enumerate(["C206", "C207", "C208"]):
        x = 266.7 + i * 10.16
        hang(sh, "Device:C_Polarized", ref, "100u", x, OY, "Capacitor_Tantalum_SMD:CP_EIA-7343-43_Kemet-X",
             fields={"MPN": "KEMET T495X107K010ATE100 [VERIFY]", "Rating": "100 uF 10 V tantalum"}, ref_at=(x + 2.54, 83.82), val_at=(x + 2.54, 86.36))
    sh.text("C206-C208: 100 uF 10 V\ntantalum (T495-X)", 264.16, 96.52, 1.0)
    jp202 = sh.sym("Jumper:SolderJumper_2_Bridged", "JP202", "ISOLATE", 309.88, OY, 0, fp="Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm",
                   ref_at=(309.88, OY - 5.08), val_at=(309.88, OY + 3.81), just="center")
    sh.wire((304.8, OY), jp202.pin("A"))
    sh.wire(jp202.pin("B"), (370.84, OY))
    sh.power("+5V", 321.31, OY, 0)
    sh.power("PWR_FLAG", 330.2, OY, 0)
    sh.sym("Connector:TestPoint", "TP202", "+5V", 340.36, OY, 0, fp=TP, ref_at=(342.39, OY - 7.62), val_at=(342.39, OY - 5.08))
    r202 = hang(sh, "Device:R", "R202", "1k", 353.06, OY, R0603, bot=None)
    d4 = sh.sym("Device:LED", "D4", "PWR", 353.06, 96.52, 90, fp=LED0805, ref_at=(355.6, 95.25), val_at=(355.6, 97.79),
                fields={"Colour": "green"})
    sh.wire(r202.pin(2), d4.pin("A"))
    sh.power("GND", *d4.pin("K"), 0)
    j3 = sh.sym("Connector_Generic:Conn_01x02", "J3", "5V_BENCH", 375.92, OY, 0, fp=HDR2, dnp=True, ref_at=(378.46, OY), val_at=(378.46, OY + 2.54))
    sh.wire(j3.pin(1), (370.84, OY))
    p2 = j3.pin(2); sh.wire(p2, (368.3, p2[1]), (368.3, p2[1] + 5.08)); sh.power("GND", 368.3, p2[1] + 5.08, 0)
    sh.text("L1: Fig 7-3 nomograph (5 V, 24 V, 4 A) -> L41 = 22 uH; SRP1770TA-220M: DCR 26.5 mOhm, Isat 18 A.\n"
            "C206-C208: Table 7-5 -> 3x AVX/KEMET 100 uF 10 V 'C4' tantalum (no all-ceramic output).\n"
            "D1: Schottky, VR >= 1.3 x 24 V, IF >= 5 A (Table 7-4 class) -> B540C (40 V, 5 A).\n"
            "C205 (CB): 0.01 uF per step 7 / sect. 7.1.6 (pin table says 100 nF - see NOTES.md).\n"
            "Output: 4.85-5.15 V over line/load/temp (SNVS029L electrical table).\n"
            "SJ201: ON/OFF (pin 7) left open = enabled (abs max 6 V, never tie to VIN); bridge to disable.\n"
            "JP202: cut to isolate the buck and feed +5V from J3 (bench supply). J3 DNP.",
            190.5, 111.76, 1.27)
    # ---------------- 3.3 V
    sh.text("3.3 V LDO for DS3234 RTC / ENC28J60 / logic-level parts (spec 6.1)", 25.4, 147.32, 1.5, bold=True)
    LY = 165.1
    u9 = sh.sym("Regulator_Linear:AMS1117-3.3", "U9", "AMS1117-3.3", 91.44, LY, 0, fp="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
                ds="http://www.advanced-monolithic.com/pdf/ds1117.pdf", fields={"MPN": "AMS1117-3.3"}, ref_at=(88.9, LY - 7.62), val_at=(88.9, LY - 5.08))
    sh.power("GND", *u9.pin("1"), 0)
    sh.wire((71.12, LY), u9.pin("3")); sh.power("+5V", 71.12, LY, 0)
    hang(sh, "Device:C", "C209", "10u", 76.2, LY, C1206)
    sh.wire(u9.pin("2"), (116.84, LY))
    hang(sh, "Device:C_Polarized", "C210", "22u 10V tant", 104.14, LY, "Capacitor_Tantalum_SMD:CP_EIA-3528-21_Kemet-B",
         ref_at=(105.41, LY + 3.81), val_at=(105.41, LY + 8.89))
    sh.power("+3V3", 111.76, LY, 0)
    sh.sym("Connector:TestPoint", "TP203", "+3V3", 116.84, LY, 0, fp=TP, ref_at=(118.87, LY - 7.62), val_at=(118.87, LY - 5.08))
    tp4 = sh.sym("Connector:TestPoint", "TP204", "GND", 127.0, LY - 2.54, 0, fp=TP, ref_at=(129.03, LY - 10.16), val_at=(129.03, LY - 7.62))
    sh.wire((127.0, LY - 2.54), (127.0, LY)); sh.power("GND", 127.0, LY, 0)
    sh.text("C210: AMS1117 datasheet 'Stability': 22 uF solid tantalum on the output covers all conditions.\\nC209: 10 uF input per the datasheet application circuit.",
            25.4, 187.96, 1.27)
    sh.text("Mounting holes H1-H4 (GND) are on the top-level sheet.", 25.4, 198.12, 1.27)
    return sh
