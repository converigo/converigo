# Phase 1 - legacy .xls fixture provenance

Generated: 2026-09-15T22:08:37
Baseline for which these were prepared: `a9323410d20d1029ca32b71e6b301bc03b2e7f95`

## Toolchain (documented, reproducible)

| Item | Value |
|---|---|
| Author host | Windows 10 AMD64 |
| Author interpreter | CPython 3.11.9 |
| BIFF8 writer | `xlwt==1.3.0` (pure-Python OLE2/CFBF + BIFF8 writer) |
| Independent reader used for validation | `xlrd==2.0.2` (mature BIFF8 reader) |
| Container validator | `validate_fixtures.py` - hand-written [MS-CFB] parser: header -> DIFAT -> FAT -> directory chain -> `Workbook` stream -> BIFF `BOF` record walk |
| Install location | `pip install --target .tmp/xls_prep/tools` - the repo virtualenv and `requirements.txt` were **not** modified |

LibreOffice was **not** available on the author host, so the fixtures were authored with a
BIFF writer instead of a LibreOffice round-trip. Every fixture is verified at the container level (real OLE2 compound file whose `Workbook` stream begins with a BIFF8 `BOF`, `version=0x0600`) **and** re-opened by an independent BIFF reader (`xlrd`). None of the legacy fixtures is a renamed ZIP: the OLE2 signature is present and the `PK\x03\x04` signature is absent (the `masquerade_*` file is intentionally the opposite).

LibreOffice reading these fixtures is asserted by Phase 2's spike (T1), which cannot run on this host - see `spike/README.md`.

## Commands

```bash
cd .tmp/xls_prep
python -m pip install --disable-pip-version-check --target tools xlwt==1.3.0 xlrd==2.0.2
PYTHONPATH=tools python make_fixtures.py     # deterministic, ~20 s
PYTHONPATH=tools python validate_fixtures.py # prints container + reader evidence
```

`make_fixtures.py` is byte-deterministic: a delete-and-regenerate cycle reproduced every SHA-256 below.

## Inventory

| File | Bytes | Container | BIFF | SHA-256 |
|---|---:|---|---|---|
| `corrupt_garbage_biff8.xls` | 34,304 | OLE2/CFBF | ? | `73d9a3361f4db3f1cc9333eaf33ff147b80ccccefa1ac337accaa884f4850444` |
| `corrupt_truncated_biff8.xls` | 18,867 | OLE2/CFBF | BIFF8 (header only) | `aa8264df9b0a38d969d243418525bf564696f14fb7b46f0d7f3b7ab8bf519b6a` |
| `masquerade_xlsx_named_xls.xls` | 4,838 | ZIP/OOXML | - | `eae389a26ca87f5aa4c2069acc0f90d735e7f913a847dffa478d8add143f9df3` |
| `sample_legacy_biff8.xls` | 34,304 | OLE2/CFBF | BIFF8 | `65e0bc2eb2dbeed6343a11d131f926b9dd09142e33190e4b9bcd2a3cd8fa4e1d` |
| `stress_biff8_120kc.xls` | 2,680,320 | OLE2/CFBF | BIFF8 | `9d263b8108fd4db3afbc7b9439cd5fb501d1f609e575fc4c84ab8bdea4fad41d` |
| `stress_biff8_bulk1m.xls` | 21,836,800 | OLE2/CFBF | BIFF8 | `d6a7162a2cf8de41a387055dfad971b0a93961985066dd90104f3cfa784612d5` |

## Intent per fixture

- `corrupt_garbage_biff8.xls` - valid OLE2 magic + intact header, every sector after it XOR-scrambled
- `corrupt_truncated_biff8.xls` - valid OLE2 magic, file cut at 55% -> FAT/stream chain incomplete
- `masquerade_xlsx_named_xls.xls` - NOT legacy: genuine OOXML (tests/assets/regression/sample.xlsx) wearing a .xls name; must stay refused by name gate
- `sample_legacy_biff8.xls` - multi-sheet (Ledger/Summary/Formats/Emptyish), 120 data rows, strings/int/decimal/date/formula/number-formats/merged cells
- `stress_biff8_120kc.xls` - mid stress probe: 2 sheets x 5000 x 12 = 120,000 cells, 20,000 formulas
- `stress_biff8_bulk1m.xls` - bulk resource probe: 1 sheet x 50,000 x 20 = 1,000,020 cells, no formulas

## Intended repository destination (implementation gate only)

```
tests/assets/regression/sample_legacy_biff8.xls
tests/assets/regression/stress_biff8_120kc.xls
tests/assets/regression/stress_biff8_bulk1m.xls
tests/assets/regression/corrupt_truncated_biff8.xls
tests/assets/regression/corrupt_garbage_biff8.xls
tests/assets/regression/masquerade_xlsx_named_xls.xls
```

`git check-ignore tests/assets/regression/sample_legacy.xls` exits 1, i.e. binary `.xls`
fixtures are **not** gitignored, so they can be committed as-is.
Suggested committed set for the enablement suite: the sample + the two corrupt variants +
the mid stress tier. The 21.8 MB bulk tier is a spike/CI probe and should stay out of
the repository unless CI needs it.
