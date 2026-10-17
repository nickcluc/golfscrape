import json,collections,statistics as st,math
exec(open('tedesco.py').read().split("json.dump(")[0])
m=lambda v: round(st.mean(v),2) if v else None
print('\n== By hole (avg to par, dist) ==')
by=collections.defaultdict(list)
for x in holes: by[x['hole']].append(x)
for k in sorted(by):
    v=by[k]; tp=[x['to_par'] for x in v]
    dbl=sum(t>=2 for t in tp)/len(tp); par_or_better=sum(t<=0 for t in tp)/len(tp)
    tc=collections.Counter(x['tee_club'] for x in v).most_common(3)
    fwv=[x for x in v if x['par']>3 and x['fw'] in('T','F')]
    print(f"H{k:2} par{v[0]['par']} si{v[0]['si']:2} {round(st.median([x['len'] for x in v if x['len']]))}yd n={len(v):2} avg {m(tp):+.2f} par-or-better {par_or_better:.0%} dbl+ {dbl:.0%} pens {sum(x['pens'] for x in v)} fw {sum(x['fw']=='T' for x in fwv)}/{len(fwv)} L{sum(x['fwl']=='T' for x in fwv)} R{sum(x['fwr']=='T' for x in fwv)} gir {sum(x['gir'] for x in v)/len(v):.0%} putts {m([x['putts'] for x in v if x['putts'] is not None])} tee {tc}")
print('\n== Tee club on par 4/5 ==')
for par in (4,5):
    g=collections.defaultdict(list)
    for x in holes:
        if x['par']==par: g[x['tee_club']].append(x)
    for c,v in sorted(g.items(),key=lambda kv:-len(kv[1])):
        if len(v)<5: continue
        print(f"par{par} {c:12} n={len(v):3} avg {m([x['to_par'] for x in v]):+.2f} fw {sum(x['fw']=='T' for x in v)/len(v):.0%} tee-pen {sum(x['tee_pen']>0 for x in v)/len(v):.0%} trees {sum(9 in x['tee_end'] for x in v)/len(v):.0%} dist {m([x['tee_dist'] for x in v])}")
print('\n== Driver vs other per par-4/5 hole ==')
for k in sorted(by):
    v=[x for x in by[k] if x['par']>3]
    if not v: continue
    d=[x['to_par'] for x in v if x['tee_club']=='Driver']; o=[x['to_par'] for x in v if x['tee_club']!='Driver']
    if len(d)>=3 and len(o)>=3: print(f"H{k} driver {m(d):+.2f} (n{len(d)}) other {m(o):+.2f} (n{len(o)})")
print('\n== Fairway vs miss: avg to par on par 4/5 ==')
for lab,f in [('fairway',lambda x:x['fw']=='T'),('miss left',lambda x:x['fwl']=='T'),('miss right',lambda x:x['fwr']=='T')]:
    v=[x['to_par'] for x in holes if x['par']>3 and f(x)]; print(lab,len(v),m(v))
# Approaches: first shot that ends on/near green from >30yd... define approach = shot starting 30-250yd from pin, not on green
print('\n== Approach by start distance ==')
def bearing_err(s,pin):
    # decompose end-pin vector relative to start->pin line
    sy,sx=s['startLat'],s['startLong']; ey,ex=s['endLat'],s['endLong']; py,px=pin
    k=math.cos(math.radians(py))
    ax,ay=(px-sx)*k,(py-sy); bx,by_=(ex-sx)*k,(ey-sy)
    L=math.hypot(ax,ay); 
    if L==0: return None
    ux,uy=ax/L,ay/L
    along=(bx*ux+by_*uy)-L; side=bx*uy-by_*ux  # side>0 => right of line
    f=111320*1.09361
    return along*f, side*f
buckets=[(30,75),(75,100),(100,125),(125,150),(150,175),(175,200),(200,250)]
aps=[]
for x in holes:
    hh=x['hh']
    for i,s in enumerate(x['shots']):
        if 1 in lie(hh,s['startLat'],s['startLong']): continue
        dpin=yd(s['startLat'],s['startLong'],*x['pin'])
        if not 30<=dpin<250: continue
        e=bearing_err(s,x['pin'])
        if not e: continue
        on=1 in lie(hh,s['endLat'],s['endLong'])
        start_lie='fairway' if 7 in lie(hh,s['startLat'],s['startLong']) else ('tee' if i==0 else 'other')
        aps.append(dict(d=dpin,along=e[0],side=e[1],on=on,prox=yd(s['endLat'],s['endLong'],*x['pin']),club=club(s['clubId']),lie=start_lie,hole=x['hole'],pens=s.get('noOfPenalties') or 0))
for a,b in buckets:
    v=[x for x in aps if a<=x['d']<b]
    if not v: continue
    miss=[x for x in v if not x['on']]
    print(f"{a}-{b}yd n={len(v):3} green {sum(x['on'] for x in v)/len(v):.0%} prox med {st.median([x['prox'] for x in v]):.0f}yd | misses: short {sum(x['along']<-5 for x in miss)/max(1,len(miss)):.0%} long {sum(x['along']>5 for x in miss)/max(1,len(miss)):.0%} left {sum(x['side']<-5 for x in miss)/max(1,len(miss)):.0%} right {sum(x['side']>5 for x in miss)/max(1,len(miss)):.0%} | avg along {m([x['along'] for x in v]):+.1f} side {m([x['side'] for x in v]):+.1f}")
for l in ('fairway','other'):
    v=[x for x in aps if x['lie']==l and 100<=x['d']<175]; print(l,'100-175', len(v), f"green {sum(x['on'] for x in v)/max(1,len(v)):.0%}")
json.dump(aps,open('ted_approaches.json','w'))
print('\n== Doubles+: what happened ==')
dbl=[x for x in holes if x['to_par']>=2]
c=collections.Counter()
for x in dbl:
    hh=x['hh']; sh=x['shots']
    on_green=[i for i,s in enumerate(sh) if 1 in lie(hh,s['startLat'],s['startLong'])]
    putts=len(on_green)
    around=[s for s in sh if 1 not in lie(hh,s['startLat'],s['startLong']) and yd(s['startLat'],s['startLong'],*x['pin'])<30]
    tags=[]
    if x['pens']: tags.append('penalty')
    if putts>=3: tags.append('3-putt')
    if len(around)>=2: tags.append('2+ shots inside 30yd')
    if x['par']>3 and (9 in x['tee_end'] ): tags.append('tee shot in trees')
    if not tags: tags.append('other')
    for t in tags: c[t]+=1
print(len(dbl),'double-bogey-or-worse holes of',len(holes), c.most_common())
print('strokes over par from doubles+:', sum(x['to_par'] for x in dbl), 'of total', sum(x['to_par'] for x in holes))
print('\n== Par 5 second shots ==')
for x in [x for x in holes if x['par']==5]:
    pass
p5=[x for x in holes if x['par']==5]
for x in p5[:0]: pass
sec=collections.Counter()
res=collections.defaultdict(list)
for x in p5:
    if len(x['shots'])<2: continue
    s=x['shots'][1]; d=yd(s['startLat'],s['startLong'],*x['pin'])
    go = s['distance']>=0.8*d
    key=('go' if go else 'layup')+(' <240' if d<240 else ' 240+')
    res[key].append(x['to_par'])
for k,v in res.items(): print(k,len(v),m(v))
