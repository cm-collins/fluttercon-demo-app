#!/usr/bin/env python3
"""Checks a deck: font sizes on the scale, text fits its box and margins, nothing collides.

usage (from this folder): python3 check_layout.py beyond-skia-dark.pptx
"""
import sys,re
from collections import Counter
from PIL import ImageFont
from pptx import Presentation
F='local/pptx/fonts/'
FACE={'Inter Tight SemiBold':'InterTight-600.ttf','Inter':'Inter-400.ttf','Inter Medium':'Inter-500.ttf','JetBrains Mono':'JetBrainsMono-400.ttf',None:'Inter-400.ttf'}
cache={}
def font(face,sz):
    k=(face,sz)
    if k not in cache: cache[k]=ImageFont.truetype(F+FACE.get(face,'Inter-400.ttf'),int(sz*4))
    return cache[k]
SCALE={16,20,24,28,36,56,72,112,160}
G=(1136+32)/12
GRID={72+k*G for k in range(13)}
SLACK=1.05   # PowerPoint and LibreOffice measure text slightly differently
def run_width(r,txt,title=False,sz=None):
    f=r.font; face=f.name or ('Inter Tight SemiBold' if title else 'Inter')
    s=sz or f.size.pt/0.75
    w=font(face,s).getlength(txt)/4
    spc=r._r.get_or_add_rPr().get('spc')
    if spc: w+=len(txt)*int(spc)/100/0.75
    return w
def para_lines(par,boxw,title):
    # greedy word wrap across runs
    toks=[]
    runs={id(r._r):r for r in par.runs}
    for el in par._p:
        tag=el.tag.split('}')[1]
        if tag=='br': toks.append((None,None))
        elif tag=='r':
            r=runs[id(el)]
            for t in re.findall(r'\S+\s*|\s+',r.text): toks.append((r,t))
    lines=1;cur=0;widest=0
    for r,t in toks:
        if r is None:
            widest=max(widest,cur);lines+=1;cur=0;continue
        w=run_width(r,t,title)*SLACK
        ws=run_width(r,t.rstrip(),title)*SLACK
        if cur+ws>boxw and cur>0: widest=max(widest,cur);lines+=1;cur=0
        cur+=w
    widest=max(widest,cur)
    return lines,widest
issues=[];sizes=Counter();lefts=Counter()
p=Presentation(sys.argv[1])
for n,s in enumerate(p.slides,1):
    rects=[]
    def visit(x,grp=False):
        if x.shape_type==6:
            for y in x.shapes: visit(y,True)
            return
        if getattr(x,'has_table',False) and x.has_table:
            tbl=x.table; wx=[c.width/9525 for c in tbl.columns]
            for i,row in enumerate(tbl.rows):
                for j,c in enumerate(row.cells):
                    for par in c.text_frame.paragraphs:
                        for r in par.runs:
                            z=round(r.font.size.pt/0.75,1); sizes[z]+=1
                            if z not in SCALE: issues.append((n,'size',z,r.text[:30]))
                        l,w=para_lines(par,wx[j]-8,False)
                        if l>1 and i>0: issues.append((n,'table cell wraps',l,c.text_frame.text[:30]))
                        if l>1 and i==0: issues.append((n,'table header wraps',l,c.text_frame.text[:30]))
            return
        if not getattr(x,'has_text_frame',False) or not x.has_text_frame or not x.text_frame.text.strip(): return
        tf=x.text_frame; L,T,Wd,H=[v/9525 for v in (x.left,x.top,x.width,x.height)]
        title=x==s.shapes.title
        total=0;wid=0;first=None
        for par in tf.paragraphs:
            maxs=0
            for r in par.runs:
                if r.font.size is None: continue
                z=round(r.font.size.pt/0.75,1); sizes[z]+=1; maxs=max(maxs,z); first=first or z
                if z not in SCALE: issues.append((n,'size',z,r.text[:30]))
            if not par.runs: continue
            inner=Wd-(20 if x.shape_type==1 else 0)
            l,w=para_lines(par,inner,title)
            sp=par.line_spacing if isinstance(par.line_spacing,float) else 1.0
            total+=l*maxs*1.21*sp; wid=max(wid,min(w,inner))
            if max(run_width(r,w0,title)*SLACK for r in par.runs for w0 in r.text.split() or [''])>inner: issues.append((n,'word wider than box',r.text[:30]))
            al=par.alignment
        name=x.name
        if not grp and x.shape_type!=1: 
            lefts[round(L,1)]+=1
        if total>H+6 and x.shape_type!=1: issues.append((n,'text taller than box',round(total),round(H),tf.text[:40]))
        if x.shape_type==1 and total>H: issues.append((n,'text taller than block',round(total),round(H),tf.text[:40]))
        top=T
        anchor=tf.vertical_anchor
        if anchor==3 or str(anchor).startswith('MIDDLE'): top=T+(H-total)/2
        bottom=top+total
        if name!='Tag' and bottom>648 and not title: issues.append((n,'below content line',round(bottom),tf.text[:40]))
        wid=wid/SLACK
        right=L+wid
        # alignment
        r_al=[pp.alignment for pp in tf.paragraphs][0]
        if r_al is not None and 'RIGHT' in str(r_al): rx0,rx1=L+Wd-wid,L+Wd
        elif r_al is not None and 'CENTER' in str(r_al): rx0,rx1=L+(Wd-wid)/2,L+(Wd+wid)/2
        else: rx0,rx1=L,L+wid
        if rx1>1208.5 and n not in (1,) : issues.append((n,'past right margin',round(rx1),tf.text[:40]))
        if rx0<71.5 and n!=1: issues.append((n,'past left margin',round(rx0),tf.text[:40]))
        if title and first and first==56:
            lines=sum(para_lines(pp,Wd,True)[0] for pp in tf.paragraphs)
            if lines>1: issues.append((n,'title wraps',lines,tf.text[:40]))
        if name=='Tag':
            lines=sum(para_lines(pp,Wd,False)[0] for pp in tf.paragraphs)
            if lines>1: issues.append((n,name+' wraps',lines,tf.text[:50]))
        if x.shape_type!=1: rects.append((rx0,top,rx1,bottom,tf.text[:28],grp))
    for x in s.shapes: visit(x)
    for i in range(len(rects)):
        for j in range(i+1,len(rects)):
            a,b=rects[i],rects[j]
            if min(a[2],b[2])-max(a[0],b[0])>2 and min(a[3],b[3])-max(a[1],b[1])>3:
                issues.append((n,'text collision',a[4],b[4]))
print('sizes used',sorted(sizes)); print('left edges',len(lefts),sorted(k for k in lefts if not any(abs(k-g)<1 for g in GRID)))
def words(sl):
    o=[]
    def w(shapes):
        for x in shapes:
            if x.shape_type==6: w(x.shapes)
            elif getattr(x,'has_text_frame',False) and x.has_text_frame and x.name not in('Code',): o.append(x.text_frame.text)
            elif getattr(x,'has_table',False) and x.has_table:
                o.extend(c.text_frame.text for r in x.table.rows for c in r.cells)
    w(sl.shapes)
    return len(' '.join(o).split())
print('words a slide, without code:',[words(s) for s in p.slides])
print('ISSUES',len(issues))
for i in issues: print(i)
