exec(open(r'C:\Users\Admin\AppData\Local\Temp\btl_mpp_draft_20261025_v1\navigate.py').read().split('OUT.mkdir')[0])
OUT=ROOT/'outputs/mpp_measurements_draft_v1'
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
rows=json.loads((OUT/'navigation/locators.json').read_text()); results=[]
for source in ('CRC-VAL-HE-7K','BACH','BreakHis'):
 sheet=Image.new('RGB',(2000,1260),'white');d=ImageDraw.Draw(sheet)
 for i,r in enumerate([r for r in rows if r['source']==source]):
  im=Image.open(DATA/r['image_path']).convert('RGB');a=np.asarray(im).astype('float32')
  mask=((a[:,:,0]>125)&(a[:,:,0]-a[:,:,1]>35)&(a[:,:,2]-a[:,:,1]>5)).astype('uint8')
  n,lab,stats,cent=cv2.connectedComponentsWithStats(mask,8);choices=[]
  for k in range(1,n):
   x,y,w,h,area=map(int,stats[k])
   if 12<=area<=1200 and min(w,h)>=4 and max(w/h,h/w)<1.8 and area/(w*h)>.5:
    choices.append((area/(w*h),cent[k].tolist()))
  chosen=[]
  for _,p in sorted(choices,reverse=True):
   if all(sum((u-v)**2 for u,v in zip(p,q))>40**2 for q in chosen): chosen.append(p)
   if len(chosen)==2:break
  xx=(i%10)*200;yy=(i//10)*210
  d.text((xx,yy),f'q{r["queue_order"]} {r["candidate_id"][:6]}',font=font,fill='black')
  for j,p in enumerate(chosen):
   half=20;cx,cy=map(round,p);left=max(0,min(im.width-40,cx-half));top=max(0,min(im.height-40,cy-half))
   crop=im.crop((left,top,left+40,top+40)).resize((96,150),Image.Resampling.NEAREST)
   # Square pixels retained: pad each 96x96 crop, do not stretch for display.
   crop=im.crop((left,top,left+40,top+40)).resize((96,96),Image.Resampling.NEAREST)
   sheet.paste(crop,(xx+j*100,yy+26));d.text((xx+j*100,yy+125),f'{cx},{cy}',font=font,fill='black')
  if not chosen:d.text((xx,yy+50),'No red locator',font=font,fill='black')
  results.append(dict(candidate_id=r['candidate_id'],source=source,queue_order=int(r['queue_order']),red_locator_points=chosen))
 sheet.save(OUT/f'navigation/rbc_{source}.png')
(OUT/'navigation/rbc_locators.json').write_text(json.dumps(results,indent=2),encoding='utf8')
