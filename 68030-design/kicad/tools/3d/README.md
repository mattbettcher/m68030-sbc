# 3D model tools

- `list.py` lists every footprint with its model paths and whether each path resolves (writes `fps.json`, which is not tracked).
- `dump_pads.py` writes `pads.json` (footprint-local pad positions) for the generated footprints.
- `gen.py` (cadquery 2.8) builds the STEP models in `kicad/3dmodels/m68030-sbc.3dshapes/` from `pads.json`.
- `setmodels.py SRC DST` rewrites only the `(model ...)` blocks of U1-U6, J1, F1 and L1 to `${KIPRJMOD}/3dmodels/m68030-sbc.3dshapes/...`.
