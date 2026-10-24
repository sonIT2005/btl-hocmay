"""Keep small upstream descriptions and licenses with the local dataset provenance."""
from pathlib import Path
import json
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
SOURCES={
 'lc25000_readme': 'https://raw.githubusercontent.com/tampapath/lung_colon_image_set/master/README.md',
 'breakhis_description':'https://web.inf.ufpr.br/vri/databases/breast-cancer-histopathological-database-BreakHis/',
 'breakhis_paper':'https://www.inf.ufpr.br/lesoliveira/download/TBME-00608-2015-R2-preprint.pdf',
 'crc_record':'https://zenodo.org/api/records/1214456',
 'bach_record':'https://zenodo.org/api/records/3632035',
 'bach_license':'https://zenodo.org/records/3632035/files/LICENSE.txt?download=1',
 'bach_readme':'https://zenodo.org/records/3632035/files/README.txt?download=1',
 'phikon_model_card':'https://huggingface.co/owkin/phikon/raw/main/README.md',
 'phikon_license':'https://raw.githubusercontent.com/owkin/HistoSSLscaling/main/LICENSE.txt',
 'lunghist_paper':'https://pmc.ncbi.nlm.nih.gov/articles/PMC11455975/',
}
def main():
 out=ROOT/'data/downloads/provenance';out.mkdir(parents=True,exist_ok=True)
 results=[]
 for name,url in SOURCES.items():
  try:
   request=urllib.request.Request(url,headers={'User-Agent':'FrameView-Academic-Preparation/1.0'})
   with urllib.request.urlopen(request,timeout=60) as r:content=r.read()
   path=out/(name+('.pdf' if name=='breakhis_paper' else '.json' if name.endswith('_record') else '.txt'))
   path.write_bytes(content);results.append({'name':name,'url':url,'bytes':len(content),'status':'saved'})
  except Exception as e:results.append({'name':name,'url':url,'status':'failed','error':repr(e)})
  print(results[-1],flush=True)
 (ROOT/'results/source_access.json').write_text(json.dumps(results,indent=2),encoding='utf-8')

if __name__=='__main__':main()
