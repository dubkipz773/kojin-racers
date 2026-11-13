import sys; sys.path.insert(0,'/workspace/tools')
import numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi
Image.MAX_IMAGE_PIXELS=None
for p in ['/workspace/kojin-print-files/speed-identity-print.png']:
    im=Image.open(p); a=np.array(im)
    al=a[...,3]>128
    big=al
    pts=cv2.findNonZero(big.astype(np.uint8)); hull=cv2.convexHull(pts)
    m=np.zeros(al.shape,np.uint8); cv2.fillPoly(m,[hull],1)
    m=cv2.erode(m,np.ones((15,15),np.uint8))  # keep soft outer edge
    before=(a[...,3]<128).sum()
    a[...,3]=np.where(m>0,255,a[...,3])
    print(p,'restored px',before-(a[...,3]<128).sum())
    Image.fromarray(a,'RGBA').save(p,dpi=(300,300))
