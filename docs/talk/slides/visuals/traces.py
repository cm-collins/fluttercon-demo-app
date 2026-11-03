import re,json,os
C=os.path.expanduser('~/fluttercon-captures/2026-10-31-infinix-x6873/traces/perfetto-system/')
pat=re.compile(r'^\s*(.+?)-(\d+)\s+\(\s*(\d+|-+)\)\s+\[\d+\]\s+\S+\s+(\d+\.\d+):\s+tracing_mark_write:\s+([BE])\|?(\d*)\|?(.*)$')
def slices(f,thread):
    st=[];out=[]
    for l in open(C+f,errors='ignore'):
        if 'tracing_mark_write' not in l: continue
        m=pat.match(l)
        if not m or not m[1].strip().endswith(thread): continue
        t=float(m[4])
        if m[5]=='B': st.append((m[7].strip(),t))
        elif st:
            n,t0=st.pop(); out.append((n,t0,t))
    return out
res={}
for key,f in (('none','thrash-trace-none.txt'),('half','thrash-trace-simplifyPaths+batchDraws.txt'),('all','thrash-trace-all.txt')):
    s=slices(f,'1.raster')
    d=[(a,b) for n,a,b in s if n.startswith('GPURasterizer::Draw')]
    t0=d[0][0]
    res[key]=[[round((a-t0)*1000,2),round((b-a)*1000,2)] for a,b in d]
    print(key,len(d),'span',round(d[-1][1]-t0,2),'p50',sorted(x[1] for x in res[key])[len(d)//2])
s=slices('skia-144.txt','1.raster')
fr=[(a,b) for n,a,b in s if n.startswith('GPURasterizer::Draw')]
big=max(fr,key=lambda x:x[1]-x[0])
prog=[(n,a,b) for n,a,b in s if 'GrGLProgramBuilder::finalize' in n and big[0]<=a<=big[1]]
res['skia_frame_ms']=round((big[1]-big[0])*1000,1)
res['skia_programs']=[[round((a-big[0])*1000,2),round((b-a)*1000,2)] for n,a,b in prog]
print('skia frame',res['skia_frame_ms'],'programs',len(prog),'sum',round(sum(p[1] for p in res['skia_programs']),1))
s=slices('impeller-144.txt','1.raster')
fr=[(a,b) for n,a,b in s if n.startswith('GPURasterizer::Draw')]
big=max(fr,key=lambda x:x[1]-x[0])
prog=[(n,a,b) for n,a,b in s if 'PipelineVK::Create' in n and big[0]<=a<=big[1]]
res['imp_frame_ms']=round((big[1]-big[0])*1000,1)
res['imp_pipelines']=[[round((a-big[0])*1000,2),round((b-a)*1000,2)] for n,a,b in prog]
print('impeller frame',res['imp_frame_ms'],'pipelines',len(prog),'sum',round(sum(p[1] for p in res['imp_pipelines']),1))
json.dump(res,open('traces.json','w'))
