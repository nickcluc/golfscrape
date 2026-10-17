import json,urllib.request,urllib.parse,time,os,glob
a=json.load(open('auth.json')); tok=urllib.parse.unquote(a['access_token'])
need=set()
for f in glob.glob('export/rounds/*.json'):
    d=json.load(open(f))
    if d.get('shouldIgnore')=='T': continue
    for h in d.get('holes') or []:
        if h and d['courseId']==6878: need.add((d['courseId'],d['courseVersion'],h['holeId']))
os.makedirs('export/holes',exist_ok=True)
print(len(need),'holes needed',flush=True)
done=0
for c,v,h in sorted(need):
    p=f'export/holes/{c}_{v}_{h}.json'
    if os.path.exists(p): continue
    try:
        r=urllib.request.Request(f'https://api.arccosgolf.com/courses/{c}/holes/{h}?courseVersion={v}',headers={'Authorization':'Bearer '+tok})
        d=json.load(urllib.request.urlopen(r,timeout=30)); d.pop('elevations',None)
        json.dump(d,open(p,'w'))
    except Exception as e: print(c,v,h,e,flush=True)
    done+=1
    if done%50==0: print(done,flush=True)
    time.sleep(0.25)
print('done',len(glob.glob('export/holes/*.json')))
