import csv,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(r'C:\Users\Admin\Documents\GitHub\btl-hocmay');DATA=Path(r'C:\Users\Admin\Documents\FrameView\btl-histo\data')
OUT=ROOT/'outputs/mpp_measurements_followup_2026-10-26'
rows=list(csv.DictReader((ROOT/'outputs/mpp_measurements_draft_v1/draft_v3/locked_candidates.csv').open(encoding='utf-8-sig')))
targets={'CRC-VAL-HE-7K':{18:[(173,94),(180,116)],44:[(137,65)],36:[(112,201)]},
         'BACH':{9:[(1057,717),(557,215)],16:[(1981,1387)],20:[(484,1480),(458,1139)],
                 24:[(119,988),(1290,332),(778,165)],25:[(1044,248),(1095,1153),(106,894)],47:[(83,1295),(838,478)]}}
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15);records=[]
for source,queues in targets.items():
 cohort=[]
 for q,points in queues.items():
  r=next(r for r in rows if r['source']==source and int(r['queue_order'])==q)
  for i,(cx,cy) in enumerate(points,1):cohort.append(dict(id=f'D2_{"CRC" if source.startswith("CRC") else source}_q{q:02d}_{i}',candidate_id=r['candidate_id'],source=source,q=q,cx=cx,cy=cy))
 records+=cohort
 for start in range(0,len(cohort),6):
  sheet=Image.new('RGB',(1500,1080),'white');d=ImageDraw.Draw(sheet)
  for i,t in enumerate(cohort[start:start+6]):
   r=next(r for r in rows if r['candidate_id']==t['candidate_id']);im=Image.open(DATA/r['image_path']).convert('RGB')
   half=25 if source=='BACH' else 20;size=half*2;scale=8
   left=max(0,min(im.width-size,t['cx']-half));top=max(0,min(im.height-size,t['cy']-half))
   xx=(i%3)*500+50;yy=(i//3)*540+65
   crop=im.crop((left,top,left+size,top+size)).resize((size*scale,size*scale),Image.Resampling.NEAREST)
   sheet.paste(crop,(xx,yy));d.text((xx-35,yy-55),t['id'],font=font,fill='black')
   for k in range(size):
    if (left+k)%5==0:
     x=xx+(k+.5)*scale;d.line((x,yy-5,x,yy+size*scale),fill='#999999');d.text((x-8,yy-23),str(left+k),font=font,fill='black')
    if (top+k)%5==0:
     y=yy+(k+.5)*scale;d.line((xx-5,y,xx+size*scale,y),fill='#999999');d.text((xx-34,y-8),str(top+k),font=font,fill='black')
   d.text((xx,yy+size*scale+10),f'RAW origin=({left},{top}); nearest {scale}x',font=font,fill='black')
  sheet.save(OUT/f'navigation/new_grid_{source}_{start//6+1:02d}.png')
(OUT/'navigation/grid_targets.json').write_text(json.dumps(records,indent=2))
