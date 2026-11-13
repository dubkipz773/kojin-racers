import os, subprocess
D=os.path.dirname(os.path.abspath(__file__)); P=D+'/photos'
BG='#181819'; CREAM='#f2e9d7'; CORAL='#f55738'; CORAL_EM='#ff694c'; BODY='#dfd5c6'; QUIET='#70665d'; CARD='#232325'; CARDB='#48413d'; PRICE='#ff836e'; INK='#171717'
CAR='''<svg viewBox="0 0 760 535" fill="none" xmlns="http://www.w3.org/2000/svg" style="display:block;width:100%%;height:auto">
<defs><pattern id="g" width="38" height="38" patternUnits="userSpaceOnUse"><path d="M38 0H0V38" stroke="#e1d7c2" stroke-opacity=".13"/></pattern>
<pattern id="c" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M0 0h15v15H0zM15 15h15v15H15z" fill="#f2e9d7"/></pattern></defs>
<path d="M0 0h760v535H0z" fill="url(#g)"/><circle cx="448" cy="236" r="159" fill="#f55738"/>
<path d="M285 278h329m-325 18h319m-311 18h303m-290 18h278m-257 18h236" stroke="#1b1b1c" stroke-width="9"/>
<path d="M92 404h582M57 418h643M27 434h695M15 450h735" stroke="#eee4d3" opacity=".23"/>
<path d="M104 368C100 356 106 347 122 343L198 331C246 323 296 312 336 302C364 276 398 258 440 252C478 248 512 252 540 264C576 279 612 293 646 300L700 309C718 313 727 324 726 340L722 376L641 381A57 57 0 0 0 529 381L291 388A57 57 0 0 0 177 383L118 381C110 379 106 374 104 368Z" fill="#181819" stroke="#f2e9d7" stroke-width="5" stroke-linejoin="round"/>
<path d="M358 300C386 276 414 264 448 260L532 267C560 277 588 290 606 299L470 302Z" fill="#333031" stroke="#f2e9d7" stroke-width="4" stroke-linejoin="round"/>
<path d="M472 262 470 302M336 302 610 300M354 304 352 372M496 302 500 368M128 345C150 338 176 336 196 338M110 360 172 358M300 324C380 318 520 316 640 312M650 301 690 288 724 290 720 299M612 302 662 306" stroke="#f2e9d7" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M506 322C516 318 528 320 530 330L528 348C520 352 510 350 506 344Z" fill="#333031" stroke="#f2e9d7" stroke-width="3"/>
<path d="M368 300 386 290 394 300Z" fill="#f2e9d7"/><path d="M300 372 520 366V374L300 380Z" fill="#f55738"/><path d="M704 318h18v14h-20z" fill="#f55738"/>
<path d="M132 350 186 344 182 352 130 356Z" fill="#f2e9d7"/>
<circle cx="234" cy="381" r="48" fill="#181819" stroke="#f2e9d7" stroke-width="5"/><circle cx="234" cy="381" r="29" stroke="#f2e9d7" stroke-width="3"/>
<circle cx="585" cy="381" r="48" fill="#181819" stroke="#f2e9d7" stroke-width="5"/><circle cx="585" cy="381" r="29" stroke="#f2e9d7" stroke-width="3"/>
<path d="M234 354v54m-27-27h54m324-27v54m-27-27h54" stroke="#f55738" stroke-width="3"/>
<path d="M48 63h90v30H48z" fill="url(#c)"/><path d="M690 52h22v22m0 376v22h-22M70 472H48v-22" stroke="#f2e9d7" stroke-width="2" opacity=".7"/>
%s</svg>'''
CAR_LABELS='''<text x="48" y="504" fill="#f2e9d7" font-family="IBM Plex Mono" font-weight="600" font-size="15" letter-spacing="2">KOJIN RACERS / GARAGE DIVISION</text>
<text x="710" y="504" text-anchor="end" fill="#f55738" font-family="IBM Plex Mono" font-weight="600" font-size="15" letter-spacing="2">FIG. 01</text>'''
GRID_BG="background-color:%s;background-image:linear-gradient(rgba(225,215,194,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(225,215,194,.07) 1px,transparent 1px);background-size:54px 54px;"%BG
CSS=f'''*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:{BG};color:{CREAM};font-family:Inter,sans-serif;-webkit-font-smoothing:antialiased}}
.pg{{position:relative;overflow:hidden;background:{BG}}}
.mono{{font-family:"IBM Plex Mono",monospace;font-weight:700;letter-spacing:.14em;text-transform:uppercase}}
.kick{{font-family:"IBM Plex Mono",monospace;font-weight:700;letter-spacing:.16em;font-size:26px;display:flex;align-items:center;gap:16px}}
.kick i{{display:inline-block;width:40px;height:13px;background:{CORAL};transform:skewX(-24deg)}}
.wm{{font-weight:800;font-style:italic;letter-spacing:-.045em;font-size:40px;color:{CREAM}}}
h1{{font-weight:900;letter-spacing:-.065em;line-height:.9;color:{CREAM}}}
h1 em{{color:{CORAL_EM};font-style:italic}}
h2{{font-weight:700;letter-spacing:-.035em;line-height:1;color:{CREAM}}}
.intro{{color:{BODY};font-weight:400;line-height:1.4}}
.btn{{display:inline-flex;align-items:center;gap:16px;padding:22px 30px;font-weight:800;font-size:30px;border:2px solid {CORAL};background:{CORAL};color:{INK};letter-spacing:-.01em}}
.btn.q{{background:transparent;color:{CREAM};border-color:{QUIET}}}
.track{{position:absolute;left:0;right:0;bottom:0;background:{CORAL};color:{INK};display:flex;justify-content:space-evenly;padding:24px 20px;font-family:"IBM Plex Mono",monospace;font-weight:700;font-size:22px;letter-spacing:.14em}}
.card{{background:{CARD};border:2px solid {CARDB}}}
.card .im{{background:#fff center/cover no-repeat}}
.card .info{{display:flex;justify-content:space-between;align-items:baseline;padding:18px 20px}}
.card .info b{{white-space:nowrap;font-weight:700;font-size:23px;letter-spacing:-.025em}}
.card .info span{{font-family:"IBM Plex Mono",monospace;font-weight:700;color:{PRICE};font-size:24px}}
.corner{{position:absolute;width:34px;height:34px;border-color:rgba(242,233,215,.7);border-style:solid;border-width:0}}
'''
def ph(n): return 'file://%s/%s.jpg'%(P,n)
def top(label='DROP 01 / PACIFIC NORTHWEST', right='FIG. 0X'):
    return f'''<div style="position:absolute;left:72px;right:72px;top:64px;display:flex;justify-content:space-between;align-items:center">
<div class="wm">Kojin Racers</div><div class="mono" style="font-size:22px;color:{CORAL}">{right}</div></div>'''
pages={}
# 1 Built in the garage IG post
pages['01-built-in-the-garage-ig-post']=(1080,1350,f'''
{top(right='DROP 01')}
<div style="position:absolute;left:72px;top:150px" class="kick"><i></i>DROP 01 / PACIFIC NORTHWEST</div>
<h1 style="position:absolute;left:66px;top:206px;font-size:172px">Built in the<br><em>garage.</em></h1>
<p class="intro" style="position:absolute;left:72px;top:540px;width:900px;font-size:32px">Original motorsport tees for the people who keep old cars on the road.</p>
<div style="position:absolute;left:72px;top:660px;display:flex;gap:18px"><div class="btn">Drops soon <span>↘</span></div><div class="btn q">Follow for the launch</div></div>
<div style="position:absolute;left:268px;width:740px;top:758px;">{CAR%CAR_LABELS}</div>
<div class="track" style="padding:22px 20px"><span>KOJIN RACERS</span><span>GRASSROOTS MOTORSPORT</span><span>PACIFIC NORTHWEST</span></div>''')
# 2 Lineup
tees=[('badge','Kojin Badge Tee','$30'),('speed','Speed Identity Tee','$30'),('ghost','Ghost Streets Katakana Tee','$28'),('nippon','Nippon Performance Garage Tee','$32')]
cards=''.join(f'<div class="card"><div class="im" data-photo="{n}" style="height:345px;background-image:url({ph(n)});background-position:center 30%;background-size:118%"></div><div class="info"><b>{t}</b><span>{p}</span></div></div>' for n,t,p in tees)
pages['02-first-drop-lineup-ig-post']=(1080,1350,f'''
{top(right='04 TEES')}
<div style="position:absolute;left:72px;top:160px" class="kick"><i></i>DROP 01 / PACIFIC NORTHWEST</div>
<h2 style="position:absolute;left:70px;top:212px;font-size:104px">The first drop.</h2>
<div style="position:absolute;left:72px;right:72px;top:350px;display:grid;grid-template-columns:1fr 1fr;gap:22px">{cards}</div>
<div style="position:absolute;left:72px;right:72px;top:1240px;display:flex;justify-content:space-between;align-items:center" >
<div class="mono" style="font-size:22px;color:{CREAM}">ORIGINAL DESIGNS / UNISEX TEES</div><div class="mono" style="font-size:22px;color:{CORAL}">DROPS SOON ↘</div></div>''')
# 3 Story
pages['03-follow-for-the-launch-story']=(1080,1920,f'''
<div style="position:absolute;inset:0;{GRID_BG}"></div>
<div style="position:absolute;left:80px;right:80px;top:200px;display:flex;justify-content:space-between;align-items:center"><div class="wm" style="font-size:46px">Kojin Racers</div><div class="mono" style="font-size:24px;color:{CORAL}">FIG. 01</div></div>
<div style="position:absolute;left:80px;top:300px" class="kick"><i></i>DROP 01 / PACIFIC NORTHWEST</div>
<h1 style="position:absolute;left:74px;top:360px;font-size:180px">Built in the<br><em>garage.</em></h1>
<div class="card" style="position:absolute;left:80px;right:80px;top:740px"><div class="im" data-photo="speed" style="height:760px;background-image:url({ph('speed')});background-position:center 35%;background-size:112%"></div>
<div class="info" style="padding:22px 26px"><b style="font-size:34px">Speed Identity Tee</b><span style="font-size:28px">DROP 01</span></div></div>
<div class="corner" style="left:56px;top:716px;border-left-width:3px;border-top-width:3px"></div><div class="corner" style="right:56px;top:716px;border-right-width:3px;border-top-width:3px"></div>
<div style="position:absolute;left:80px;right:80px;top:1640px;display:flex;gap:18px"><div class="btn" style="flex:1;justify-content:center;font-size:34px">Follow for the launch ↘</div></div>
<div style="position:absolute;left:80px;right:80px;top:1580px;display:flex;justify-content:space-between" class="mono"><span style="font-size:22px">KOJIN RACERS / GARAGE DIVISION</span><span style="font-size:22px;color:{CORAL}">DROPS SOON</span></div>''')
# 4 Product hero (Badge)
pages['04-kojin-badge-tee-ig-post']=(1080,1350,f'''
{top(right='FIG. 02')}
<div style="position:absolute;left:72px;top:150px" class="kick"><i></i>DROP 01 / THE BADGE</div>
<div class="card" style="position:absolute;left:72px;right:72px;top:212px"><div class="im" data-photo="badge" style="height:800px;background-image:url({ph('badge')});background-position:center 32%;background-size:115%"></div></div>
<div class="corner" style="left:50px;top:190px;border-left-width:3px;border-top-width:3px"></div><div class="corner" style="right:50px;top:190px;border-right-width:3px;border-top-width:3px"></div>
<div style="position:absolute;left:72px;right:72px;top:1046px;display:flex;justify-content:space-between;align-items:baseline">
<h2 style="font-size:84px;font-weight:900;letter-spacing:-.055em">Kojin Badge <em style="color:{CORAL_EM}">Tee.</em></h2><div class="mono" style="font-size:40px;color:{PRICE};letter-spacing:.04em">$30</div></div>
<div style="position:absolute;left:72px;right:72px;top:1158px;display:flex;justify-content:space-between;align-items:center">
<div class="mono" style="font-size:22px;color:{BODY}">BLACK / UNISEX STAPLE TEE / ORIGINAL ART</div><div class="btn" style="font-size:28px;padding:18px 26px">Drops soon ↘</div></div>
<div class="track" style="padding:18px 20px;font-size:20px"><span>KOJIN RACERS</span><span>GRASSROOTS MOTORSPORT</span><span>PACIFIC NORTHWEST</span></div>''')
# 5 Mechanic teaser 4:5
svc=['Brakes','Suspension','Oil changes','Maintenance &amp; diagnostics','Select engine repairs']
rows=''.join(f'<div style="display:flex;gap:26px;align-items:baseline;border-top:2px solid {CARDB};padding:18px 0"><span class="mono" style="font-size:22px;color:{CORAL}">0{i+1}</span><span style="font-size:36px;font-weight:700;letter-spacing:-.03em">{s}</span></div>' for i,s in enumerate(svc))
pages['05-shop-mobile-mechanic-ig-post']=(1080,1350,f'''
{top(right='03 / SERVICES')}
<div style="position:absolute;left:72px;top:160px" class="kick"><i></i>KOJIN RACERS / GARAGE DIVISION</div>
<h1 style="position:absolute;left:66px;top:220px;font-size:132px;line-height:.92">Shop &amp; Mobile<br><em>Mechanic.</em></h1>
<p class="intro" style="position:absolute;left:72px;top:500px;width:900px;font-size:32px">In our shop or at your driveway. Serving Renton, Kent and Greater Seattle.</p>
<div style="position:absolute;left:72px;width:560px;top:610px">{rows}<div style="border-top:2px solid {CARDB}"></div></div>
<div style="position:absolute;right:36px;width:410px;top:730px">{CAR%''}</div>
<div style="position:absolute;left:72px;top:1130px;display:flex;gap:18px"><div class="btn">Booking opens soon</div><div class="btn q">DM to get on the list</div></div>
<div class="track" style="padding:22px 20px"><span>RENTON</span><span>KENT</span><span>GREATER SEATTLE</span></div>''')
pages['06-built-in-the-garage-square']=(1080,1080,f'''
{top(right='DROP 01')}
<div style="position:absolute;left:72px;top:142px" class="kick"><i></i>DROP 01 / PACIFIC NORTHWEST</div>
<h1 style="position:absolute;left:66px;top:192px;font-size:150px">Built in the<br><em>garage.</em></h1>
<p class="intro" style="position:absolute;left:72px;top:484px;width:900px;font-size:29px">Original motorsport tees for the people who keep old cars on the road.</p>
<div style="position:absolute;left:72px;top:612px;display:flex;flex-direction:column;align-items:flex-start;gap:16px"><div class="btn">Drops soon <span>↘</span></div><div class="btn q">Follow for the launch</div></div>
<div style="position:absolute;left:440px;width:600px;top:582px;">{CAR%CAR_LABELS}</div>
<div class="track" style="padding:20px 20px;font-size:20px"><span>KOJIN RACERS</span><span>GRASSROOTS MOTORSPORT</span><span>PACIFIC NORTHWEST</span></div>''')
import json,re,sys
JS="<script>window.onload=()=>{const r=[...document.querySelectorAll('.im')].map(e=>{const b=e.getBoundingClientRect();const cs=getComputedStyle(e);return {photo:e.dataset.photo,left:b.left,top:b.top,width:b.width,height:b.height,size:cs.backgroundSize,pos:cs.backgroundPosition}});document.body.setAttribute('data-rects',JSON.stringify(r))}</script>"
meta={}
def chrome(args): return subprocess.run(['google-chrome','--headless=new','--no-sandbox','--disable-gpu','--hide-scrollbars','--allow-file-access-from-files']+args,check=True,capture_output=True,timeout=60)
only=sys.argv[1:]
for name,(w,h,body) in pages.items():
    if only and name not in only: continue
    for variant in ['full','base']:
        extra = ' .im{background-image:none!important;background-color:#fff}' if variant=='base' else ''
        html=f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS} .pg{{width:{w}px;height:{h}px}}{extra}</style></head><body><div class="pg">{body}</div>{JS}</body></html>'
        f=f'{D}/{name}.{variant}.html'; open(f,'w').write(html)
        out=f'/workspace/kojin-ads/canva-exports/{name}.png' if variant=='full' else f'{D}/base/{name}.base.png'
        os.makedirs(D+'/base',exist_ok=True)
        chrome([f'--window-size={w},{h}','--force-device-scale-factor=1',f'--screenshot={out}',f'file://{f}'])
        if variant=='full':
            dom=chrome([f'--window-size={w},{h}','--virtual-time-budget=3000','--dump-dom',f'file://{f}']).stdout.decode()
            m=re.search(r'data-rects="([^"]*)"',dom)
            import html as H
            meta[name]={'w':w,'h':h,'rects':json.loads(H.unescape(m.group(1))) if m else []}
        print(out)
json.dump(meta,open(D+'/rects.json','w'),indent=1)
