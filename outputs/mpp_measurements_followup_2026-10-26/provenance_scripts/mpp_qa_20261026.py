from pathlib import Path
original=Path(r'C:\Users\Admin\AppData\Local\Temp\btl_mpp_draft_20261025_v1\qa.py')
source=original.read_text()
source=source.replace("OUT=ROOT/'outputs/mpp_measurements_draft_v1'; D=OUT/'draft_v3'",
                      "OUT=ROOT/'outputs/mpp_measurements_followup_2026-10-26'; D=OUT/'draft_v4'")
source=source.replace("if r['geometry']]", "if r['geometry'] and r['measurement_id'].startswith('D2_')]")
exec(compile(source,str(original),'exec'))
