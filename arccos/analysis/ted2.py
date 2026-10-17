import json,collections,statistics as st
exec(open('tedesco.py').read().split("json.dump(")[0])
m=lambda v: round(st.mean(v),1) if v else None
sd={c['clubId']:round(c['smartDistance']['distance']) for c in json.load(open('export/smart_distances.json'))['clubs'] if c.get('smartDistance')}
print('== Par 3 tee shots: hole length vs club smart distance ==')
for hn in (3,7,8,13):
    v=[x for x in holes if x['hole']==hn]; L=st.median([x['len'] for x in v if x['len']])
    s=[x['shots'][0] for x in v]
    gap=[ (sd.get(t['clubId'],0)) - yd(t['startLat'],t['startLong'],*x['pin']) for t,x in zip(s,v)]
    ends=[yd(t['endLat'],t['endLong'],*x['pin']) for t,x in zip(s,v)]
    from ted_analyze_helpers import bearing_err
    al=[bearing_err(t,x['pin']) for t,x in zip(s,v)]
    short=sum(a[0]< -5 for a in al if a)/len(al)
    print(f"H{hn} {L:.0f}yd: actual pin dist {m([yd(t['startLat'],t['startLong'],*x['pin']) for t,x in zip(s,v)])}yd, club smart dist minus pin dist avg {m(gap)}yd, finish short {short:.0%}, avg along {m([a[0] for a in al if a])}yd, green {sum(x['gir'] for x in v)/len(v):.0%}")
    byc=collections.defaultdict(list)
    for t,x,a in zip(s,v,al): byc[club(t['clubId'])].append((x['to_par'],a[0] if a else 0, 1 in lie(x['hh'],t['endLat'],t['endLong'])))
    for c,r in sorted(byc.items(),key=lambda kv:-len(kv[1])):
        if len(r)>=3: print(f"    {c:10} n={len(r):2} avg to par {m([q[0] for q in r]):+} along {m([q[1] for q in r]):+} on green {sum(q[2] for q in r)/len(r):.0%}")
print('\n== Approach: club smart distance vs actual pin distance (100-200yd, non-tee) ==')
from ted_analyze_helpers import bearing_err
gaps=[];
for x in holes:
    for i,t in enumerate(x['shots']):
        if i==0 and x['par']>3: continue
        d=yd(t['startLat'],t['startLong'],*x['pin'])
        if 100<=d<200 and t['clubId'] in sd and not 1 in lie(x['hh'],t['startLat'],t['startLong']):
            gaps.append((sd[t['clubId']]-d, bearing_err(t,x['pin'])[0]))
print('n',len(gaps),'avg (club smart distance - pin distance)',m([g[0] for g in gaps]),'yd; share where club rated shorter than pin',f"{sum(g[0]<0 for g in gaps)/len(gaps):.0%}")
print('\n== Worst holes detail ==')
for hn in (1,7,15,16):
    v=[x for x in holes if x['hole']==hn]
    sc=collections.Counter(min(x['to_par'],3) for x in v)
    tee=collections.Counter(('FW' if x['fw']=='T' else 'L' if x['fwl']=='T' else 'R' if x['fwr']=='T' else '-')+('/trees' if 9 in x['tee_end'] else '') for x in v)
    second=[yd(x['shots'][1]['startLat'],x['shots'][1]['startLong'],*x['pin']) for x in v if len(x['shots'])>1]
    print(f"H{hn} scores {dict(sorted(sc.items()))} tee {dict(tee)} 2nd-shot dist med {st.median(second):.0f} putts3+ {sum((x['putts'] or 0)>=3 for x in v)} pens {sum(x['pens'] for x in v)}")
    for lab,f in [('fw',lambda x:x['fw']=='T'),('L',lambda x:x['fwl']=='T'),('R',lambda x:x['fwr']=='T')]:
        q=[x['to_par'] for x in v if f(x)]
        if q: print('   after',lab,len(q),m(q))
print('\n== Short game: shots inside 40yd off green -> up&down ==')
ud=[]
for x in holes:
    sh=x['shots']
    for i,t in enumerate(sh):
        if 1 in lie(x['hh'],t['startLat'],t['startLong']): continue
        d=yd(t['startLat'],t['startLong'],*x['pin'])
        if d<40:
            rest=len(sh)-i + sum(s.get('noOfPenalties') or 0 for s in sh[i:])
            ud.append((d,rest, 3 in lie(x['hh'],t['startLat'],t['startLong'])))
            break
for a,b in [(0,10),(10,20),(20,40)]:
    v=[r for r in ud if a<=r[0]<b and not r[2]]
    print(f"{a}-{b}yd (not bunker) n={len(v)} up&down {sum(r[1]<=2 for r in v)/len(v):.0%} 3+ to hole out {sum(r[1]>=3 for r in v)/len(v):.0%} avg {m([r[1] for r in v])}")
v=[r for r in ud if r[2]]; print('bunker',len(v), f"{sum(r[1]<=2 for r in v)/max(1,len(v)):.0%}")
