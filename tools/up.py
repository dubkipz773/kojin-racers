import sys, torch, numpy as np
from PIL import Image
from spandrel import ModelLoader
torch.set_num_threads(8)
m = ModelLoader().load_from_file('/workspace/tools/RealESRGAN_x4plus.pth').model.eval()
def run(arr):  # HxWx3 float 0-1
    H,W,_=arr.shape; T=192; P=12; out=np.zeros((H*4,W*4,3),np.float32)
    t=torch.from_numpy(arr).permute(2,0,1)[None]
    for y in range(0,H,T):
        for x in range(0,W,T):
            y0,x0=max(0,y-P),max(0,x-P); y1,x1=min(H,y+T+P),min(W,x+T+P)
            with torch.no_grad(): o=m(t[:,:,y0:y1,x0:x1]).clamp(0,1)[0].permute(1,2,0).numpy()
            print("tile",y,x,flush=True)
            yy,xx=min(T,H-y),min(T,W-x)
            out[y*4:(y+yy)*4,x*4:(x+xx)*4]=o[(y-y0)*4:(y-y0+yy)*4,(x-x0)*4:(x-x0+xx)*4]
    return out
src,dst=sys.argv[1],sys.argv[2]
im=Image.open(src)
a=np.asarray(im.convert('RGB')).astype(np.float32)/255
o=run(a)
res=Image.fromarray((o*255+0.5).astype(np.uint8))
if im.mode=='RGBA':
    al=im.getchannel('A').resize(res.size,Image.LANCZOS); res=res.convert('RGBA'); res.putalpha(al)
res.save(dst); print(dst,res.size)
