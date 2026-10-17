import json,collections,statistics as st,csv
exec(open('tedesco.py').read().split("json.dump(")[0])
from ted_analyze_helpers import bearing_err
r1=lambda v: round(v,1)
pct=lambda a,b: round(100*a/b,1) if b else None
def w(name,rows):
    with open(f'dash/{name}.csv','w',newline='') as f:
        c=csv.DictWriter(f,fieldnames=list(rows[0])); c.writeheader(); c.writerows(rows)
    print(name,len(rows)); print(open(f'dash/{name}.csv').read()[:700])
sd={c['clubId']:round(c['smartDistance']['distance']) for c in json.load(open('export/smart_distances.json'))['clubs'] if c.get('smartDistance')}
# per hole
by=collections.defaultdict(list)
for x in holes: by[x['hole']].append(x)
rows=[]
for k in sorted(by):
    v=by[k]; tp=[x['to_par'] for x in v]; f=[x for x in v if x['par']>3 and x['fw'] in('T','F')]
    rows.append(dict(hole=k,par=v[0]['par'],yards=round(st.median([x['len'] for x in v if x['len']]) * 1.0936133)  # Arccos tee distances are metres,played=len(v),avg_to_par=round(st.mean(tp),2),
        par_or_better_pct=pct(sum(t<=0 for t in tp),len(v)),double_plus_pct=pct(sum(t>=2 for t in tp),len(v)),
        fairway_pct=pct(sum(x['fw']=='T' for x in f),len(f)) if f else None,gir_pct=pct(sum(x['gir'] for x in v),len(v)),
        three_putt_pct=pct(sum((x['putts'] or 0)>=3 for x in v),len(v)),penalties=sum(x['pens'] for x in v)))
w('ted_holes',rows)
# approaches
aps=json.load(open('ted_approaches.json'))
rows=[]
for a,b in [(30,75),(75,100),(100,125),(125,150),(150,175),(175,200),(200,250)]:
    v=[x for x in aps if a<=x['d']<b]; miss=[x for x in v if not x['on']]
    rows.append(dict(distance=f'{a}-{b}',from_yd=a,shots=len(v),green_pct=pct(sum(x['on'] for x in v),len(v)),median_left_yd=round(st.median([x['prox'] for x in v])),
        avg_finish_vs_pin_yd=r1(st.mean([x['along'] for x in v])),misses=len(miss),short_of_misses_pct=pct(sum(x['along']<-5 for x in miss),len(miss)),long_of_misses_pct=pct(sum(x['along']>5 for x in miss),len(miss))))
w('ted_approach',rows)
# 100-200 summary
v=[x for x in aps if 100<=x['d']<200]; miss=[x for x in v if not x['on']]
summ=dict(window='100-200',shots=len(v),misses=len(miss),short_of_misses_pct=pct(sum(x['along']<-5 for x in miss),len(miss)),avg_finish_vs_pin_yd=r1(st.mean([x['along'] for x in v])))
# par 3s
rows=[]
for hn in sorted({x['hole'] for x in holes if x['par']==3}):
    v=[x for x in holes if x['hole']==hn]; s=[x['shots'][0] for x in v]
    pin=[yd(t['startLat'],t['startLong'],*x['pin']) for t,x in zip(s,v)]
    gap=[sd.get(t['clubId'],0)-p for t,p in zip(s,pin) if t['clubId'] in sd]
    al=[bearing_err(t,x['pin'])[0] for t,x in zip(s,v)]
    rows.append(dict(hole=hn,scorecard_yd=round(st.median([x['len'] for x in v if x['len']]) * 1.0936133),avg_pin_yd=round(st.mean(pin)),club_vs_pin_yd=r1(st.mean(gap)),
        avg_finish_vs_pin_yd=r1(st.mean(al)),finish_short_pct=pct(sum(a<-5 for a in al),len(al)),gir_pct=pct(sum(x['gir'] for x in v),len(v)),avg_to_par=round(st.mean([x['to_par'] for x in v]),2)))
w('ted_par3',rows)
# short game
ud=[]
for x in holes:
    sh=x['shots']
    for i,t in enumerate(sh):
        if 1 in lie(x['hh'],t['startLat'],t['startLong']): continue
        d=yd(t['startLat'],t['startLong'],*x['pin'])
        if d<40:
            ud.append((d,len(sh)-i+sum(s.get('noOfPenalties') or 0 for s in sh[i:]),3 in lie(x['hh'],t['startLat'],t['startLong']))); break
rows=[]
for lab,f in [('0-10 yd',lambda r:r[0]<10 and not r[2]),('10-20 yd',lambda r:10<=r[0]<20 and not r[2]),('20-40 yd',lambda r:20<=r[0]<40 and not r[2]),('Bunker',lambda r:r[2])]:
    v=[r for r in ud if f(r)]
    rows.append(dict(spot=lab,attempts=len(v),up_and_down_pct=pct(sum(r[1]<=2 for r in v),len(v)),avg_strokes_to_hole_out=round(st.mean([r[1] for r in v]),2)))
w('ted_shortgame',rows)
# tee & par5 & doubles summary rows
p4=[x for x in holes if x['par']==4]
tee=[]
for c in ['Driver','3W','Hybrid/FW']:
    v=[x for x in p4 if x['tee_club']==c]
    tee.append(dict(key='tee_'+c,label=c,n=len(v),avg_to_par=round(st.mean([x['to_par'] for x in v]),2),fairway_pct=pct(sum(x['fw']=='T' for x in v),len(v)),penalty_pct=pct(sum(x['tee_pen']>0 for x in v),len(v))))
fw=[x['to_par'] for x in holes if x['par']>3 and x['fw']=='T']; ms=[x['to_par'] for x in holes if x['par']>3 and (x['fwl']=='T' or x['fwr']=='T')]
p5=collections.defaultdict(list)
for x in holes:
    if x['par']==5 and len(x['shots'])>1:
        s=x['shots'][1]; d=yd(s['startLat'],s['startLong'],*x['pin'])
        if d<240: p5['go' if s['distance']>=0.8*d else 'layup'].append(x['to_par'])
dbl=[x for x in holes if x['to_par']>=2]
facts=tee+[
 dict(key='fairway_hit',label='Par 4/5 after hitting the fairway',n=len(fw),avg_to_par=round(st.mean(fw),2),fairway_pct=None,penalty_pct=None),
 dict(key='fairway_missed',label='Par 4/5 after missing the fairway',n=len(ms),avg_to_par=round(st.mean(ms),2),fairway_pct=None,penalty_pct=None),
 dict(key='par5_go',label='Par 5, went for the green from inside 240',n=len(p5['go']),avg_to_par=round(st.mean(p5['go']),2),fairway_pct=None,penalty_pct=None),
 dict(key='par5_layup',label='Par 5, laid up from inside 240',n=len(p5['layup']),avg_to_par=round(st.mean(p5['layup']),2),fairway_pct=None,penalty_pct=None),
]
w('ted_facts',facts)
tot=sum(x['to_par'] for x in holes)
w('ted_summary',[dict(rounds=len({x['rid'] for x in holes}),holes=len(holes),first=min(x['date'] for x in holes),last=max(x['date'] for x in holes),
   double_plus_holes=len(dbl),double_plus_pct=pct(len(dbl),len(holes)),strokes_over_par=tot,strokes_from_double_plus=sum(x['to_par'] for x in dbl),
   double_plus_share_pct=pct(sum(x['to_par'] for x in dbl),tot),approach_shots_100_200=summ['shots'],approach_misses_100_200=summ['misses'],
   approach_short_of_misses_pct=summ['short_of_misses_pct'],approach_avg_finish_yd=summ['avg_finish_vs_pin_yd'])])
