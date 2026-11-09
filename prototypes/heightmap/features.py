import numpy as np
from PIL import Image, ImageDraw, ImageFont

def grooves(n=24, depth=0.4, gw=0.5):
    def h(TH, Z, Ro):
        arc = (TH % (2*np.pi/n)) * Ro           # arc-length position inside each slot (mm)
        return np.where(arc < gw, -depth, 0.0)
    return h

def hammered(n=260, r=1.1, depth=0.18, seed=1):
    rng = np.random.default_rng(seed)
    def h(TH, Z, Ro):
        ct, cz = rng.uniform(0, 2*np.pi, n), rng.uniform(Z.min(), Z.max(), n)
        out = np.zeros_like(TH)
        for t0, z0 in zip(ct, cz):
            dth = np.angle(np.exp(1j*(TH - t0)))            # wrap-around angle difference
            d2 = (dth*Ro)**2 + (Z - z0)**2
            out = np.minimum(out, np.where(d2 < r*r, -depth*(1 - d2/(r*r)), 0))
        return out
    return h

def voronoi(n=70, line=0.28, depth=0.35, seed=3):
    rng = np.random.default_rng(seed)
    def h(TH, Z, Ro):
        C = 2*np.pi*Ro; W = Z.max()-Z.min()
        sx, sz = rng.uniform(0, C, n), rng.uniform(Z.min(), Z.max(), n)
        X = TH*Ro
        d = np.stack([np.hypot(np.minimum(abs(X-x), C-abs(X-x)), Z-z) for x, z in zip(sx, sz)])
        d.sort(0)
        return np.where(d[1]-d[0] < line, -depth, 0.0)   # near the border between two cells
    return h

def engrave_text(text, font_path, depth=0.3, size_px=64):
    def h(TH, Z, Ro):
        nth, nz = TH.shape
        img = Image.new("L", (nth, nz), 0); dr = ImageDraw.Draw(img)
        font = ImageFont.truetype(font_path, int(nz*0.62))
        box = dr.textbbox((0, 0), text, font=font)
        # stretch so letters keep their proportions on the curved surface
        tw = box[2]-box[0]; th_ = box[3]-box[1]
        aspect = (2*np.pi*Ro/nth) / ((Z.max()-Z.min())/nz)   # mm per column / mm per row
        canvas = Image.new("L", (tw+20, th_+20), 0)
        ImageDraw.Draw(canvas).text((10-box[0], 10-box[1]), text, fill=255, font=font)
        canvas = canvas.resize((int(canvas.width/aspect), nz))
        img.paste(canvas, ((nth-canvas.width)//2, 0))
        m = np.asarray(img, float).T[:, ::-1]/255.0          # (nth, nz), flip so text is upright
        return -depth*m
    return h
