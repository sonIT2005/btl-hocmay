from pathlib import Path
script=Path(r'C:\Users\Admin\AppData\Local\Temp\mpp_grids_20261026.py')
source=script.read_text();start=source.index('targets=');end=source.index('font=',start)
source=source[:start]+"targets={'BreakHis':{35:[(9,303)],49:[(522,306)],56:[(618,93)],60:[(602,67)]}}\n"+source[end:]
source=source.replace("navigation/grid_targets.json","navigation/breakhis_grid_targets.json")
exec(compile(source,str(script),'exec'))
