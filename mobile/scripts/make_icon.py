"""Generate an original Meme Fighter app-icon candidate (not third-party meme artwork).
Outputs a fully opaque 1024px PNG for Apple. Uses only Pillow; the generated PNG
is tracked by Git after reviewing the candidate.
"""
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/"assets"/"icon.png"
SIZE=1024
BG=(18,12,42)

def font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf"):
        if Path(p).exists(): return ImageFont.truetype(p,size)
    return ImageFont.load_default()

def produce():
    im=Image.new("RGB",(SIZE,SIZE),BG)
    pixels=im.load()
    # Two opposing neon arcs behind a large original MF monogram.
    for y in range(SIZE):
        for x in range(SIZE):
            dx=x-512;dy=y-480
            lift=max(0,1-(dx*dx+dy*dy)**0.5/670)
            left=max(0,1-((x-220)**2+(y-365)**2)**0.5/580)
            right=max(0,1-((x-790)**2+(y-560)**2)**0.5/560)
            pixels[x,y]=(int(18+8*lift+9*left+15*right),
                         int(12+7*lift+12*left+4*right),
                         int(42+23*lift+23*left+18*right))
    layer=Image.new("RGBA",(SIZE,SIZE),(0,0,0,0))
    d=ImageDraw.Draw(layer)
    # Chunky concentric rings that resemble an arcade versus screen.
    for box,width,color in [
        ((64,64,960,960),21,(112,85,160,255)),
        ((94,94,930,930),8,(92,244,213,215)),
        ((122,122,902,902),5,(251,99,173,185))]:
        d.rounded_rectangle(box,radius=176,outline=color,width=width)
    # A lightning versus slash separates the fighters.
    d.polygon([(479,240),(583,240),(521,451),(607,451),
               (418,759),(470,547),(398,547)],fill=(255,220,111,255))
    d.polygon([(279,333),(346,295),(448,400),(439,534),
               (381,601),(278,539),(234,455)],fill=(85,235,210,255))
    d.polygon([(745,333),(678,295),(576,400),(585,534),
               (643,601),(746,539),(790,455)],fill=(248,93,166,255))
    # Gloves / simplified angular fighter silhouettes, intentionally original.
    d.rounded_rectangle((245,340,402,490),radius=52,fill=(116,255,227,255))
    d.rounded_rectangle((622,340,779,490),radius=52,fill=(255,133,186,255))
    d.rounded_rectangle((291,470,388,554),radius=26,fill=(26,130,132,255))
    d.rounded_rectangle((636,470,733,554),radius=26,fill=(133,37,94,255))
    d.line([(295,364),(295,419)],fill=(218,255,251,255),width=13)
    d.line([(728,364),(728,419)],fill=(255,226,242,255),width=13)
    # Arcade title directly integrated in the mark.
    label="MEME"
    bbox=d.textbbox((0,0),label,font=font(113),stroke_width=0)
    d.text(((1024-(bbox[2]-bbox[0]))//2,675),label,
           font=font(113),fill=(250,249,255,255),stroke_width=0)
    label2="FIGHTER"
    bbox=d.textbbox((0,0),label2,font=font(68))
    d.text(((1024-(bbox[2]-bbox[0]))//2,806),label2,
           font=font(68),fill=(106,246,215,255))
    im=Image.alpha_composite(im.convert("RGBA"),layer).convert("RGB")
    return im

def main():
    img=produce()
    if "--check" in sys.argv:
        if not TARGET.exists():
            raise SystemExit("FAIL: mobile/assets/icon.png missing")
        saved=Image.open(TARGET)
        if saved.size != (1024,1024) or saved.mode!="RGB":
            raise SystemExit("FAIL: opaque 1024x1024 RGB icon required")
        print("PASS: iOS RGB icon is 1024x1024")
    else:
        TARGET.parent.mkdir(parents=True,exist_ok=True)
        img.save(TARGET,format="PNG",optimize=True)
        print("Wrote",TARGET)

if __name__=="__main__":
    main()
