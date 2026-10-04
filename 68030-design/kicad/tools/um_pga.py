# MC68030 PGA-128 (RC suffix) pin assignment, transcribed from MC68030UM §14.2 figure (page 14-2, bottom view)
rows = {
'N':"D31 D28 D26 D25 D23 D21 D19 D18 D16 D15 D13 D11 D8",
'M':"DBEN ECS D29 D27 D24 D22 D20 D17 D14 D12 D9 D6 D3",
'L':"CIIN SIZ0 R/W D30 GND VCC GND GND GND D10 D7 D4 D2",
'C':"FC1 CIOUT BGACK A1 GND VCC GND A18 GND A11 A9 A5 A4",
'B':"RMC BG A31 A29 A27 A25 A22 A20 A16 A14 A12 A8 A7",
'A':"BR A0 A30 A28 A26 A24 A23 A21 A19 A17 A15 A13 A10",
}
partial = {
'K':{1:'CBREQ',2:'DS',3:'SIZ1',4:'VCC',5:'NC',10:'VCC',11:'D5',12:'D1',13:'D0'},
'J':{1:'CBACK',2:'AS',3:'GND',11:'GND',12:'STATUS',13:'REFILL'},
'H':{1:'BERR',2:'HALT',3:'VCC',11:'VCC',12:'CDIS',13:'IPL0'},
'G':{1:'STERM',2:'DSACK1',3:'GND',11:'GND',12:'IPL2',13:'IPL1'},
'F':{1:'DSACK0',2:'VCC',3:'GND',4:'NC',10:'NC',11:'VCC',12:'RESET',13:'MMUDIS'},
'E':{1:'CLK',2:'AVEC',3:'GND',11:'GND',12:'NC',13:'IPEND'},
'D':{1:'FC2',2:'FC0',3:'OCS',4:'VCC',5:'NC',10:'VCC',11:'A6',12:'A3',13:'A2'},
}
PGA={}
for r,s in rows.items():
    for i,n in enumerate(s.split()): PGA[f"{r}{i+1}"]=n
for r,d in partial.items():
    for c,n in d.items(): PGA[f"{r}{c}"]=n
assert len(PGA)==128, len(PGA)
