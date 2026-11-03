"""The art on the closing slide: the demo's real chart, squeezed into a dim band clear of every word."""
import os
import numpy as np
from PIL import Image

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'local', 'visuals')
src = Image.open(os.path.join(V, 'chart-full.jpg')).convert('RGB')
W, H = src.size
top, bottom = int(H * .725), int(H * .9)
band = np.asarray(src.crop((0, int(H * .08), W, int(H * .92))).resize((W, bottom - top), Image.LANCZOS)).astype(float)
bg = np.array([11, 11, 12.])
out = np.full((H, W, 3), bg)
y = np.linspace(0, 1, bottom - top)[:, None, None]
out[top:bottom] = bg + (band - bg) * .55 * np.clip(y / .16, 0, 1) * np.clip((1 - y) / .16, 0, 1)
Image.fromarray(out.clip(0, 255).astype('uint8')).save(os.path.join(V, 'close-bg.jpg'), quality=90, optimize=True)
