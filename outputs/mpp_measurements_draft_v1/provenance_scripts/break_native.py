import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
root=Path(r'C:\Users\Admin\Documents\GitHub\btl-hocmay');data=Path(r'C:\Users\Admin\Documents\FrameView\btl-histo\data')
out=root/'outputs/mpp_measurements_draft_v1/navigation'
rows=[r for r in json.loads((out/'locators.json').read_text()) if r['source']=='BreakHis']
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
for start in range(0,60,4):
 sheet=Image.new('RGB',(1400,1000),'white');d=ImageDraw.Draw(sheet)
 for i,r in enumerate(rows[start:start+4]):
  x=(i%2)*700;y=(i//2)*500;im=Image.open(data/r['image_path']).convert('RGB')
  sheet.paste(im,(x,y+35));d.text((x+2,y+2),f"q{r['queue_order']} {Path(r['image_path']).name}",font=font,fill='black')
 sheet.save(out/f'BreakHis_native_{start+1:02d}_{start+4:02d}.png')
