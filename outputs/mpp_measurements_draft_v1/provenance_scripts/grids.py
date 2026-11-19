exec(open(r'C:\Users\Admin\AppData\Local\Temp\btl_mpp_draft_20261025_v1\navigate.py').read().split('OUT.mkdir')[0])
OUT=ROOT/'outputs/mpp_measurements_draft_v1'
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
rows=json.loads((OUT/'navigation/locators.json').read_text())
targets={
 'CRC-VAL-HE-7K':{3:[(207,109),(30,35)],6:[(72,150),(47,165)],7:[(190,73)],16:[(150,51),(126,103),(132,38)],18:[(158,69),(145,45)],20:[(68,49),(140,32),(182,145)],21:[(78,163),(133,142)],24:[(68,65),(118,83),(174,137)],28:[(162,36),(206,81),(97,13)],33:[(33,198),(135,108),(142,203)],36:[(206,104),(97,186),(41,164)],39:[(112,136)],47:[(81,176),(33,137),(39,212)],48:[(93,66),(126,145)],60:[(162,76),(196,119),(147,151)]},
 'BACH':{2:[(1987,432)],9:[(1681,42)],15:[(1014,605)],16:[(1500,567),(532,1217)],20:[(1127,616)],23:[(266,1505)],25:[(218,935)],26:[(787,226)],27:[(995,133),(2023,353)],29:[(1945,966),(602,584)],30:[(582,833)],32:[(445,1324),(371,874)],35:[(1571,872),(821,138)],36:[(921,1290),(568,871)],47:[(1967,1068)],49:[(211,1400)],50:[(856,297),(1395,755)],52:[(885,1119)],53:[(1384,54)],56:[(1664,418)],57:[(479,1070)],58:[(211,386)]},
 'BreakHis':{4:[(348,48)],21:[(535,416),(668,434)],36:[(236,236)],42:[(393,147)],43:[(11,22)],
             10:[(120,355)],13:[(260,60)],22:[(282,328)],29:[(175,173)],37:[(544,130)],50:[(546,335),(561,214)]}}
records=[]
for source,queue in targets.items():
 cohort=[]
 for q,points in queue.items():
  r=next(r for r in rows if r['source']==source and int(r['queue_order'])==q)
  for index,(cx,cy) in enumerate(points,1):
   cohort.append(dict(id=f'{source}_q{q:02d}_{index}',candidate_id=r['candidate_id'],source=source,q=q,cx=cx,cy=cy))
 records+=cohort
 for start in range(0,len(cohort),6):
  sheet=Image.new('RGB',(1500,1080),'white');d=ImageDraw.Draw(sheet)
  for i,c in enumerate(cohort[start:start+6]):
   r=next(r for r in rows if r['candidate_id']==c['candidate_id']);im=Image.open(DATA/r['image_path']).convert('RGB')
   half=20 if source!='BACH' else 25;scale=8;size=half*2
   left=max(0,min(im.width-size,c['cx']-half));top=max(0,min(im.height-size,c['cy']-half))
   crop=im.crop((left,top,left+size,top+size)).resize((size*scale,size*scale),Image.Resampling.NEAREST)
   xx=(i%3)*500+50;yy=(i//3)*540+65;sheet.paste(crop,(xx,yy))
   d.text((xx-35,yy-55),c['id'],font=font,fill='black')
   for t in range(size):
    if (left+t)%5==0:
     x=xx+(t+.5)*scale;d.line((x,yy-5,x,yy+size*scale),fill='#999999',width=1);d.text((x-8,yy-23),str(left+t),font=font,fill='black')
    if (top+t)%5==0:
     y=yy+(t+.5)*scale;d.line((xx-5,y,xx+size*scale,y),fill='#999999',width=1);d.text((xx-34,y-8),str(top+t),font=font,fill='black')
   d.text((xx,yy+size*scale+10),f'RAW origin=({left},{top}); {scale}x nearest',font=font,fill='black')
  sheet.save(OUT/f'navigation/grid_{source}_{start//6+1:02d}.png')
(OUT/'navigation/grid_targets.json').write_text(json.dumps(records,indent=2))
