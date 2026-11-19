import json,math,csv
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(r'C:\Users\Admin\Documents\GitHub\btl-hocmay')
OUT=ROOT/'outputs/mpp_measurements_draft_v1'; D=OUT/'draft_v3'
DATA=Path(r'C:\Users\Admin\Documents\FrameView\btl-histo\data')
rows=[r for r in json.loads((D/'measurements_geometry.json').read_text()) if r['geometry']]
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
for start in range(0,len(rows),9):
 sheet=Image.new('RGB',(1680,900),'white');draw=ImageDraw.Draw(sheet)
 for i,r in enumerate(rows[start:start+9]):
  xx=(i%3)*560;yy=(i//3)*300
  x,y=zip(*r['polygon']);bounds=(max(0,math.floor(min(x))-5),max(0,math.floor(min(y))-5),min(r['width'],math.ceil(max(x))+6),min(r['height'],math.ceil(max(y))+6))
  plain=Image.open(DATA/r['image_path']).convert('RGB').crop(bounds)
  marked=Image.open(D/'objects'/(r['measurement_id']+'_context.png')).crop(bounds)
  for j,im in enumerate((plain,marked)):
   im=im.resize((im.width*8,im.height*8),Image.Resampling.NEAREST);im.thumbnail((268,245),Image.Resampling.NEAREST)
   sheet.paste(im,(xx+j*280,yy+42))
  draw.text((xx+3,yy+2),r['measurement_id']+' '+r['decision'],font=font,fill='black')
  draw.text((xx+3,yy+21),f"raw crop {bounds}; D={r['diameter_px']:.2f} H={r['axis_h_px']:.2f} V={r['axis_v_px']:.2f}",font=font,fill='black')
 sheet.save(OUT/f'navigation/final_caliper_qa_{start//9+1:02d}.png')
