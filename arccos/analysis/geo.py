import json,glob,math
def pip(lat,lon,poly):
    inside=False; n=len(poly); j=n-1
    for i in range(n):
        yi,xi=poly[i]; yj,xj=poly[j]
        if ((yi>lat)!=(yj>lat)) and (lon < (xj-xi)*(lat-yi)/(yj-yi+1e-15)+xi): inside=not inside
        j=i
    return inside
def yd(a1,o1,a2,o2):
    R=6371000; p=math.radians
    x=(p(o2)-p(o1))*math.cos(p((a1+a2)/2)); y=p(a2)-p(a1)
    return math.hypot(x,y)*R*1.09361
def load_holes(cid):
    H={}
    for f in glob.glob(f'export/holes/{cid}_*.json'):
        d=json.load(open(f))
        feats=[(x['featureId'],[(c['latitude'],c['longitude']) for c in x['coordinates']]) for x in d['features']]
        H[(d['courseVersion'],d['holeId'])]=dict(par=d['mensPar'],si=d['mensHandicap'],tees={t['teeId']:t['distance'] for t in d['holeTees']},feats=feats)
    return H
def lie(H,lat,lon):
    return sorted({fid for fid,poly in H['feats'] if pip(lat,lon,poly)})
