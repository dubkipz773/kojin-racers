import sys, numpy as np, cv2
from PIL import Image, ImageFilter
W,H=1100,1320
def load_tee(n):
    t=Image.open(f'/workspace/kojin-mockups/base/crop-{n}.png').convert('RGB').resize((W,H),Image.LANCZOS)
    return t
def shirt_bounds(t):
    a=np.asarray(t).astype(float); bg=a[5:40,5:40].reshape(-1,3).mean(0)
    m=np.abs(a-bg).sum(-1)>25
    rows=np.where(m.any(1))[0]; return m,rows.min(),rows.max()
def composite(tee, art, cx, top, width, out):
    t=np.asarray(tee).astype(np.float32)/255
    art=art.convert('RGBA'); w=int(width); h=int(art.height*w/art.width)
    art=art.resize((w,h),Image.LANCZOS)
    A=np.asarray(art).astype(np.float32)/255
    x0=int(cx-w/2); y0=int(top)
    reg=t[y0:y0+h,x0:x0+w]
    lum=reg@np.array([.299,.587,.114],np.float32)
    # fabric shading: low-freq ratio and high-freq grain
    blur=cv2.GaussianBlur(lum,(0,0),25); base=float(np.median(blur))+1e-3
    shade=np.clip(blur/base,0.75,1.25)
    grain=lum-cv2.GaussianBlur(lum,(0,0),1.5)
    # displacement by fabric folds
    gy,gx=np.gradient(cv2.GaussianBlur(lum,(0,0),6))
    k=60.0
    mx,my=np.meshgrid(np.arange(w,dtype=np.float32),np.arange(h,dtype=np.float32))
    A=cv2.remap(A,mx+gx*k,my+gy*k,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
    rgb=A[...,:3]; al=A[...,3:]*0.97
    # shading: for dark shirt use relative brightness of folds; light shirt multiply-ish
    ink=rgb*shade[...,None]**0.9 + grain[...,None]*1.6
    ink=np.clip(ink,0,1)
    # soft edge / slight ink spread
    al=cv2.GaussianBlur(al,(0,0),0.6)[...,None] if al.ndim==3 else al
    if al.ndim==2: al=al[...,None]
    reg2=reg*(1-al)+ink*al
    t[y0:y0+h,x0:x0+w]=reg2
    Image.fromarray((np.clip(t,0,1)*255+.5).astype(np.uint8)).save(out,quality=92)
if __name__=='__main__':
    n,artp,out,cx,top,width=sys.argv[1:7]
    composite(load_tee(n),Image.open(artp),float(cx),float(top),float(width),out)
