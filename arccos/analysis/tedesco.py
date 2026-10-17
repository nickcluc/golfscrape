import json,glob,collections,statistics as st
from geo import *
H=load_holes(6878)
bag={c['clubId']:c for c in json.load(open('export/bag.json'))['clubs']}
def club(cid):
    c=bag.get(cid,{}); t=c.get('clubType')
    names={1:'Driver',2:'3W',34:'Hybrid/FW',35:'Paradym (FW)',26:'Takomo'}
    if t in names: return names[t]
    if t and t>=40: return f'{t}°'
    return f'Iron{t}' if t else '?'
holes=[]
for f in sorted(glob.glob('export/rounds/*.json')):
    d=json.load(open(f))
    if d['courseId']!=6878 or d.get('shouldIgnore')=='T': continue
    for h in d['holes'] or []:
        if not h or not h.get('shots') or h.get('shouldIgnore')=='T': continue
        hh=H.get((d['courseVersion'],h['holeId']))
        if not hh: continue
        sh=h['shots']; pin=(h.get('pinLat'),h.get('pinLong'))
        if not pin[0]: continue
        pens=sum(s.get('noOfPenalties') or 0 for s in sh)
        score=len(sh)+pens if h.get('scoreOverride') is None else h['scoreOverride']
        holes.append(dict(date=d['startTime'][:10],rid=d['roundId'],hole=h['holeId'],par=hh['par'],si=hh['si'],len=hh['tees'].get(d['teeId']),
            score=score,to_par=score-hh['par'],putts=h.get('putts'),gir=h['isGir']=='T',fw=h['isFairWay'],fwl=h['isFairWayLeft'],fwr=h['isFairWayRight'],
            pens=pens,tee_pen=sh[0].get('noOfPenalties') or 0,tee_club=club(sh[0]['clubId']),tee_dist=sh[0]['distance'],
            tee_end=lie(hh,sh[0]['endLat'],sh[0]['endLong']),shots=sh,pin=pin,hh=hh))
json.dump([{k:v for k,v in x.items() if k not in('shots','hh')} for x in holes],open('ted_holes.json','w'))
print(len(holes),'holes,',len({x['rid'] for x in holes}),'rounds', min(x['date'] for x in holes),max(x['date'] for x in holes))
