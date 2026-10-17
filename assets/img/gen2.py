import math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ACCENT=(255,106,0); ACC=(255,140,40)
def font(sz):
    try: return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",sz)
    except: return ImageFont.load_default()
def lerp(a,b,t): return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
def base_bg(w,h,c1,c2):
    img=Image.new("RGB",(w,h),c1); d=ImageDraw.Draw(img)
    for y in range(h): d.line([(0,y),(w,y)],fill=lerp(c1,c2,y/h*0.7))
    ov=Image.new("RGB",(w,h)); do=ImageDraw.Draw(ov)
    for x in range(w): do.line([(x,0),(x,h)],fill=lerp((0,0,0),c2,int(60*(x/w))))
    return Image.blend(img,ov,0.35)
def glow(img,cx,cy,r,color,alpha=80):
    layer=Image.new("L",img.size,0); dl=ImageDraw.Draw(layer)
    for i in range(40,0,-1):
        a=int(alpha*(i/40)**2); dl.ellipse([cx-r*i//40,cy-r*i//40,cx+r*i//40,cy+r*i//40],fill=a)
    layer=layer.filter(ImageFilter.GaussianBlur(r//3))
    img.paste(Image.composite(Image.new("RGB",img.size,color),img,layer),(0,0))
def grain(img,amt=10): return Image.blend(img,Image.effect_noise(img.size,amt).convert("RGB"),0.05)
def vignette(img):
    w,h=img.size; m=Image.new("L",(w,h),0); dm=ImageDraw.Draw(m)
    dm.ellipse([-w*.25,-h*.25,w*1.25,h*1.25],fill=255); m=m.filter(ImageFilter.GaussianBlur(min(w,h)//6))
    return Image.composite(img,Image.new("RGB",(w,h),(0,0,0)),m)
def proj(x,y,z,cx,cy,s): return (int(cx+(x-y)*0.866*s),int(cy+(x+y)*0.5*s-z*s))
BE=[(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
def bpts(x,y,z,sx,sy,sz): return [(x,y,z),(x+sx,y,z),(x+sx,y+sy,z),(x,y+sy,z),(x,y,z+sz),(x+sx,y,z+sz),(x+sx,y+sy,z+sz),(x,y+sy,z+sz)]
def draw_box(d,x,y,z,sx,sy,sz,cx,cy,s,top,left,right,outline=None):
    P=[proj(*p,cx,cy,s) for p in bpts(x,y,z,sx,sy,sz)]
    d.polygon([P[4],P[5],P[6],P[7]],fill=top,outline=outline)
    d.polygon([P[1],P[2],P[6],P[5]],fill=right,outline=outline)
    d.polygon([P[0],P[1],P[5],P[4]],fill=left,outline=outline)
    return P
def wire_box(d,x,y,z,sx,sy,sz,cx,cy,s,color=(130,160,200),w=1):
    P=[proj(*p,cx,cy,s) for p in bpts(x,y,z,sx,sy,sz)]
    for i,j in BE: d.line([P[i],P[j]],fill=color,width=w)
def wire_sphere(d,cx0,cy0,z0,r,cx,cy,s,color=(140,170,220),w=1,nlat=5,nlon=8):
    for la in range(1,nlat):
        z=z0-r+2*r*la/nlat; rr=math.sqrt(max(r*r-(z-z0)**2,0.01)); pts=[]
        for i in range(49):
            a=2*math.pi*i/48; pts.append(proj(cx0+rr*math.cos(a),cy0+rr*math.sin(a),z,cx,cy,s))
        for i in range(len(pts)-1): d.line([pts[i],pts[i+1]],fill=color,width=w)
    for lo in range(nlon):
        a=math.pi*lo/nlon; pts=[]
        for i in range(33):
            t=math.pi*i/32
            pts.append(proj(cx0+r*math.sin(t)*math.cos(a),cy0+r*math.sin(t)*math.sin(a),z0+r*math.cos(t),cx,cy,s))
        for i in range(len(pts)-1): d.line([pts[i],pts[i+1]],fill=color,width=w)
def gear_shape(d,z,r_out,r_in,teeth,cx,cy,s,fill,outline=None):
    pts=[]
    for i in range(teeth*4):
        a=2*math.pi*i/(teeth*4); r=r_out if (i%4)<2 else r_in
        pts.append(proj(r*math.cos(a),r*math.sin(a),z,cx,cy,s))
    d.polygon(pts,fill=fill,outline=outline)
def pf(name,W,H,fn,c1,c2):
    img=base_bg(W,H,c1,c2); d=ImageDraw.Draw(img)
    cx,cy,s=W//2,int(H*0.60),min(W,H)/8.2
    glow(img,cx,int(cy-s),int(s*2.4),(255,120,30),60)
    fn(d,cx,cy,s,img)
    img=vignette(img); img=grain(img); img.save(f"gen/{name}.jpg",quality=88); print(name,"ok")

W,H=1600,1200

def p_gear(d,cx,cy,s,img):
    gear_shape(d,0.9,2.2,1.7,12,cx,cy,s,(70,82,110),(40,48,66))
    gear_shape(d,0.9,0.8,0.5,8,cx,cy,s,(20,24,34),(60,70,95))
    wire_box(d,-2.4,-2.4,0,4.8,4.8,2.2,cx,cy,s,(110,140,190),1)
    draw_box(d,1.6,1.6,0,0.9,0.9,1.4,cx,cy,s,(60,68,90),(38,45,62),(24,30,42))
pf("p_gear",W,H,p_gear,(11,13,19),(28,24,38))

def p_vase(d,cx,cy,s,img):
    prof=[(0.2,0),(0.7,0.3),(1.0,1.0),(0.85,1.8),(0.55,2.4),(0.62,2.9),(0.5,3.1)]
    for rz,r in prof:
        c=lerp((255,106,0),(255,209,102),rz/3.1)
        d.ellipse([cx-r*s,cy+int(rz*s*0.55)-int(r*s*0.5),cx+r*s,cy+int(rz*s*0.55)+int(r*s*0.5)],fill=c,outline=(40,25,10))
    wire_sphere(d,-2.3,-1.6,0.9,0.9,cx,cy,s,(140,170,220),1,4,7)
pf("p_vase",W,H,p_vase,(14,12,18),(30,20,16))

def p_logo(d,cx,cy,s,img):
    W2,H2=img.size; d2=ImageDraw.Draw(img,"RGBA")
    d2.rounded_rectangle([W2*0.18,H2*0.16,W2*0.82,H2*0.84],radius=90,fill=(240,242,248,255))
    cxx,cyy=W2//2,H2//2-20; R=200
    d2.ellipse([cxx-R,cyy-R,cxx+R,cyy+R],fill=(20,22,32,255))
    d2.polygon([(cxx-R*0.75,cyy-R*0.55),(cxx-R*0.35,cyy-R*1.25),(cxx-R*0.05,cyy-R*0.75)],fill=(20,22,32,255))
    d2.polygon([(cxx+R*0.75,cyy-R*0.55),(cxx+R*0.35,cyy-R*1.25),(cxx+R*0.05,cyy-R*0.75)],fill=(20,22,32,255))
    d2.ellipse([cxx-R*0.45,cyy-R*0.25,cxx-R*0.15,cyy+R*0.05],fill=(255,140,40,255))
    d2.ellipse([cxx+R*0.15,cyy-R*0.25,cxx+R*0.45,cyy+R*0.05],fill=(255,140,40,255))
    d2.polygon([(cxx-30,cyy+R*0.28),(cxx+30,cyy+R*0.28),(cxx,cyy+R*0.5)],fill=(255,106,0,255))
    d2.text((W2*0.30,H2*0.72),"CATCO // BRANDMARK",font=font(46),fill=(30,32,45,255))
pf("p_logo",W,H,p_logo,(16,14,20),(36,26,18))

def p_poster(d,cx,cy,s,img):
    W2,H2=img.size; d2=ImageDraw.Draw(img,"RGBA")
    d2.rounded_rectangle([W2*0.22,H2*0.10,W2*0.78,H2*0.90],radius=60,fill=(250,238,215,255))
    cols=[(255,106,0),(255,209,102),(46,196,182),(255,90,120)]
    random.seed(11)
    for i in range(9):
        x=random.randint(int(W2*0.26),int(W2*0.66)); y=random.randint(int(H2*0.16),int(H2*0.7))
        r=random.randint(60,190); c=cols[i%4]
        if i%2: d2.ellipse([x,y,x+r,y+r],fill=c+(235,),outline=(25,25,35,255),width=8)
        else: d2.polygon([(x,y),(x+r,y+r//3),(x+r//4,y+r)],fill=c+(225,),outline=(25,25,35,255))
    d2.text((W2*0.28,H2*0.78),"POSTER SERIES 2025",font=font(52),fill=(25,25,35,255))
pf("p_poster",W,H,p_poster,(18,14,22),(30,22,34))

def p_emblem(d,cx,cy,s,img):
    W2,H2=img.size; d2=ImageDraw.Draw(img,"RGBA")
    cxx,cyy=W2//2,H2//2
    for i,r in enumerate([340,300,230]):
        col=(255,106,0) if i==1 else (240,240,248)
        d2.ellipse([cxx-r,cyy-r,cxx+r,cyy+r],outline=col,width=14 if i!=1 else 30)
    for ang in range(0,360,15):
        a=math.radians(ang)
        d2.line([cxx+250*math.cos(a),cyy+250*math.sin(a),cxx+290*math.cos(a),cyy+290*math.sin(a)],fill=(255,140,40,255),width=6)
    d2.polygon([(cxx-90,cyy+40),(cxx,cyy-120),(cxx+90,cyy+40)],fill=(46,196,182,255))
    d2.ellipse([cxx-40,cyy-20,cxx+40,cyy+60],fill=(255,106,0,255))
    d2.text((cxx-190,cyy+370),"VECTOR TRACING",font=font(40),fill=(200,210,230,255))
pf("p_emblem",W,H,p_emblem,(12,14,20),(20,26,40))

def p_helmet(d,cx,cy,s,img):
    wire_sphere(d,0,0,1.4,1.5,cx,cy,s,(150,180,230),1,4,8)
    d2=ImageDraw.Draw(img,"RGBA")
    for i in range(8):
        z=2.6-i*0.22; r=math.sqrt(max(1.5**2-(z-1.4)**2,0.2)) if z>0 else 0.5
        c=lerp((70,82,110),(30,36,52),i/8)
        d2.ellipse([cx-r*s,cy-int(z*s*0.55)-int(r*s*0.28),cx+r*s,cy-int(z*s*0.55)+int(r*s*0.28)],fill=c+(255,))
    d2.ellipse([cx-1.1*s,cy-0.6*s,cx+1.1*s,cy+0.5*s],fill=(255,140,40,90),outline=(255,106,0,255),width=6)
    draw_box(d,-1.5,-1.9,0,3,0.5,0.3,cx,cy,s,(50,58,80),(32,38,55),(20,25,36))
pf("p_helmet",W,H,p_helmet,(13,15,22),(26,30,44))

def p_exo(d,cx,cy,s,img):
    for i in range(5):
        draw_box(d,-0.5+i*0.02,-0.5,0.2+i*0.75,1.0-i*0.06,1.0-i*0.06,0.6,cx,cy,s,(72,84,112),(45,54,76),(28,35,50))
        wire_sphere(d,0,0,0.2+i*0.75+0.6,0.35,cx,cy,s,(160,190,240),1,3,5)
    draw_box(d,-0.2,-0.2,4.0,0.4,0.4,0.9,cx,cy,s,ACC,(200,80,10),(150,60,5))
    wire_box(d,-2.2,-2.2,0,4.4,4.4,5.0,cx,cy,s,(100,130,180),1)
pf("p_exo",W,H,p_exo,(11,12,18),(22,26,38))

def p_tile(d,cx,cy,s,img):
    W2,H2=img.size; d2=ImageDraw.Draw(img,"RGBA")
    cols=[(255,106,0),(255,209,102),(46,196,182),(240,240,248),(255,90,120)]
    random.seed(5)
    for gy in range(6):
        for gx in range(8):
            x=gx*200+random.randint(-20,20); y=gy*200+random.randint(-20,20)
            c=cols[(gx+gy)%5]; sh=(gx*7+gy*13)%3
            if sh==0: d2.ellipse([x+30,y+30,x+170,y+170],fill=c+(240,))
            elif sh==1: d2.rounded_rectangle([x+30,y+50,x+170,y+150],radius=40,fill=c+(240,))
            else: d2.polygon([(x+100,y+20),(x+180,y+180),(x+20,y+180)],fill=c+(240,))
    d2.rectangle([0,0,W2,H2],outline=(255,255,255,60),width=12)
pf("p_tile",W,H,p_tile,(16,15,20),(34,28,20))

def p_printpart(d,cx,cy,s,img):
    draw_box(d,-1.8,-1.2,0,3.6,2.4,0.15,cx,cy,s,(150,160,180),(90,98,120),(60,66,84))
    draw_box(d,-1.2,-0.8,0.15,2.4,1.6,0.5,cx,cy,s,(245,160,70),(205,120,40),(170,90,25))
    draw_box(d,-1.2,-0.8,0.65,0.6,1.6,1.6,cx,cy,s,(250,180,90),(210,130,45),(175,95,28))
    draw_box(d,0.6,-0.8,0.65,0.6,1.6,1.0,cx,cy,s,(250,180,90),(210,130,45),(175,95,28))
    wire_sphere(d,2.2,-1.8,0.7,0.6,cx,cy,s,(150,180,230),1,3,6)
    d.text((cx-int(s*2.8),cy-int(s*3.0)),"PETG // 0.2mm",font=font(24),fill=(150,170,200))
pf("p_printpart",W,H,p_printpart,(13,12,17),(28,22,18))

def p_fidget(d,cx,cy,s,img):
    gear_shape(d,1.2,1.6,1.25,9,cx,cy,s,(70,84,112),(42,52,74))
    gear_shape(d,1.2,0.55,0.35,6,cx,cy,s,(20,24,34),(150,170,210))
    for ang in range(0,360,120):
        a=math.radians(ang)
        wire_sphere(d,1.9*math.cos(a),1.9*math.sin(a),0.6,0.5,cx,cy,s,(160,190,240),1,3,5)
        draw_box(d,1.9*math.cos(a)-0.2,1.9*math.sin(a)-0.2,0.0,0.4,0.4,0.35,cx,cy,s,ACC,(200,80,10),(150,60,5))
pf("p_fidget",W,H,p_fidget,(12,13,20),(24,28,42))

# CTA sci-fi composition
def cta_scene(d,cx,cy,s,img):
    wire_torus_ring(d,cx,cy,s)
    draw_box(d,-0.7,-0.7,0.3,1.4,1.4,0.5,cx,cy,s,(60,70,95),(38,45,64),(24,29,42))
    draw_box(d,-0.4,-0.4,0.8,0.8,0.8,1.2,cx,cy,s,(85,98,130),(52,62,86),(34,42,60))
    draw_box(d,-0.15,-0.15,2.0,0.3,0.3,0.6,cx,cy,s,ACC,(200,80,10),(150,60,5))
    wire_sphere(d,0,0,3.0,1.1,cx,cy,s,(150,180,230),1,4,8)
    wire_box(d,-2.4,-2.4,0.2,0.9,0.9,0.9,cx,cy,s,(110,140,190),1)
    wire_box(d,2.0,1.4,1.6,0.7,0.7,0.7,cx,cy,s,(110,140,190),1)
def wire_torus_ring(d,cx,cy,s):
    R,r,z0=2.2,0.25,1.6
    for i in range(25):
        a=2*math.pi*i/24; pts=[]
        for j in range(25):
            b=2*math.pi*j/24
            pts.append(proj((R+r*math.cos(b))*math.cos(a),(R+r*math.cos(b))*math.sin(a),z0+r*math.sin(b),cx,cy,s))
        for k in range(len(pts)-1): d.line([pts[k],pts[k+1]],fill=(140,170,220),width=1)
pf("cta_scene",1400,1000,cta_scene,(12,13,19),(26,22,34))
print("ALL DONE")
