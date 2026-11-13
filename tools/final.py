import sys; sys.path.insert(0,'/workspace/tools')
import numpy as np
from PIL import Image, ImageFilter
from cutout import cutout, crop_pad
Image.MAX_IMAGE_PIXELS=None
jobs=[('design1-badge',30,'kojin-badge'),('design2-patch',0,'nippon-performance-garage'),('design3-fixed',45,'speed-identity'),('design4-katakana',30,'ghost-streets-katakana')]
for d,thr,name in jobs:
    orig=Image.open(f'/workspace/kojin-user-designs/{d}.png')
    esr=Image.open(f'/workspace/kojin-print-files/raw/{d}-x4.png')
    lz=orig.resize(esr.size,Image.LANCZOS)
    lzs=lz.convert('RGB').filter(ImageFilter.UnsharpMask(radius=3,percent=60,threshold=2))
    e=np.asarray(esr.convert('RGB')).astype(np.float32); l=np.asarray(lzs).astype(np.float32)
    rgb=np.clip(e*0.65+l*0.35,0,255).astype(np.uint8)
    im=Image.fromarray(rgb)
    if orig.mode=='RGBA':
        im=im.convert('RGBA'); im.putalpha(esr.getchannel('A') if esr.mode=='RGBA' else lz.getchannel('A'))
    out=im.convert('RGBA') if thr<=0 else cutout(im,thr)
    out=crop_pad(out)
    s=4500/max(out.size); out=out.resize((round(out.width*s),round(out.height*s)),Image.LANCZOS)
    p=f'/workspace/kojin-print-files/{name}-print.png'; out.save(p,dpi=(300,300),optimize=False)
    print(p,out.size,out.mode)
