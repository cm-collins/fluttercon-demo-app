const BG='#0b0b0c',PAPER='#f4f3ef',ASH='#aeada8',EMBER='#ff5c28',CYAN='#4fc3f7',CARD='#2a2b30',HAIR='#38383c',INK='#0b0b0c';
const HEAD='500 %px "Inter Display"',BODY='400 %px Inter',MID='500 %px Inter',MONO='400 %px "JetBrains Mono"';
const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x)),ease=x=>{x=clamp(x);return x*x*(3-2*x)},seg=(t,a,b)=>ease((t-a)/(b-a)),lerp=(a,b,p)=>a+(b-a)*p;
function tx(g,s,x,y,size,color=PAPER,font=BODY,align='left',alpha=1){g.save();g.globalAlpha=alpha;g.font=font.replace('%',size);g.letterSpacing=font===HEAD?(-.018*size)+'px':'0px';g.fillStyle=color;g.textAlign=align;g.textBaseline='alphabetic';g.fillText(s,x,y);g.restore();}
function rr(g,x,y,w,h,c,a=1){g.save();g.globalAlpha=a;g.fillStyle=c;g.fillRect(x,y,w,h);g.restore();}
function ln(g,x1,y1,x2,y2,c,w=1,dash){g.save();g.strokeStyle=c;g.lineWidth=w;if(dash)g.setLineDash(dash);g.beginPath();g.moveTo(x1,y1);g.lineTo(x2,y2);g.stroke();g.restore();}
function glowRect(g,x,y,w,h,c,b=18){g.save();g.shadowColor=c;g.shadowBlur=b;g.fillStyle=c;g.fillRect(x,y,w,h);g.restore();}
const S={};
// ---- A frame that misses the tick
S.frame={W:1280,H:456,dur:15.5,poster:13.2,draw(g,t){
  const X0=270,X1=1208,MS=50,k=(X1-X0)/MS,TICK=8.33;
  const A={label:'Target: about 4 ms UI, 4 ms raster',rate:'120 fps',ui:[...Array(6)].map((_,i)=>[i*TICK,4]),ra:[...Array(6)].map((_,i)=>[i*TICK+4,4]),col:CYAN,say:'Every tick shows a new frame.'};
  const B={label:'Measured: raster 28 ms',rate:'36 fps',ui:[[.78,12.72],[26.19,13.69]],ra:[[0,24.51],[24.55,29.55]],col:EMBER,say:'The screen shows the old frame again.'};
  const P=t<7.75?A:B,T0=t<7.75?0:7.75,p=clamp((t-T0-.4)/5.6),now=p*MS,fade=seg(t-T0,0,.3)*(1-seg(t-T0,7.3,7.7));
  g.save();g.globalAlpha=fade;
  tx(g,P.label,72,44,36,PAPER,HEAD);tx(g,P.rate,1208,44,36,P.col,HEAD,'right');
  for(let i=0;i<=6;i++){const x=X0+i*TICK*k;ln(g,x,70,x,344,'rgba(255,255,255,.14)',1.2);}
  tx(g,'8.3 ms',X0+TICK*k-8,68,20,ASH,BODY,'right');
  [['UI',84],['Raster',156],['Screen',254]].forEach(([s,y])=>tx(g,s,72,y+40,24,ASH,MID));
  const bars=(sp,y,c)=>{for(const [a,d] of sp){const e=Math.min(a+d,now);if(e>a){rr(g,X0+a*k,y,Math.max((e-a)*k-2,1),60,c);}}};
  bars(P.ui,84,'#6f6e6a');bars(P.ra,156,P.col);
  const done=P.ra.map(([a,d])=>a+d);
  for(let j=0;j<6;j++){const tick=j*TICK;if(now<tick)break;let shown=done.filter(e=>e<=tick+1e-6).length;let prev=done.filter(e=>e<=tick-TICK+1e-6).length;const fresh=(j>0&&shown>prev)||(j===0&&P===A);const x=X0+tick*k+2,w=TICK*k-6,a=seg(now,tick,tick+1);
    g.save();g.globalAlpha*=a;if(fresh){rr(g,x,254,w,86,CYAN);tx(g,'Frame '+(shown+1),x+w/2,306,24,INK,HEAD,'center');}else{rr(g,x,254,w,86,CARD);g.strokeStyle=EMBER;g.lineWidth=2.5;g.strokeRect(x+1,255,w-2,84);tx(g,'Frame '+(shown+1),x+w/2,306,24,EMBER,HEAD,'center');}g.restore();}
  ln(g,X0+now*k,66,X0+now*k,350,PAPER,2);
  tx(g,P.say,72,416,36,P.col,HEAD,'left',seg(t-T0,3.2,3.8));
  tx(g,'Slow motion',1208,416,20,ASH,BODY,'right');
  g.restore();
}};
// ---- The CPU records, the GPU executes
S.cmd={W:1280,H:456,dur:13,poster:6.3,draw(g,t){
  const LX=500,BX=650,BE=1208,S=(BE-BX)/9.2,Y={r:44,q:166,g:288},H=86;
  const list=['begin render pass','  bind pipeline','  bind vertex buffer','  bind uniforms','  draw','end render pass','submit, with a fence'];
  [['1.raster',Y.r],['queue',Y.q],['GPU',Y.g]].forEach(([s,y])=>{tx(g,s,LX,y+H/2+8,24,ASH,MONO);ln(g,LX,y+H+18,BE,y+H+18,HAIR,1);});
  ln(g,LX,24,BE,24,PAPER,1);
  // Frame 1 and 2 on each lane. Times in seconds.
  const fr=[{rec:[0,3.0],sub:3.0,gpu:[3.5,6.8],c:CYAN,n:'Frame 1'},{rec:[3.3,6.3],sub:6.3,gpu:[6.9,9.4],c:PAPER,n:'Frame 2'}];
  fr.forEach(f=>{const e=Math.min(t,f.rec[1]);if(e>f.rec[0]){rr(g,BX+f.rec[0]*S,Y.r,(e-f.rec[0])*S,H,f.c);tx(g,f.n,BX+f.rec[0]*S+14,Y.r+H/2+8,24,INK,HEAD);}
    const a=seg(t,f.sub,f.sub+.5);if(t>f.sub){const x=BX+f.rec[1]*S-6,y=lerp(Y.r+H-10,Y.q+20,a);glowRect(g,x,y,14,46,f.c,16);if(a>=1){const b=seg(t,f.gpu[0]-.2,f.gpu[0]);if(b>0&&b<1){const yy=lerp(Y.q+20,Y.g+20,b);glowRect(g,x+4,yy,14,46,f.c,16);}}}
    const ge=Math.min(t,f.gpu[1]);if(ge>f.gpu[0]){rr(g,BX+f.gpu[0]*S,Y.g,(ge-f.gpu[0])*S,H,f.c);tx(g,f.n,BX+f.gpu[0]*S+14,Y.g+H/2+8,24,INK,HEAD);}
    if(t>f.gpu[1]){const pf=seg(t,f.gpu[1],f.gpu[1]+.55),x=BX+f.gpu[1]*S,yy=lerp(Y.g,Y.r+H+2,pf);ln(g,x,Y.g,x,yy,f.c,2.5,[5,5]);if(pf<1){g.save();g.shadowColor=f.c;g.shadowBlur=12;g.fillStyle=f.c;g.beginPath();g.arc(x,yy,6,0,7);g.fill();g.restore();}tx(g,'fence: done',x>1150?x-12:x+12,Y.q+H/2+8,22,f.c,MONO,x>1150?'right':'left',seg(t,f.gpu[1],f.gpu[1]+.3)*(1-seg(t,f.gpu[1]+1.6,f.gpu[1]+2.1)));}
  });
  // the list being written
  const cur=t<3.15?fr[0]:fr[1],L0=cur.rec[0],prog=clamp((t-L0)/(cur.rec[1]-L0)),count=Math.ceil(prog*list.length);
  tx(g,'Command buffer',72,48,28,PAPER,HEAD);tx(g,cur.n,72,84,24,cur.c,MID);
  list.forEach((s,i)=>{if(i<count)tx(g,s,72,134+i*42,26,i===count-1?cur.c:PAPER,MONO);});
}};
// ---- A layer is a round trip
S.layer={W:1280,H:456,dur:19,poster:15.5,draw(g,t){
  const TX=72,TY=92,CW=62,CH=62,COLS=7,ROWS=4,MX=840,MW=368;
  const ph2=t>=7;const T=ph2?t-7:t;
  tx(g,ph2?'With one saveLayer':'One render pass',72,44,36,PAPER,HEAD);
  tx(g,'Tile memory, on the chip: fast',TX,TY+ROWS*CH+36,24,CYAN,MID);tx(g,'Main memory: slow',MX,TY+ROWS*CH+36,24,EMBER,MID);
  g.strokeStyle=EMBER;g.lineWidth=2;g.strokeRect(MX,TY,MW,ROWS*CH);
  let trips=0;const packet=(t0,dur,to,c,lab)=>{const p=clamp((T-t0)/dur);if(p>0&&p<1){const a=TX+COLS*CW+14,b=MX-14,x=to?lerp(a,b,ease(p)):lerp(b,a,ease(p)),y=TY+ROWS*CH/2;glowRect(g,x-34,y-26,68,52,c,24);tx(g,lab,x,y+7,20,INK,HEAD,'center');}if(p>0)trips++;};
  const tile=(i,j,c,a=1)=>rr(g,TX+i*CW+2,TY+j*CH+2,CW-4,CH-4,c,a);
  for(let j=0;j<ROWS;j++)for(let i=0;i<COLS;i++)tile(i,j,CARD);
  const fill=(a,b,c,fr=1)=>{const p=clamp((T-a)/(b-a))*COLS*ROWS*fr;let n=0;for(let j=0;j<ROWS;j++)for(let i=0;i<COLS;i++){if(n<p)tile(i,j,c);n++;}};
  const mem=(a,c,lab,row)=>{if(T>a){const y=TY+14+row*62;rr(g,MX+14,y,MW-28,50,c,seg(T,a,a+.3));tx(g,lab,MX+28,y+33,22,INK,HEAD,'left',seg(T,a,a+.3));}};
  if(!ph2){fill(.4,3,CYAN);packet(3.3,1.2,true,EMBER,'Store');mem(4.5,CYAN,'The finished frame',0);}
  else{
    if(T<1.6)fill(.3,1.3,CYAN,.55);else if(T<2.9)fill(.3,1.3,CYAN,.55);
    packet(1.7,1,true,EMBER,'Store');mem(2.7,CYAN,'Draws so far',0);
    if(T>=2.9&&T<6){fill(3,4.2,'#ffb547',.5);}
    packet(4.4,1,true,EMBER,'Store');mem(5.4,'#ffb547','The blurred layer',1);
    if(T>=6)fill(6.4,6.45,CYAN,.55);
    packet(6,.8,false,EMBER,'Load');
    if(T>=6.9)fill(6.9,7.7,PAPER,1);
    packet(8,1,true,EMBER,'Store');mem(9,PAPER,'The finished frame',2);
  }
  tx(g,'Trips to main memory',MX,44-8,22,ASH,BODY);tx(g,String(trips),MX+MW,44,44,EMBER,HEAD,'right');
}};
// ---- Keep what you can see
S.simplify={W:1280,H:456,dur:11,poster:7.2,init(){
  const COL=['#4fc3f7','#9b6bff','#3ddc97','#ffb547'];const mk=(dec)=>{const c=document.createElement('canvas');c.width=1872;c.height=684;const g=c.getContext('2d');g.scale(1.5,1.5);g.fillStyle='#0b0d14';g.fillRect(0,0,1280,456);g.lineJoin='round';const Y=(l,v)=>16+l*15+(1-v)*190;
    L.lines.forEach((s,l)=>{g.strokeStyle=COL[l%4];g.lineWidth=1.2;g.beginPath();if(dec){const d=L.dec[l];for(let i=0;i<d.length;i+=2){const x=d[i]/316*1248,y=Y(l,d[i+1]);i?g.lineTo(x,y):g.moveTo(x,y);}}else for(let k=0;k<s.length;k++){const x=k/s.length*1248,y=Y(l,s[k]);k?g.lineTo(x,y):g.moveTo(x,y);}g.stroke();});return c;};
  this.full=mk(false);this.dec=mk(true);
  const n=8000,PW=316,v=L.lines[0];let c0=0,bestE=1e9;for(let c=20;c<296;c++){const a=Math.floor(c/PW*n),b=Math.floor((c+1)/PW*n);let lo=1,hi=0;for(let k=a;k<=b;k++){lo=Math.min(lo,v[k]);hi=Math.max(hi,v[k]);}const e=Math.abs((hi-lo)*230-4.6);if(e<bestE){bestE=e;c0=c;}}
  const a=Math.floor(c0/PW*n),b=Math.floor((c0+1)/PW*n),pts=[];for(let k=a;k<=b;k++)pts.push([(k-a)/(b-a),v[k]]);this.pts=pts;
},draw(g,t){
  const p=clamp((t-1)/6),X=p*1280,Y0=0;
  g.drawImage(this.full,0,Y0,1280,456);
  g.save();g.beginPath();g.rect(0,0,X,456);g.clip();g.drawImage(this.dec,0,Y0,1280,456);g.restore();
  if(p>0&&p<1){ln(g,X,0,X,456,PAPER,2);}
  // the lens
  const LW=170,LH=270,LX=1208-LW,LY=60;rr(g,LX-16,LY-48,LW+32,LH+98,'rgba(11,11,12,.93)');tx(g,'One pixel column',LX+LW/2,LY-20,20,ASH,MID,'center');
  rr(g,LX,LY,LW,LH,'rgba(79,195,247,.10)');g.strokeStyle=CYAN;g.lineWidth=1.5;g.strokeRect(LX,LY,LW,LH);
  const lo=Math.min(...this.pts.map(q=>q[1])),hi=Math.max(...this.pts.map(q=>q[1]));const PX=q=>LX+14+q[0]*(LW-28),PY=q=>LY+14+(hi-q[1])/(hi-lo)*(LH-28);
  const iLo=this.pts.indexOf(this.pts.reduce((a,b)=>b[1]<a[1]?b:a)),iHi=this.pts.indexOf(this.pts.reduce((a,b)=>b[1]>a[1]?b:a));
  const q=seg(t,4.2,5.2);
  g.strokeStyle='rgba(255,122,76,'+(1-q)+')';g.lineWidth=2;g.beginPath();this.pts.forEach((pt,i)=>{i?g.lineTo(PX(pt),PY(pt)):g.moveTo(PX(pt),PY(pt))});g.stroke();
  this.pts.forEach((pt,i)=>{const keep=i===iLo||i===iHi;g.save();g.globalAlpha=keep?1:1-q;g.fillStyle=keep?EMBER:'#fff';g.beginPath();g.arc(PX(pt),PY(pt),keep?6:4,0,7);g.fill();g.restore();});
  if(q>0){const a=this.pts[Math.min(iLo,iHi)],b=this.pts[Math.max(iLo,iHi)];g.save();g.globalAlpha=q;g.strokeStyle=EMBER;g.lineWidth=2.5;g.beginPath();g.moveTo(PX(a),PY(a));g.lineTo(PX(b),PY(b));g.stroke();g.restore();}
  tx(g,q<.5?'25 points':'2 points',LX+LW/2,LY+LH+34,24,q<.5?PAPER:EMBER,HEAD,'center');
  const count=Math.round(lerp(129920,12032,p));
  rr(g,0,370,520,86,'rgba(11,11,12,.86)');tx(g,count.toLocaleString('en-US'),72,430,60,p<1?EMBER:CYAN,HEAD);tx(g,'path points',72+count.toLocaleString('en-US').length*33+6,430,24,ASH,MID);
}};
// ---- 480 trips or one
S.batch={W:1280,H:456,dur:13,poster:11,draw(g,t){
  const X0=72,X1=1208,N=60,SW=(X1-X0)/N,BASE=210,HM=150;
  const heat=(k)=>.5+.25*Math.sin(k/N*6*Math.PI)+.15*Math.sin(k/N*40*Math.PI);
  const mixc=(v)=>{const a=[155,107,255],b=[255,92,40];return `rgb(${a.map((x,i)=>Math.round(lerp(x,b[i],clamp(v)))).join(',')})`;};
  const ph2=t>=6.6,T=ph2?t-6.6:t;
  tx(g,ph2?'After: one draw':'Before: one draw per segment',X0,44,36,PAPER,HEAD);
  tx(g,ph2?'canvas.drawVertices(vertices, BlendMode.dst, paint);':'canvas.drawPath(segment, paint);',X0,274,28,PAPER,MONO);const lane=400;tx(g,'GPU commands',X0,lane-38,24,ASH,MID);ln(g,X0,lane+40,X1,lane+40,HAIR,1);
  const adv=ph2?1:clamp(T/5);
  for(let k=0;k<N;k++){const h=heat(k)*HM;const lit=ph2?T>.5:k<adv*N;rr(g,X0+k*SW,BASE-h,ph2?SW+.5:SW-3,h,lit?mixc(heat(k)):CARD);}
  if(!ph2){const shown=Math.floor(adv*N);for(let k=0;k<shown;k++){rr(g,X0+k*SW,lane-18,SW-3,46,CYAN);}
    if(adv<1){const k=shown,x=X0+k*SW,fr=(adv*N)%1;glowRect(g,x,lerp(BASE,lane-18,fr),SW-3,14,EMBER,10);}
    const c=Math.round(adv*480);tx(g,c+' draws',X1,44,48,EMBER,HEAD,'right');
  }else{const p=seg(T,.6,1.4);if(p>0){rr(g,X0,lane-18,X1-X0,46,CYAN,p);tx(g,'drawVertices: every segment, one call',X0+16,lane+13,24,INK,HEAD,'left',p);}
    tx(g,'1 draw',X1,44,48,CYAN,HEAD,'right',seg(T,.6,1.2));}
}};
// ---- What RepaintBoundary saves
S.repaint={W:1280,H:404,dur:12,poster:4.2,draw(g,t){
  const panels=[[72,'Without a boundary',false],[672,'With RepaintBoundary',true]],F=1.4,phase=(t%F)/F,flash=1-seg(phase,0,.55),frame=Math.floor(t/F);
  panels.forEach(([x,name,iso])=>{
    tx(g,name,x,44,36,iso?CYAN:PAPER,HEAD);
    const rows=[['Grid',84,'#3a3f4b'],['Lines',84,'#3a3f4b']];
    tx(g,'Dart records',x,104,24,ASH,MID);tx(g,'Raster draws',x+280,104,24,ASH,MID);
    const box=(bx,by,label,on,col)=>{rr(g,bx,by,232,110,CARD);if(on>0)rr(g,bx,by,232,110,col,on*.92);g.strokeStyle=HAIR;g.strokeRect(bx,by,232,110);tx(g,label,bx+116,by+62,28,on>.35?INK:PAPER,HEAD,'center');};
    box(x,126,'Grid',iso?0:flash,CYAN);box(x,248,'Lines',flash,CYAN);
    box(x+280,126,'Grid',flash,EMBER);box(x+280,248,'Lines',flash,EMBER);
    if(iso){tx(g,'Recorded once',x,392,24,CYAN,MID);tx(g,'Still drawn, every frame',x+280,392,24,EMBER,MID);}else{tx(g,'Every frame',x,392,24,PAPER,MID);tx(g,'Every frame',x+280,392,24,EMBER,MID);}
  });
  ln(g,640,20,640,396,HAIR,1);
}};
// ---- Five real seconds
S.frames={W:1280,H:372,dur:9,poster:7,draw(g,t){
  const SP=5040,k=1280/SP,U=3.0,now=clamp((t-.4)/5.04)*(SP+30),R=[[T.none,'Broken',EMBER,184,32],[T.all,'Fixed',CYAN,336,230]];
  R.forEach(([data,name,col,base,ly])=>{let n=0;
    for(const [a,d] of data){if(a+d>now)continue;n++;const h=Math.min(d,48)*U,over=d>8.33;rr(g,a*k,base-h,Math.max(d*k-.3,.6),h,over?EMBER:CYAN);}
    const by=base-8.33*U;ln(g,0,by,1280,by,'rgba(255,255,255,.8)',1,[4,5]);
    tx(g,name,72,ly,30,col,HEAD);tx(g,n+' frames',1208,ly,30,col,HEAD,'right');});
  tx(g,Math.min(now/1000,5).toFixed(1)+' s, real speed',640,364,22,ASH,MID,'center');
}};
// ---- 3D scenes
S.wall={W:1280,H:456,dur:6.2,poster:5,async init(){
  const THREE=await import('three');const {EffectComposer}=await import('three/addons/postprocessing/EffectComposer.js');const {RenderPass}=await import('three/addons/postprocessing/RenderPass.js');const {UnrealBloomPass}=await import('three/addons/postprocessing/UnrealBloomPass.js');const {OutputPass}=await import('three/addons/postprocessing/OutputPass.js');
  const W=1280,H=456,r=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});r.setSize(W,H,false);r.setPixelRatio(1.5);r.toneMapping=THREE.ACESFilmicToneMapping;r.shadowMap.enabled=true;r.shadowMap.type=THREE.PCFSoftShadowMap;
  const s=new THREE.Scene();s.background=new THREE.Color(0x0b0b0c);const span=T.skia_frame_ms,vw=span*1.1,c=new THREE.OrthographicCamera(-vw/2,vw/2,vw/2*H/W,-vw/2*H/W,-9000,9000);c.position.set(span*.06,span*.34,span*.9);c.lookAt(0,172,0);
  s.add(new THREE.HemisphereLight(0x8899bb,0x050506,.55));const sun=new THREE.DirectionalLight(0xffffff,2.6);sun.position.set(-span*.4,span*.9,span*.55);s.add(sun);
  const H0=230,D=70,ember=new THREE.MeshStandardMaterial({color:0xff5c28,emissive:0xff3d10,emissiveIntensity:.42,roughness:.5});this.blocks=[];
  for(const [t0,d] of T.skia_programs){const m=new THREE.Mesh(new THREE.BoxGeometry(Math.max(d-1.8,1),H0,D),ember);m.position.set(t0+d/2-span/2,H0/2,0);m.visible=false;s.add(m);this.blocks.push([t0/1000,m]);}
  const bud=new THREE.Mesh(new THREE.BoxGeometry(8.33,H0,D),new THREE.MeshStandardMaterial({color:0xffffff,emissive:0xffffff,emissiveIntensity:1.3}));bud.position.set(-span/2+4,H0/2,D*1.5);s.add(bud);
  const comp=new EffectComposer(r);comp.setPixelRatio(1.5);comp.setSize(W,H);comp.addPass(new RenderPass(s,c));comp.addPass(new UnrealBloomPass(new THREE.Vector2(W,H),.42,.75,.55));comp.addPass(new OutputPass());
  this.comp=comp;this.r=r;this.last=-1;
},draw(g,t){
  const clock=clamp(t-.5,0,1.82);let vis=0;for(const [a,m] of this.blocks){m.visible=a<=clock;if(m.visible)vis++;}
  if(vis!==this.last){this.comp.render();this.last=vis;}
  g.drawImage(this.r.domElement,0,0,1280,456);g.save();g.globalCompositeOperation='lighter';g.fillStyle='#0b0b0c';g.fillRect(0,0,1280,456);g.restore();
  tx(g,clock.toFixed(2)+' s',72,108,112,EMBER,HEAD);
  tx(g,vis+' of 118 shaders',560,76,36,PAPER,HEAD);tx(g,'Real speed. The app is frozen.',560,114,24,ASH,MID);
  tx(g,'White bar: one frame’s 8.3 ms budget, same scale',72,440,24,PAPER,MID);
}};
S.layers={W:816,H:720,dur:10.5,poster:4.2,async init(){
  const THREE=await import('three');const {EffectComposer}=await import('three/addons/postprocessing/EffectComposer.js');const {RenderPass}=await import('three/addons/postprocessing/RenderPass.js');const {UnrealBloomPass}=await import('three/addons/postprocessing/UnrealBloomPass.js');const {OutputPass}=await import('three/addons/postprocessing/OutputPass.js');
  const COLX=['#4fc3f7','#9b6bff','#3ddc97','#ffb547'],cv=document.createElement('canvas');cv.width=2048;cv.height=1280;const q=cv.getContext('2d');q.fillStyle='#0d0e14';q.fillRect(0,0,2048,1280);q.strokeStyle='rgba(255,255,255,.07)';q.lineWidth=2;for(let i=1;i<6;i++){q.beginPath();q.moveTo(i*2048/6,0);q.lineTo(i*2048/6,1280);q.stroke();q.beginPath();q.moveTo(0,i*1280/6);q.lineTo(2048,i*1280/6);q.stroke();}
  const Yf=(l,v)=>80+(l*80*.72)+(1-v)*1280*.28;L.lines.forEach((s,l)=>{q.strokeStyle=COLX[l%4];q.lineWidth=2.4;q.beginPath();for(let k=0;k<s.length;k+=2){const x=k/s.length*2048,y=Yf(l,s[k]);k?q.lineTo(x,y):q.moveTo(x,y);}q.stroke();});
  const W=816,H=720,r=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});r.setSize(W,H,false);r.setPixelRatio(1.5);r.toneMapping=THREE.ACESFilmicToneMapping;const s=new THREE.Scene();s.background=new THREE.Color(0x0b0b0c);const c=new THREE.PerspectiveCamera(32,W/H,1,6000);c.position.set(420,800,1340);c.lookAt(0,170,-20);
  const tex=new THREE.CanvasTexture(cv);tex.colorSpace=THREE.SRGBColorSpace;tex.anisotropy=8;const PW=860,PH=PW*1280/2048;const base=new THREE.Mesh(new THREE.PlaneGeometry(PW,PH),new THREE.MeshBasicMaterial({map:tex}));base.rotation.x=-Math.PI/2;s.add(base);
  this.items=[];const n=8000;for(let dot=0;dot<64;dot++){const line=dot%16,slot=Math.floor(dot/16),f=((slot+.5)/4+line*.013)%1,kk=Math.floor(f*n)%n,v=L.lines[line][kk],x=f*PW-PW/2,z=Yf(line,v)/1280*PH-PH/2,h=70+((dot*37)%64)*5.1,sz=46;
    const pm=new THREE.MeshBasicMaterial({color:0xff5c28,transparent:true,opacity:.16,side:THREE.DoubleSide}),q2=new THREE.Mesh(new THREE.PlaneGeometry(sz,sz),pm);q2.rotation.x=-Math.PI/2;s.add(q2);
    const em=new THREE.LineBasicMaterial({color:0xffa07a,transparent:true}),qe=new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.PlaneGeometry(sz,sz)),em);qe.rotation.x=-Math.PI/2;s.add(qe);
    const dm=new THREE.MeshBasicMaterial({color:0xffe2d6,side:THREE.DoubleSide,transparent:true}),d2=new THREE.Mesh(new THREE.CircleGeometry(7,20),dm);d2.rotation.x=-Math.PI/2;s.add(d2);
    const lm=new THREE.LineBasicMaterial({color:0xff5c28,transparent:true,opacity:.34}),ll=new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0,0,0),new THREE.Vector3(0,1,0)]),lm);ll.position.set(x,1,z);s.add(ll);
    this.items.push({x,z,h,q2,qe,d2,ll,pm,em,dm,lm,dot});}
  const comp=new EffectComposer(r);comp.setPixelRatio(1.5);comp.setSize(W,H);comp.addPass(new RenderPass(s,c));comp.addPass(new UnrealBloomPass(new THREE.Vector2(W,H),.5,.6,.2));comp.addPass(new OutputPass());this.comp=comp;this.r=r;
},draw(g,t){
  for(const it of this.items){const d=it.dot/64*1.2,up=seg(t,.3+d,1.6+d),down=seg(t,6.2+d*.5,7.6+d*.5),hh=1+(it.h-1)*up*(1-down),vis=(1-down*.92);
    for(const m of [it.q2,it.qe,it.d2]){m.position.set(it.x,hh,it.z);}it.d2.position.y=hh+.5;it.ll.scale.y=Math.max(hh,1);
    it.pm.opacity=.16*vis*up;it.em.opacity=vis*up;it.dm.opacity=Math.max(vis*up,.0)+0;it.lm.opacity=.34*vis*up;}
  this.comp.render();g.drawImage(this.r.domElement,0,0,816,720);g.save();g.globalCompositeOperation='lighter';g.fillStyle='#0b0b0c';g.fillRect(0,0,816,720);g.restore();
}};
const q=new URLSearchParams(location.search).get('scene'),sc=S[q],cv=document.getElementById('c'),ctx=cv.getContext('2d'),SCALE=1.5;
cv.width=Math.round(sc.W*SCALE/2)*2;cv.height=Math.round(sc.H*SCALE/2)*2;
window.ready=(async()=>{await document.fonts.load('500 40px "Inter Display"');await document.fonts.load('400 24px Inter');await document.fonts.load('500 24px Inter');await document.fonts.load('400 24px "JetBrains Mono"');if(sc.init)await sc.init();return JSON.stringify({w:cv.width,h:cv.height,dur:sc.dur,poster:sc.poster});})();
window.render=(t)=>{ctx.setTransform(SCALE,0,0,SCALE,0,0);ctx.globalAlpha=1;ctx.fillStyle=BG;ctx.fillRect(0,0,sc.W,sc.H);sc.draw(ctx,t);const f=Math.min(seg(t,0,.25),1-seg(t,sc.dur-.35,sc.dur));if(f<1){ctx.fillStyle=BG;ctx.globalAlpha=1-f;ctx.fillRect(0,0,sc.W,sc.H);ctx.globalAlpha=1;}return cv.toDataURL('image/jpeg',.97);};
