from build_common import *

def build_reset(P):
    sh = P.sub("reset", "Reset", 4)
    sh.comments = ['TPS3702CX50 (SBVS251A Tbl 10-2) window + TPS3808G50 (SBVS050N) delay', 'RESET_n / HALT_n are open-drain nets; 1k pull-ups here (spec 8.1)', 'PWR_RST_n -> U3 pin 1 and U4 pin 1 (GCLR); spec 7.2']
    sh.text("Power-on / brown-out supervisor", 30.48, 50.8, 1.5, bold=True)
    u7 = sh.sym("m68030-sbc:TPS3702CX50", "U7", "TPS3702CX50DDCR", 88.9, 88.9, fp="Package_TO_SOT_SMD:SOT-23-6",
                ds="https://www.ti.com/lit/ds/symlink/tps3702.pdf", fields={"MPN": "TPS3702CX50DDCR"},
                ref_at=(91.44, 78.74), val_at=(91.44, 101.6))
    u7.to_power("5", "+5V"); u7.to_power("2", "GND")
    s = u7.pin("3"); sh.wire(s, (s[0] - 12.7, s[1])); sh.power("+5V", s[0] - 12.7, s[1], 90)
    st = u7.pin("4"); sh.wire(st, (st[0] - 7.62, st[1]))
    jp = sh.sym("Jumper:SolderJumper_3_Bridged12", "JP401", "SET", st[0] - 7.62, st[1] + 7.62, 180,
                fp="Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm", ref_at=(st[0] - 7.62, st[1] + 11.43), val_at=(st[0] - 7.62, st[1] + 13.97), just="center")
    cpin = jp.pin("2"); sh.wire((st[0] - 7.62, st[1]), cpin)
    ap = jp.pin("1"); sh.wire(ap, (ap[0] + 2.54, ap[1])); sh.power("+5V", ap[0] + 2.54, ap[1], 270)
    bp = jp.pin("3"); sh.wire(bp, (bp[0], bp[1] + 2.54)); sh.power("GND", bp[0], bp[1] + 2.54, 0)
    sh.text("JP401 (A-C bridged) = SET high: +/-4 % window.\\nCut A-C, bridge B-C = SET low: +/-9 % (UV 4.55 V) fallback.", 50.8, 111.76, 1.0)
    uv, ov = u7.pin("1"), u7.pin("6")
    jx = uv[0] + 5.08
    sh.wire(uv, (jx, uv[1])); sh.wire(ov, (jx, ov[1])); sh.wire((jx, ov[1]), (jx, uv[1]))
    u27 = sh.sym("Power_Supervisor:TPS3808DBV", "U27", "TPS3808G50DBVR", 144.78, 88.9, fp="Package_TO_SOT_SMD:SOT-23-6",
                 ds="https://www.ti.com/lit/ds/symlink/tps3808.pdf", fields={"MPN": "TPS3808G50DBVR"},
                 ref_at=(147.32, 78.74), val_at=(147.32, 101.6))
    u27.to_power("6", "+5V"); u27.to_power("2", "GND")
    mr = u27.pin("3")
    sh.wire((jx, uv[1]), mr)
    sh.label("SUP_MR_n", 121.92, uv[1], 0)
    sp = u27.pin("5"); sh.wire(sp, (sp[0] - 2.54, sp[1])); sh.wire((sp[0] - 2.54, sp[1]), (sp[0] - 2.54, sp[1] - 5.08))
    sh.power("+5V", sp[0] - 2.54, sp[1] - 5.08, 0)
    ct = u27.pin("4")
    r402 = R(sh, "R402", "100k", ct[0] - 2.54, ct[1] + 7.62, 0)
    sh.wire(ct, (ct[0] - 2.54, ct[1])); sh.wire((ct[0] - 2.54, ct[1]), r402.pin(1))
    b = r402.pin(2); sh.wire(b, (b[0], b[1] + 2.54)); sh.power("+5V", b[0], b[1] + 2.54, 180)
    # MR pull-up + SW3
    r401 = R(sh, "R401", "10k", 106.68, 78.74, 0)
    sh.wire(r401.pin(2), (106.68, uv[1])); sh.power("+5V", 106.68, r401.pin(1)[1], 0)
    sw3 = sh.sym("Switch:SW_Push", "SW3", "COLD_RESET", 119.38, 99.06, 90, fp=SW6, ref_at=(116.84, 97.79), val_at=(116.84, 100.33), just="right")
    sh.wire(sw3.pin("2"), (119.38, uv[1]))
    g = sw3.pin("1"); sh.power("GND", g[0], g[1], 0)
    # RESET output
    ro = u27.pin("1")
    sh.wire(ro, (ro[0] + 22.86, ro[1])); sh.hlabel("PWR_RST_n", "output", ro[0] + 22.86, ro[1], 0)
    r403 = R(sh, "R403", "10k", ro[0] + 7.62, ro[1] - 10.16, 0)
    sh.wire(r403.pin(2), (ro[0] + 7.62, ro[1])); sh.power("+5V", ro[0] + 7.62, r403.pin(1)[1], 0)
    cap_row(sh, [("C401", "100n", C0603), ("C402", "100n", C0603)], 88.9, 134.62, 12.7)
    sh.text("C401: U7 VDD, C402: U27 VDD (place at the pins)", 83.82, 119.38, 1.0)
    sh.text("Operation: U7 compares +5V against a 4.757-4.843 V (UV) / 5.153-5.247 V (OV) window; its open-drain\\n"
            "outputs, SW3 and R401 form SUP_MR_n into U27 MR. U27 holds PWR_RST_n low while MR is low or +5V < 4.65 V,\\n"
            "then releases it ~300 ms later (CT = 100k to VDD). LM2678-5.0 output: 4.85-5.15 V (TI SNVS029L).",
            30.48, 152.4, 1.27)
    # ---------------- buttons
    sh.text("Buttons (debounced in the glue CPLD, spec 3.5 / 7.2)", 223.52, 50.8, 1.5, bold=True)
    for i, (rref, swref, net, val) in enumerate([("R404", "SW1", "WARM_RST_BTN_n", "WARM_RESET"), ("R405", "SW2", "NMI_BTN_n", "NMI")]):
        x = 233.68 + i * 45.72
        r = R(sh, rref, "10k", x, 71.12, 0)
        sh.power("+5V", x, r.pin(1)[1], 0)
        node = (x, 81.28)
        sh.wire(r.pin(2), node)
        sh.wire(node, (x + 20.32, node[1])); sh.hlabel(net, "output", x + 20.32, node[1], 0)
        sw = sh.sym("Switch:SW_Push", swref, val, x, 91.44, 90, fp=SW6, ref_at=(x + 2.54, 90.17), val_at=(x + 2.54, 92.71))
        sh.wire(sw.pin("2"), node)
        g = sw.pin("1"); sh.power("GND", g[0], g[1], 0)
    # ---------------- RESET/HALT pull-ups
    sh.text("CPU RESET_n / HALT_n open-drain pull-ups (spec 8.1)", 223.52, 116.84, 1.5, bold=True)
    for i, (rref, net) in enumerate([("R406", "RESET_n"), ("R407", "HALT_n")]):
        x = 233.68 + i * 45.72
        r = R(sh, rref, "1k", x, 134.62, 0)
        sh.power("+5V", x, r.pin(1)[1], 0)
        node = (x, 144.78)
        sh.wire(r.pin(2), node)
        sh.wire(node, (x + 20.32, node[1])); sh.hlabel(net, "bidirectional", x + 20.32, node[1], 0)
    sh.text("RESET_n: driven by U3 (power-on / warm reset), by the CPU RESET instruction, read by U3;\\nalso FPU RESET and LA3. HALT_n: 68030 input only, driven by U3 with RESET.\\n1k gives ~5 mA sink at 5 V (CPU IOL 10.7 mA, EC).",
            223.52, 157.48, 1.27)
    return sh
