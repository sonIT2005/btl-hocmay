"""Additional navigation only: no blob size is used as a cell measurement."""
import argparse,csv,hashlib,json
from collections import Counter
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(r'C:\Users\Admin\Documents\GitHub\btl-hocmay')
DATA=Path(r'C:\Users\Admin\Documents\FrameView\btl-histo\data')
BASE=ROOT/'outputs/mpp_measurements_draft_v1/draft_v3'
OUT=ROOT/'outputs/mpp_measurements_followup_2026-10-26'
OUT.mkdir(exist_ok=False);(OUT/'navigation').mkdir()
rows=list(csv.DictReader((BASE/'locked_candidates.csv').open(encoding='utf-8-sig')))
previous=json.loads((BASE/'measurements_geometry.json').read_text())
selected=Counter(r['candidate_id'] for r in previous if r['decision']=='draft_eligible')
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
nav=[]
for r in rows:
 source=r['source'];q=int(r['queue_order'])
 if source not in ('BreakHis','BACH','CRC-VAL-HE-7K'):continue
 # All locked BreakHis images, all non-full BACH images, and CRC images not yet represented.
 if source=='BACH' and selected[r['candidate_id']]>=3:continue
 if source=='CRC-VAL-HE-7K' and (selected[r['candidate_id']]>0 or q not in (11,13,18,23,26,35,44,56)):continue
 path=DATA/r['image_path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==r['raw_sha256']
 im=Image.open(path).convert('RGB');a=np.array(im).astype('float32');g=cv2.cvtColor(a.astype('uint8'),cv2.COLOR_RGB2GRAY)
 # Relative contrast rather than a fixed dark-pixel threshold helps navigate pale images.
 thresh=float(np.percentile(g,25));mask=((g<thresh)&(a[:,:,2]-a[:,:,1]>1)).astype('uint8')
 n,labels,stats,cent=cv2.connectedComponentsWithStats(mask,8);poss=[]
 for k in range(1,n):
  x,y,w,h,area=map(int,stats[k]);cx,cy=map(float,cent[k]);fill=area/(w*h)
  if not (8<=area<=1800 and min(w,h)>=3 and max(w/h,h/w)<=1.55 and fill>=.52):continue
  if x<3 or y<3 or x+w>=im.width-3 or y+h>=im.height-3:continue
  tile=g[y:y+h,x:x+w];values=tile[labels[y:y+h,x:x+w]==k]
  pad=g[max(0,y-6):min(im.height,y+h+6),max(0,x-6):min(im.width,x+w+6)]
  contrast=float(np.median(pad))-float(np.median(values))
  score=fill*12+contrast*.25-float(values.std())*.12
  if any((cx-float(np.mean(np.array(p['polygon'])[:,0])))**2+(cy-float(np.mean(np.array(p['polygon'])[:,1])))**2<16**2
         for p in previous if p['candidate_id']==r['candidate_id'] and p.get('polygon')):continue
  poss.append((score,cx,cy,w,h,area))
 chosen=[]
 for p in sorted(poss,reverse=True):
  if all((p[1]-c[1])**2+(p[2]-c[2])**2>=28**2 for c in chosen):chosen.append(p)
  if len(chosen)==6:break
 item={**r,'adaptive_threshold':thresh,'locators':[{'x':round(p[1],2),'y':round(p[2],2),'w':p[3],'h':p[4]} for p in chosen]}
 nav.append(item)
(OUT/'navigation/adaptive_locators.json').write_text(json.dumps(nav,indent=2),encoding='utf8')
for source in ('CRC-VAL-HE-7K','BACH','BreakHis'):
 subset=[r for r in nav if r['source']==source]
 for start in range(0,len(subset),12):
  sheet=Image.new('RGB',(1800,1440),'white');d=ImageDraw.Draw(sheet)
  for i,r in enumerate(subset[start:start+12]):
   xx=(i%3)*600;yy=(i//3)*360
   im=Image.open(DATA/r['image_path']).convert('RGB');thumb=im.copy();thumb.thumbnail((230,230));sheet.paste(thumb,(xx,yy+30))
   d.text((xx+3,yy+2),f"{source} q{r['queue_order']} {r['candidate_id'][:8]}",font=font,fill='black')
   for j,p in enumerate(r['locators']):
    cx,cy=int(p['x']),int(p['y']);half=20 if source!='BACH' else 30
    l=max(0,min(im.width-half*2,cx-half));t=max(0,min(im.height-half*2,cy-half))
    crop=im.crop((l,t,l+half*2,t+half*2)).resize((112,112),Image.Resampling.NEAREST)
    dx=xx+240+(j%3)*118;dy=yy+30+(j//3)*148;sheet.paste(crop,(dx,dy))
    d.text((dx,dy+114),f"{j+1}:{p['x']:.0f},{p['y']:.0f}",font=font,fill='black')
    px=xx+p['x']*thumb.width/im.width;py=yy+30+p['y']*thumb.height/im.height
    d.ellipse((px-3,py-3,px+3,py+3),outline='red');d.text((px+3,py),str(j+1),font=font,fill='red')
  sheet.save(OUT/f'navigation/{source}_extra_{start//12+1:02d}.png')
print({s:sum(r['source']==s for r in nav) for s in ('CRC-VAL-HE-7K','BACH','BreakHis')})
