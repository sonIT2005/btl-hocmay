import csv, hashlib, json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(r'C:\Users\Admin\Documents\GitHub\btl-hocmay')
DATA=Path(r'C:\Users\Admin\Documents\FrameView\btl-histo\data')
OUT=ROOT/'outputs/mpp_measurements_draft_v1'
OUT.mkdir(exist_ok=False)
(OUT/'navigation').mkdir()
rows=list(csv.DictReader((ROOT/'outputs/maintenance_2026-10-25/mpp_kit/candidates.csv').open(encoding='utf-8-sig')))
rows=[r for r in rows if r['source'] in ('BACH','BreakHis','CRC-VAL-HE-7K')]
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
loc=[]
for r in rows:
 p=DATA/r['image_path']; assert hashlib.sha256(p.read_bytes()).hexdigest()==r['raw_sha256']
 im=Image.open(p).convert('RGB'); a=np.array(im); assert im.size==(int(r['width']),int(r['height']))
 gray=cv2.cvtColor(a,cv2.COLOR_RGB2GRAY); blue=a[:,:,2].astype(float); green=a[:,:,1].astype(float)
 threshold=min(105,float(np.percentile(gray,18)))
 mask=((gray<threshold)&(blue>green+2)).astype('uint8')
 n,lab,stats,cent=cv2.connectedComponentsWithStats(mask,8)
 candidates=[]
 for k in range(1,n):
  x,y,w,h,area=map(int,stats[k]); cx,cy=cent[k]
  if area<10 or area>900 or w<4 or h<4 or max(w/h,h/w)>1.65 or x<2 or y<2 or x+w>=im.width-2 or y+h>=im.height-2: continue
  patch=gray[y:y+h,x:x+w]; pixels=patch[lab[y:y+h,x:x+w]==k]
  fill=area/(w*h)
  if fill<.48: continue
  score=fill*20-float(pixels.mean())*.08-float(pixels.std())*.15
  candidates.append((score,cx,cy,w,h,area))
 chosen=[]
 for s in sorted(candidates,reverse=True):
  if all((s[1]-c[1])**2+(s[2]-c[2])**2>50**2 for c in chosen): chosen.append(s)
  if len(chosen)==3: break
 r['locators']=[{'x':round(c[1],2),'y':round(c[2],2),'w':c[3],'h':c[4],'threshold_blob_area':c[5]} for c in chosen]
 loc.append(r)
 print(r['source'],r['queue_order'],len(chosen),flush=True)
(OUT/'navigation/locators.json').write_text(json.dumps(loc,indent=2),encoding='utf8')
for source in ('CRC-VAL-HE-7K','BACH','BreakHis'):
 cohort=[r for r in loc if r['source']==source]
 for start in range(0,60,20):
  sheet=Image.new('RGB',(1800,1400),'#eeeeee'); d=ImageDraw.Draw(sheet)
  for i,r in enumerate(cohort[start:start+20]):
   x=(i%4)*450;y=(i//4)*280
   im=Image.open(DATA/r['image_path']).convert('RGB')
   preview=im.copy();preview.thumbnail((218,210))
   sheet.paste(preview,(x,y+35))
   d.text((x+2,y+2),f"{source} q{r['queue_order']} {r['candidate_id'][:8]}",font=font,fill='black')
   for k,c in enumerate(r['locators']):
    half=24 if source!='BACH' else 42
    left=max(0,min(im.width-2*half,int(c['x'])-half));top=max(0,min(im.height-2*half,int(c['y'])-half))
    crop=im.crop((left,top,left+2*half,top+2*half)).resize((104,104),Image.Resampling.NEAREST)
    xx=x+225+(k%2)*110; yy=y+35+(k//2)*119
    sheet.paste(crop,(xx,yy));d.text((xx,yy+104),f"{k+1}: {c['x']:.0f},{c['y']:.0f}",font=font,fill='black')
    px=x+c['x']*preview.width/im.width;py=y+35+c['y']*preview.height/im.height
    d.ellipse((px-4,py-4,px+4,py+4),outline='red',width=1);d.text((px+4,py),str(k+1),font=font,fill='red')
  sheet.save(OUT/f'navigation/{source}_{start+1:02d}_{start+20:02d}.png')
