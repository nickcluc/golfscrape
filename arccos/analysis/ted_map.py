import json,glob,sys
sys.path.insert(0,'.')
exec(open('tedesco.py').read().split("json.dump(")[0])
KIND={1:'green',2:'bunker',3:'bunker',4:'water',5:'water',6:'tee',7:'fairway',8:'fairway',9:'trees'}
feats=[]
for f in sorted(glob.glob('export/holes/6878_4_*.json')):
    d=json.load(open(f))
    for i,x in enumerate(d['features']):
        k=KIND.get(x['featureId'])
        if not k: continue
        feats.append(dict(hole=d['holeId'],shape=i,arccos_type=x['featureId'],kind=k,path=' '.join(f"{c['latitude']:.6f},{c['longitude']:.6f}" for c in x['coordinates'])))
json.dump(feats,open('dash/ted_map_features.json','w'),separators=(',',':'))
H4={k[1]:v for k,v in H.items() if k[0]==4}
def endlie(hn,lat,lon):
    l=lie(H4[hn],lat,lon); ks=[KIND.get(t) for t in l]
    for k in ('green','water','bunker','fairway','tee','trees'):
        if k in ks: return k
    return 'rough'
import re
def cname(cid):
    c=bag.get(cid,{}); t=c.get('clubType')
    if t==1: return 'Driver'
    if t==12: return 'Putter'
    if t and t>=40: return f'{t}° wedge'
    m=re.sub(r'^(Callaway|Titleist|Mizuno|Takomo)\s+','',f"{c.get('clubMakeOther') or ''} {c.get('clubModelOther') or ''}".strip()).replace(' Other','') or 'Unknown'
    return f'{m} ({t})' if t else m
shots=[]
for x in holes:
    hh=H4[x['hole']]
    for i,s in enumerate(x['shots']):
        if s.get('endLat') is None: s=dict(s,endLat=x['pin'][0],endLong=x['pin'][1])
        if s.get('startLat') is None: continue
        on_green=1 in lie(hh,s['startLat'],s['startLong'])
        dpin=yd(s['startLat'],s['startLong'],*x['pin'])
        t='tee' if i==0 else 'putt' if on_green else 'short' if dpin<40 else 'approach'
        shots.append(dict(id=f"{x['rid']}-{x['hole']}-{s['shotId']}",date=x['date'],hole=x['hole'],shot=i+1,type=t,club=cname(s['clubId']),
            club_id=s['clubId'],distance_yd=round(s['distance']),to_pin_yd=round(dpin),start_lat=round(s['startLat'],6),start_lon=round(s['startLong'],6),
            end_lat=round(s['endLat'],6),end_lon=round(s['endLong'],6),finish=endlie(x['hole'],s['endLat'],s['endLong']),penalties=s.get('noOfPenalties') or 0,
            pin_lat=round(x['pin'][0],6),pin_lon=round(x['pin'][1],6),hole_to_par=x['to_par']))
json.dump(shots,open('dash/ted_map_shots.json','w'),separators=(',',':'))
import collections,os
print(len(feats),os.path.getsize('dash/ted_map_features.json'),len(shots),os.path.getsize('dash/ted_map_shots.json'))
print(collections.Counter(s['type'] for s in shots), collections.Counter(s['finish'] for s in shots if s['type']=='tee'))
print(collections.Counter(s['club'] for s in shots).most_common(30))
