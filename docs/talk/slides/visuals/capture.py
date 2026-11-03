#!/usr/bin/env python3
"""Renders the animated explainers: draws each frame in headless Chrome and encodes it to H.264.

usage: capture.py OUT_DIR [scene ...] [--stills]      (needs websocket-client and imageio-ffmpeg)
"""
import base64,json,os,socket,subprocess,sys,tempfile,time,urllib.request
import imageio_ffmpeg,websocket
HERE=os.path.dirname(os.path.abspath(__file__))
args=[a for a in sys.argv[1:] if not a.startswith('--')];OUT=args[0];os.makedirs(OUT,exist_ok=True)
STILLS='--stills' in sys.argv
ALL=['frame','wall','cmd','layer','simplify','batch','repaint','frames','layers'];scenes=args[1:] or ALL
s=socket.socket();s.bind(('127.0.0.1',0));PORT=s.getsockname()[1];s.close()
prof=tempfile.mkdtemp(prefix='cap-')
ch=subprocess.Popen(['google-chrome','--headless=new','--use-angle=swiftshader',f'--remote-debugging-port={PORT}',f'--user-data-dir={prof}','--window-size=1280,720','about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    for _ in range(60):
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json/version',timeout=1);break
        except Exception: time.sleep(.5)
    for name in scenes:
        req=urllib.request.Request(f'http://127.0.0.1:{PORT}/json/new?about:blank',method='PUT')
        tab=json.load(urllib.request.urlopen(req))
        ws=websocket.create_connection(tab['webSocketDebuggerUrl'],max_size=None,timeout=300,suppress_origin=True)
        n=[0]
        def call(m,**p):
            n[0]+=1;ws.send(json.dumps({'id':n[0],'method':m,'params':p}))
            while True:
                r=json.loads(ws.recv())
                if r.get('id')==n[0]:
                    if 'error' in r: raise RuntimeError(r['error'])
                    return r['result']
        def ev(x,aw=False):
            r=call('Runtime.evaluate',expression=x,awaitPromise=aw,returnByValue=True)
            if 'exceptionDetails' in r: raise RuntimeError(str(r['exceptionDetails'])[:600])
            return r['result'].get('value')
        call('Page.enable');call('Page.navigate',url=f'file://{HERE}/anim.html?scene={name}')
        for _ in range(100):
            time.sleep(.2)
            if ev('typeof window.ready')=='object':break
        info=json.loads(ev('window.ready',True));dur,w,h=info['dur'],info['w'],info['h']
        grab=lambda t:base64.b64decode(ev(f'window.render({t})').split(',')[1])
        if STILLS:
            ts=[dur*.25,dur*.5,info['poster'],dur*.8]
            for i,t in enumerate(ts):
                open(f'{OUT}/{name}-{i}.jpg','wb').write(grab(t))
            print(name,'stills');ws.close();continue
        path=f'{OUT}/{name}.mp4'
        ff=subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-loglevel','error','-f','image2pipe','-c:v','mjpeg','-r','30','-i','-','-an','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-vf','scale=out_color_matrix=bt709:out_range=tv','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-movflags','+faststart',path],stdin=subprocess.PIPE)
        t0=time.time();N=int(dur*30)
        for i in range(N):
            ff.stdin.write(grab(i/30))
        ff.stdin.close();ff.wait()
        open(f'{OUT}/{name}.jpg','wb').write(grab(info['poster']))
        print(name,N,'frames',round(time.time()-t0),'s',os.path.getsize(path)//1024,'KB',flush=True)
        ws.close()
finally:
    ch.terminate()
