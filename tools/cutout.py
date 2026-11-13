import sys, numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi
def cutout(im, thr):
    """remove near-black background connected to image border; returns RGBA"""
    im=im.convert('RGBA'); a=np.asarray(im).astype(np.float32)
    mx=a[...,:3].max(-1)
    dark=mx<thr
    lab,_=ndi.label(dark)
    border=np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])); border=border[border>0]
    bg=np.isin(lab,border)
    # soft edge: in a band around bg, alpha ramps with brightness
    band=ndi.binary_dilation(bg,iterations=max(2,int(im.size[0]/400)))
    ramp=np.clip((mx-thr*0.5)/(thr*1.6-thr*0.5),0,1)
    alpha=np.where(bg,0,np.where(band,ramp,1.0))*(a[...,3]/255)
    a[...,3]=alpha*255
    lab2,n=ndi.label(alpha>0.05)
    if n:
        sizes=ndi.sum(np.ones_like(alpha),lab2,range(1,n+1))
        small=np.isin(lab2,np.where(sizes<0.00004*alpha.size)[0]+1)
        a[...,3][small]=0
    return Image.fromarray(a.astype(np.uint8),'RGBA')
def crop_pad(im,pad=0.02):
    bb=im.getchannel('A').point(lambda v:255 if v>8 else 0).getbbox()
    x0,y0,x1,y1=bb; p=int(max(x1-x0,y1-y0)*pad)
    return im.crop((max(0,x0-p),max(0,y0-p),min(im.width,x1+p),min(im.height,y1+p)))
if __name__=='__main__':
    src,dst,thr=sys.argv[1],sys.argv[2],float(sys.argv[3])
    im=Image.open(src)
    out=im.convert('RGBA') if thr<=0 else cutout(im,thr)
    out=crop_pad(out); out.save(dst); print(dst,out.size)
