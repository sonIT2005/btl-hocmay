"""LC25000: pretrained-CNN candidates, geometrically verified components.

Group IDs are reconstructed image-family IDs, never claimed to be patient IDs.
No inference model for the research experiments is trained here.
"""
from __future__ import annotations
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import csv
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("TORCH_HOME", str(ROOT/".cache/torch"))
os.environ.setdefault("OMP_NUM_THREADS", "4")
import cv2
import numpy as np
import torch
from PIL import Image
import yaml
from sklearn.neighbors import NearestNeighbors
from threadpoolctl import threadpool_limits
from torchvision.models import resnet18, ResNet18_Weights
from torchvision import transforms
from torch.utils.data import Dataset, DataLoader

class Images(Dataset):
    def __init__(self, paths):
        self.paths=paths
        self.transform=transforms.Compose([transforms.Resize((160,160)),transforms.ToTensor(),
             transforms.Normalize([.485,.456,.406],[.229,.224,.225])])
    def __len__(self):return len(self.paths)
    def __getitem__(self,i):
        with Image.open(self.paths[i]) as im:return self.transform(im.convert('RGB'))

class UnionFind:
    def __init__(self,n):self.parent=list(range(n));self.size=[1]*n
    def find(self,a):
        while self.parent[a]!=a:
            self.parent[a]=self.parent[self.parent[a]];a=self.parent[a]
        return a
    def union(self,a,b):
        a,b=self.find(a),self.find(b)
        if a==b:return False
        if self.size[a]<self.size[b]:a,b=b,a
        self.parent[b]=a;self.size[a]+=self.size[b];return True

@lru_cache(maxsize=4096)
def load_gray(path,size):
    a=cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if a is None:raise ValueError(f"Unreadable image {path}")
    return cv2.resize(a,(size,size),interpolation=cv2.INTER_AREA)

@lru_cache(maxsize=2048)
def descriptor(path,size,features,mirror=False):
    gray=load_gray(path,size)
    if mirror:gray=cv2.flip(gray,1)
    cache=ROOT/'outputs/grouping/descriptors'/f'{size}_{features}_{int(mirror)}_{Path(path).stem}.npz'
    if cache.exists():
        with np.load(cache) as data:
            points=data['points'];d=data['descriptors']
            return gray,points,d if len(d) else None
    sift=cv2.SIFT_create(nfeatures=features,contrastThreshold=.025,edgeThreshold=15)
    kp,d=sift.detectAndCompute(gray,None)
    points=np.array([x.pt for x in kp],dtype=np.float32)
    cache.parent.mkdir(parents=True,exist_ok=True)
    tmp=cache.with_name(cache.stem+f'.{threading.get_ident()}.tmp.npz')
    np.savez(tmp,points=points,descriptors=d if d is not None else np.empty((0,128),dtype=np.float32))
    tmp.replace(cache)
    return gray,points,d

def verify(a,b,cfg):
    size=cfg['verification_size'];nf=cfg['sift_features']
    # Cheap direct pixel agreement first; this is stricter than a pHash match.
    # It resolves exact D4 variants without spending SIFT on identical images.
    gaa=load_gray(str(a),size);gbb=load_gray(str(b),size)
    av=gaa[8:-8,8:-8].astype(np.float32).ravel();av-=av.mean()
    an=float(np.linalg.norm(av))
    if an>1e-6:
        for flipped in (False,True):
            value=np.fliplr(gbb) if flipped else gbb
            for k in range(4):
                bv=np.rot90(value,k)[8:-8,8:-8].astype(np.float32).ravel();bv-=bv.mean()
                corr=float(np.dot(av,bv)/(an*max(float(np.linalg.norm(bv)),1e-6)))
                if corr>=.96:
                    return {'inliers':0,'inlier_ratio':1.0,'coverage':1.0,'scale':1.0,
                            'correlation':round(corr,5),'mirror':flipped}
    ga,pa,da=descriptor(str(a),size,nf,False)
    if da is None or len(da)<cfg['min_inliers']:return None
    for mirror in (False,True):
        gb,pb,db=descriptor(str(b),size,nf,mirror)
        if db is None or len(db)<cfg['min_inliers']:continue
        matches=cv2.BFMatcher(cv2.NORM_L2).knnMatch(db,da,k=2)
        good=[x[0] for x in matches if len(x)==2 and x[0].distance<.70*x[1].distance]
        if len(good)<cfg['min_inliers']:continue
        source=np.float32([pb[m.queryIdx] for m in good])
        target=np.float32([pa[m.trainIdx] for m in good])
        mat,mask=cv2.estimateAffine2D(source,target,method=cv2.RANSAC,
            ransacReprojThreshold=cfg['max_reprojection_error'],maxIters=2000,confidence=.999)
        if mat is None:continue
        count=int(mask.sum());ratio=count/len(good)
        scale=float(np.sqrt(abs(np.linalg.det(mat[:,:2]))))
        if count<cfg['min_inliers'] or ratio<cfg['min_inlier_ratio']:continue
        singular=np.linalg.svd(mat[:,:2],compute_uv=False)
        if np.linalg.det(mat[:,:2])<=0:continue
        if not cfg['scale_range'][0]<=singular.min()<=singular.max()<=cfg['scale_range'][1]:continue
        if singular.max()/singular.min()>cfg.get('max_axis_scale_ratio',1.35):continue
        pts=target[mask.ravel().astype(bool)]
        coverage=float(cv2.contourArea(cv2.convexHull(pts)))/(size*size)
        if coverage<cfg['min_coverage']:continue
        warped=cv2.warpAffine(gb,mat,(size,size))
        valid=cv2.warpAffine(np.full_like(gb,255),mat,(size,size))>254
        valid[:8]=False;valid[-8:]=False;valid[:,:8]=False;valid[:,-8:]=False
        if valid.mean()<.50:continue
        correlation=float(np.corrcoef(ga[valid],warped[valid])[0,1])
        if not np.isfinite(correlation) or correlation<cfg['min_overlap_correlation']:continue
        return {'inliers':count,'inlier_ratio':round(ratio,5),'coverage':round(coverage,5),
                'scale':round(scale,5),'correlation':round(correlation,5),'mirror':mirror}
    return None

def embeddings(paths,out):
    cache=out/'features.npy';names=out/'feature_paths.json'
    listed=[str(x.relative_to(ROOT/'data')) for x in paths]
    if cache.exists() and names.exists() and json.loads(names.read_text())==listed:
        return np.load(cache)
    torch.set_num_threads(4)
    torch.manual_seed(42)
    model=resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
    model.fc=torch.nn.Identity();model.eval()
    loader=DataLoader(Images(paths),batch_size=64,num_workers=4,shuffle=False,persistent_workers=True)
    features=[];start=time.time()
    with torch.inference_mode():
        for i,batch in enumerate(loader):
            value=model(batch).numpy();value/=np.maximum(np.linalg.norm(value,axis=1,keepdims=True),1e-12)
            features.append(value)
            if i%20==0:print(f'EMBEDDINGS {min((i+1)*64,len(paths))}/{len(paths)} {time.time()-start:.0f}s',flush=True)
    array=np.concatenate(features)
    np.save(cache,array);names.write_text(json.dumps(listed))
    return array

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--neighbors',type=int)
    parser.add_argument('--sift-refine',action='store_true')
    parser.add_argument('--verify-cached',action='store_true')
    parser.add_argument('--rescue-small',action='store_true')
    parser.add_argument('--cnn-rescue-small',action='store_true')
    parser.add_argument('--representatives',type=int,choices=[1,3],default=1);args=parser.parse_args()
    config=yaml.safe_load((ROOT/'configs/preparation.yaml').read_text())['grouping']
    if args.rescue_small or args.cnn_rescue_small:
        config.update(verification_size=512,sift_features=500,min_inliers=20)
    if args.neighbors:config['neighbors']=args.neighbors
    cv2.setNumThreads(1);cv2.setRNGSeed(42)
    out=ROOT/'outputs/grouping';out.mkdir(parents=True,exist_ok=True)
    def candidate_cache(label):
        suffix='' if args.representatives==1 else f'_r{args.representatives}'
        if args.rescue_small:suffix+='_highres'
        return out/f'sift_candidates_{label}{suffix}.npz'
    paths=sorted((ROOT/'data/raw/LC25000').rglob('*.jpeg'))
    if len(paths)!=25000:raise ValueError(f'LC25000 count: {len(paths)}')
    labels=[p.parent.name for p in paths]
    feats=embeddings(paths,out)
    uf=UnionFind(len(paths));accepted=[];candidates=[]
    old=ROOT/'data/downloads/provenance/legacy_phash_groups.csv'
    byname={p.name:i for i,p in enumerate(paths)}
    checkpoint=out/'accepted_checkpoint.jsonl'
    if checkpoint.exists():
        for line in checkpoint.read_text().splitlines():
            edge=json.loads(line)
            if uf.union(byname[edge['a']],byname[edge['b']]):accepted.append(edge)
    # Compare with the existing exact D4-pHash baseline, but verify all of its
    # edges too. A perceptual-hash collision alone never joins two families.
    baseline={}
    if not old.exists():
        import imagehash
        def canonical(path):
            with Image.open(path) as im:im=im.convert('L').resize((128,128),Image.Resampling.BILINEAR)
            hashes=[]
            for k in range(4):
                rotated=im.rotate(k*90)
                hashes.extend([str(imagehash.phash(rotated)),str(imagehash.phash(rotated.transpose(Image.Transpose.FLIP_LEFT_RIGHT)))])
            return min(hashes)
        old.parent.mkdir(parents=True,exist_ok=True)
        with ThreadPoolExecutor(max_workers=4) as pool,old.open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=['filename','cluster_id']);writer.writeheader()
            for p,h in zip(paths,pool.map(canonical,paths)):
                writer.writerow({'filename':p.name,'cluster_id':p.parent.name+':'+h})
    with old.open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):baseline.setdefault(row['cluster_id'],[]).append(byname[row['filename']])
    for members in baseline.values():
        for j in members[1:]:candidates.append((1.01,members[0],j,'phash'))
    for label in sorted(set(labels)):
        if args.sift_refine or args.verify_cached:continue
        indexes=np.array([i for i,l in enumerate(labels) if l==label]);x=feats[indexes]
        k=min(config['neighbors']+1,len(x))
        nn=NearestNeighbors(n_neighbors=k,metric='cosine',algorithm='brute',n_jobs=4).fit(x)
        query_local=[i for i,j in enumerate(indexes) if uf.size[uf.find(int(j))]<=4] if args.cnn_rescue_small else list(range(len(x)))
        if not query_local:continue
        distances,neighbors=nn.kneighbors(x[query_local])
        seen=set()
        for qi,i in enumerate(query_local):
            for d,j in zip(distances[qi,1:],neighbors[qi,1:]):
                if 1-d<(.65 if args.cnn_rescue_small else config['candidate_cosine']):continue
                a,b=sorted((int(indexes[i]),int(indexes[j])))
                if (a,b) not in seen:candidates.append((float(1-d),a,b,'cnn_rescue' if args.cnn_rescue_small else 'cnn'));seen.add((a,b))
        print('CANDIDATES',label,len(seen),flush=True)
    if args.sift_refine:
        # Rotation-invariant local-descriptor retrieval recovers candidates that
        # a global ImageNet embedding misses. Votes propose pairs only; the same
        # pixel/affine checks below still decide whether to merge them.
        with threadpool_limits(limits=1),ThreadPoolExecutor(max_workers=4) as pool:
            for label in sorted(set(labels)):
                members_by_root={}
                for i,l in enumerate(labels):
                    if l==label:members_by_root.setdefault(uf.find(i),[]).append(i)
                indexes=[]
                for members in members_by_root.values():
                    if args.representatives==1 or len(members)==1:
                        indexes.append(members[0]);continue
                    x=feats[members];mean=x.mean(axis=0)
                    chosen=[int(np.argmax(x@mean))]
                    while len(chosen)<min(args.representatives,len(members)):
                        distance=np.max(x@x[chosen].T,axis=1);distance[chosen]=np.inf
                        chosen.append(int(np.argmin(distance)))
                    indexes.extend(members[j] for j in chosen)
                indexes.sort()
                size=config['verification_size'];nf=config['sift_features']
                def desc(i):return descriptor(str(paths[i]),size,nf,False)[2]
                descriptors=list(pool.map(desc,indexes))
                bank=[];owners=[]
                for i,d in zip(indexes,descriptors):
                    if d is not None:bank.append(d);owners.extend([i]*len(d))
                if not bank:continue
                bank=np.concatenate(bank).astype(np.float32);owners=np.asarray(owners,dtype=np.int32)
                index=cv2.flann_Index(bank,dict(algorithm=1,trees=4))
                pairs={}
                def retrieve(item):
                    i,d=item
                    votes=Counter()
                    for mirror,query in [(False,d),(True,descriptor(str(paths[i]),size,nf,True)[2])]:
                        if query is None:continue
                        nn,dist=index.knnSearch(query.astype(np.float32),8,params=dict(checks=48))
                        valid=(dist<180.0**2)&(owners[nn]!=i)
                        votes.update(owners[nn[valid]].tolist())
                    return i,votes
                queries=[(i,d) for i,d in zip(indexes,descriptors)
                         if not args.rescue_small or uf.size[uf.find(i)]<=4]
                for n,(i,votes) in enumerate(pool.map(retrieve,queries)):
                    for j,count in votes.most_common(12):
                        if count<8:continue
                        a,b=sorted((i,int(j)))
                        pairs[(a,b)]=max(pairs.get((a,b),0),count)
                    if n%500==0:print('SIFT_RETRIEVAL',label,n,len(indexes),flush=True)
                for (a,b),votes in pairs.items():candidates.append((min(.9999,votes/100),a,b,'sift_votes'))
                np.savez(candidate_cache(label),pairs=np.array([[a,b,v] for (a,b),v in pairs.items()],dtype=np.int32))
                print('SIFT_CANDIDATES',label,len(indexes),len(pairs),flush=True)
                del index,bank,owners,descriptors
    if args.verify_cached:
        for label in sorted(set(labels)):
            cache=candidate_cache(label)
            if not cache.exists():raise FileNotFoundError(cache)
            for a,b,votes in np.load(cache)['pairs']:
                candidates.append((min(.9999,float(votes)/100),int(a),int(b),'sift_votes'))
    candidates.sort(key=lambda x:(-x[0],x[1],x[2]))
    verified=0;negative=set();index=0
    # Root-pair memoization avoids repeatedly testing 20x20 variants of two
    # unrelated tissue fields. Conservative negatives can only leave groups split.
    with threadpool_limits(limits=1),ThreadPoolExecutor(max_workers=4) as pool,checkpoint.open('a',encoding='utf-8') as log:
        while index<len(candidates):
            batch=[];pending=set()
            while index<len(candidates) and len(batch)<64:
                sim,a,b,method=candidates[index];index+=1
                ra,rb=sorted((uf.find(a),uf.find(b)))
                if ra==rb or (ra,rb) in negative or (ra,rb) in pending:continue
                pending.add((ra,rb));batch.append((sim,a,b,method))
            def check(item):
                sim,a,b,method=item
                return verify(paths[a],paths[b],config)
            for item,match in zip(batch,pool.map(check,batch)):
                sim,a,b,method=item;verified+=1
                if match and uf.union(a,b):
                    edge={'a':paths[a].name,'b':paths[b].name,'candidate':method,
                          'cosine':round(sim,5) if method=='cnn' else '',
                          'candidate_score':round(sim,5),**match}
                    accepted.append(edge);log.write(json.dumps(edge)+'\n')
                elif not match:
                    ra,rb=sorted((uf.find(a),uf.find(b)))
                    negative.add((ra,rb))
            log.flush()
            if verified and (verified//1000 != (verified-len(batch))//1000 or index==len(candidates)):
                print('VERIFY',verified,'MERGES',len(accepted),'COMPONENTS',len(paths)-len(accepted),flush=True)
    families={}
    for i in range(len(paths)):families.setdefault(uf.find(i),[]).append(i)
    idmap={root:'LC25000:'+hashlib.sha256('\n'.join(paths[i].name for i in members).encode()).hexdigest()[:16]
           for root,members in families.items()}
    with (ROOT/'splits/lc_groups.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['source_image_path','original_label','group_id','group_size'])
        writer.writeheader()
        for i,p in enumerate(paths):writer.writerow({'source_image_path':p.relative_to(ROOT/'data').as_posix(),
            'original_label':labels[i],'group_id':idmap[uf.find(i)],'group_size':len(families[uf.find(i)])})
    with (out/'accepted_edges.csv').open('w',newline='',encoding='utf-8') as f:
        if accepted:
            writer=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for e in accepted for k in e)))
            writer.writeheader();writer.writerows(accepted)
    summary={'images':len(paths),'legacy_phash_groups':len(baseline),'verified_groups':len(families),
        'size_histogram':dict(Counter(len(v) for v in families.values())),
        'groups_per_class':dict(Counter(labels[v[0]] for v in families.values())),
        'verified_candidate_pairs_this_pass':verified,'accepted_edges':len(accepted),'config':config,
        'retrieval_representatives_per_group':args.representatives,
        'high_resolution_small_group_rescue':args.rescue_small or args.cnn_rescue_small,
        'candidate_stage':'cnn_small_group_rescue' if args.cnn_rescue_small else 'sift_refinement' if args.sift_refine else 'cached_geometric_verification' if args.verify_cached else 'cnn_and_phash',
        'candidate_cosine_used':.65 if args.cnn_rescue_small else config['candidate_cosine'],
        'identity_limit':'Reconstructed augmentation families, not patient identities; residual leakage remains possible.'}
    (ROOT/'results/grouping_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print('GROUPING_DONE',json.dumps(summary),flush=True)

if __name__=='__main__':main()
