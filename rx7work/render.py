import re,subprocess,sys
src=open('/workspace/kojin-drop-mechanic-hero.liquid').read()
frag=open('/workspace/rx7work/car.svgfrag').read().rstrip('\n')
lines=src.split('\n')
# lines 25-31 (1-indexed) are the car
new=lines[:24]+[frag]+lines[31:]
out='\n'.join(new)
open('/workspace/rx7work/new.liquid','w').write(out)
svg=re.search(r'<svg.*?</svg>',out,re.S).group(0).replace('{{ section.id }}','x')
open('/workspace/rx7work/hero.html','w').write('<html><body style="margin:0;background:#181819"><div style="width:1140px">'+svg+'</div></body></html>')
