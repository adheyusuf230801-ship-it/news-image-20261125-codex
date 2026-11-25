"""A deterministic newspaper, rasterized at 2x using only the standard library."""
import os
import struct
import zlib
from pathlib import Path

# Glyphs use a seven-row body, with two extra rows for lowercase descenders.
PATTERNS = {
'A':'01110/10001/10001/11111/10001/10001/10001',
'B':'11110/10001/10001/11110/10001/10001/11110',
'C':'01111/10000/10000/10000/10000/10000/01111',
'D':'11110/10001/10001/10001/10001/10001/11110',
'E':'11111/10000/10000/11110/10000/10000/11111',
'F':'11111/10000/10000/11110/10000/10000/10000',
'G':'01111/10000/10000/10111/10001/10001/01111',
'H':'10001/10001/10001/11111/10001/10001/10001',
'I':'111/010/010/010/010/010/111',
'J':'00111/00010/00010/00010/10010/10010/01100',
'K':'10001/10010/10100/11000/10100/10010/10001',
'L':'10000/10000/10000/10000/10000/10000/11111',
'M':'10001/11011/10101/10101/10001/10001/10001',
'N':'10001/11001/11001/10101/10011/10011/10001',
'O':'01110/10001/10001/10001/10001/10001/01110',
'P':'11110/10001/10001/11110/10000/10000/10000',
'Q':'01110/10001/10001/10001/10101/10010/01101',
'R':'11110/10001/10001/11110/10100/10010/10001',
'S':'01111/10000/10000/01110/00001/00001/11110',
'T':'11111/00100/00100/00100/00100/00100/00100',
'U':'10001/10001/10001/10001/10001/10001/01110',
'V':'10001/10001/10001/10001/10001/01010/00100',
'W':'10001/10001/10001/10101/10101/10101/01010',
'X':'10001/10001/01010/00100/01010/10001/10001',
'Y':'10001/10001/01010/00100/00100/00100/00100',
'Z':'11111/00001/00010/00100/01000/10000/11111',
'a':'00000/00000/01110/00001/01111/10001/01111',
'b':'10000/10000/11110/10001/10001/10001/11110',
'c':'00000/00000/01111/10000/10000/10000/01111',
'd':'00001/00001/01111/10001/10001/10001/01111',
'e':'00000/00000/01110/10001/11111/10000/01111',
'f':'00110/01000/01000/11100/01000/01000/01000',
'g':'00000/00000/01111/10001/10001/10001/01111/00001/01110',
'h':'10000/10000/11110/10001/10001/10001/10001',
'i':'1/0/1/1/1/1/1',
'j':'001/000/001/001/001/001/001/101/010',
'k':'10000/10000/10010/10100/11000/10100/10010',
'l':'10/10/10/10/10/10/01',
'm':'00000/00000/11010/10101/10101/10101/10101',
'n':'00000/00000/11110/10001/10001/10001/10001',
'o':'00000/00000/01110/10001/10001/10001/01110',
'p':'00000/00000/11110/10001/10001/10001/11110/10000/10000',
'q':'00000/00000/01111/10001/10001/10001/01111/00001/00001',
'r':'0000/0000/1011/1100/1000/1000/1000',
's':'00000/00000/01111/10000/01110/00001/11110',
 't':'0100/0100/1110/0100/0100/0100/0011',
'u':'00000/00000/10001/10001/10001/10001/01111',
'v':'00000/00000/10001/10001/10001/01010/00100',
'w':'00000/00000/10001/10001/10101/10101/01010',
'x':'00000/00000/10001/01010/00100/01010/10001',
'y':'00000/00000/10001/10001/10001/10001/01111/00001/11110',
'z':'00000/00000/11111/00010/00100/01000/11111',
'0':'01110/10001/10011/10101/11001/10001/01110',
'1':'010/110/010/010/010/010/111',
'2':'01110/10001/00001/00010/00100/01000/11111',
'3':'11110/00001/00001/01110/00001/00001/11110',
'4':'00010/00110/01010/10010/11111/00010/00010',
'5':'11111/10000/10000/11110/00001/00001/11110',
'6':'01110/10000/10000/11110/10001/10001/01110',
'7':'11111/00001/00010/00100/01000/01000/01000',
'8':'01110/10001/10001/01110/10001/10001/01110',
'9':'01110/10001/10001/01111/00001/00001/01110',
' ':'000/000/000/000/000/000/000',
'.':'0/0/0/0/0/0/1', ',':'00/00/00/00/00/01/10',
';':'00/01/00/00/00/01/10', ':':'0/1/0/0/1/0/0',
'!':'1/1/1/1/1/0/1', '?':'1110/0001/0001/0110/0100/0000/0100',
"'":'1/1/0/0/0/0/0', '"':'101/101/000/000/000/000/000',
'-':'000/000/000/111/000/000/000',
'(':'01/10/10/10/10/10/01', ')':'10/01/01/01/01/01/10',
'/':'00001/00001/00010/00100/01000/10000/10000',
'&':'01100/10010/10100/01000/10101/10010/01101',
'%':'11001/11010/00010/00100/01000/01011/10011',
'$':'00100/01111/10100/01110/00101/11110/00100',
'·':'0/0/0/1/0/0/0',
}
FONT = {ch: rows.split('/') for ch, rows in PATTERNS.items()}
PAPER = (246, 241, 228)
INK = (32, 34, 33)
RED = (145, 39, 41)
MUTED = (104, 101, 94)
RULE = (192, 184, 168)
S = 2
W = H = 1024
pixels = bytearray(bytes(PAPER) * (W * H * S * S))
PRINTED = []


def rect(x, y, w, h, color=INK):
    x0, y0 = round(x*S), round(y*S)
    x1, y1 = round((x+w)*S), round((y+h)*S)
    assert 0 <= x0 <= x1 <= W*S and 0 <= y0 <= y1 <= H*S
    row = bytes(color) * (x1-x0)
    for yy in range(y0, y1):
        start = (yy*W*S+x0)*3
        pixels[start:start+len(row)] = row


def polygon(points, color=INK):
    pts = [(x*S, y*S) for x, y in points]
    for y in range(int(min(p[1] for p in pts)), int(max(p[1] for p in pts))+1):
        hits = []
        for (x1,y1),(x2,y2) in zip(pts, pts[1:]+pts[:1]):
            if min(y1,y2) <= y+.5 < max(y1,y2):
                hits.append(x1+(y+.5-y1)*(x2-x1)/(y2-y1))
        hits.sort()
        for a,b in zip(hits[::2],hits[1::2]):
            rect(a/S, y/S, (b-a)/S, 1/S, color)


def circle(cx, cy, radius, color=INK):
    for y in range(round((cy-radius)*S), round((cy+radius)*S)):
        dy = (y+.5)/S-cy
        dx = max(0, radius*radius-dy*dy)**.5
        rect(cx-dx, y/S, 2*dx, 1/S, color)


def width(s, size):
    return (sum(len(FONT.get(c, FONT[' '])[0])+1 for c in s)-1)*size


def text(s, x, y, size, color=INK, max_width=None):
    PRINTED.append(s)
    if max_width is not None:
        size = min(size, max_width/(width(s, 1) or 1))
    assert x+width(s,size) <= 985 and y+max(len(FONT.get(c, FONT[' '])) for c in s)*size <= 1000, s
    for ch in s:
        rows = FONT.get(ch, FONT[' '])
        for yy,row in enumerate(rows):
            for xx,bit in enumerate(row):
                if bit == '1':
                    rect(x+xx*size, y+yy*size, size, size, color)
        x += (len(rows[0])+1)*size
    return size


def centered(s, y, size, color=INK):
    text(s, (W-width(s,size))/2, y, size, color)


def rule(y, x=42, w=940, color=INK, h=1):
    rect(x,y,w,h,color)


# Newspaper furniture: generous paper, decisive rules, a single accent ink.
text('THE DAY IN ONE IMAGE',42,28,1.35,RED)
issue = 'GLOBAL EDITION / 08 STORIES'
text(issue,982-width(issue,1.15),29,1.15,MUTED)
rule(49)
centered('WORLD IN ONE DAY',66,8.0)
rule(135,h=3)
text('WEDNESDAY 25 NOVEMBER 2026',42,151,1.65)
text('A WORLD IN MOTION',982-width('A WORLD IN MOTION',1.35),153,1.35,RED)
rule(179,h=1)

# The lead is treated as a picture-led feature with an original geometric launch.
text('01 / SPACE',42,200,1.4,RED)
text('SHENZHOU-24',42,228,5.25,max_width=584)
text('LIFTS OFF',42,279,5.8,max_width=584)
rect(42,338,44,4,RED)
text('China launches Shenzhou-24 to Tiangong at 00:18 UTC.',42,364,1.75,max_width=583)
text('Muhammad Zeeshan Ali, first Pakistani in orbit, joins Tang Hongbo',42,390,1.75,max_width=583)
text('and Wu Yi on the first joint Chinese-foreign crewed flight.',42,416,1.75,max_width=583)
text('THREE ASTRONAUTS. A FIRST SHARED FLIGHT.',42,468,1.2,RED,max_width=582)

# A flat editorial illustration: orbital disc, launch plume, gantry and rocket.
rect(661,198,321,290,(235,228,212))
circle(820,319,110,RED)
circle(820,319,96,(235,228,212))
rect(661,377,321,111,(235,228,212))
# Pad tower is offset to keep the rocket's silhouette clear.
rect(700,277,6,177,MUTED)
rect(733,277,5,177,MUTED)
for yy in (283,316,349,382,415):
    rect(700,yy,38,3,MUTED)
polygon([(792,399),(771,470),(803,449),(821,481),(840,449),(866,470),(848,399)],RED)
polygon([(808,400),(805,443),(820,462),(832,436),(834,400)],PAPER)
polygon([(800,326),(781,402),(800,392)],INK)
polygon([(842,326),(860,402),(842,392)],INK)
rect(800,278,42,123,PAPER)
polygon([(800,278),(821,234),(842,278)],INK)
rect(800,291,42,9,RED)
rect(800,383,42,17,INK)
circle(821,319,12,INK)
circle(821,319,7,RED)
rect(819,342,4,26,RED)
rect(685,474,273,3,INK)
text('00:18 UTC',677,211,1.2,INK)
text('TIANGONG / CHINA',677,495,1.1,MUTED)
rule(522,h=3)
text('THE REST OF THE WORLD',42,539,1.5,RED)
text('25.11.2026',982-width('25.11.2026',1.3),540,1.3,MUTED)

# Each item has one short summary line; detail lines retain the supplied context.
STORIES = [
('CLIMATE','DUTCH CLIMATE','TARGETS STAND',
 'The Hague appeal court keeps national climate targets binding.',
 "Judges refuse a suspension while the state's appeal proceeds."),
('PACIFIC','PACIFIC PACT','SIGNED',
 'Australia and Solomon Islands sign a security pact.',
 'Australia is primary security partner; foreign bases ruled out.'),
('LABOUR','BANGLADESH','WAGE UP 36%',
 'Garment minimum wage rises 36% to 17,000 taka after all-night talks.',
 'Gazipur workers protest, saying the new minimum is still too low.'),
('MARKETS','ASIAN TECH','SHARES SLIDE',
 'Asian technology shares fall sharply after a Wall Street retreat.',
 'Investors sell AI-linked stocks.'),
('MIDDLE EAST','COALITION HITS','HODEIDAH',
 "Saudi-led coalition strikes Yemen's Hodeidah port overnight.",
 "It intercepts drones over Saudi Arabia's Eastern Province."),
('EUROPE','EU AND CANADA','TEAM UP ON AI',
 'The EU and Canada plan deeper collaboration on AI.',
 'Artificial intelligence is the focus of the planned cooperation.'),
('VATICAN','POPE SEEKS','MAIL-IN BALLOT',
 'Pope Leo XIV applies for a US midterm mail-in ballot.',
 'The pontiff is a dual US-Vatican citizen.'),
]
# Two columns; the final right-hand cell provides a quiet edition colophon.
rect(511,570,1,358,RULE)
for i,(tag,h1,h2,summary,detail) in enumerate(STORIES):
    col,row = i%2,i//2
    x,y = 42+col*493,574+row*91
    rule(y-9,x,447,RULE)
    text(tag,x,y,1.1,RED)
    # Compact one-line headings free room for legible factual captions.
    headline = h1+' '+h2
    text(headline,x,y+18,2.15,max_width=447)
    text(summary,x,y+43,1.28,max_width=447)
    text(detail,x,y+59,1.28,max_width=447)
text('ONE DAY. EIGHT STORIES.',535,866,1.85,RED,max_width=440)
text('From orbit to the world below.',535,892,1.5,MUTED)
rule(943,h=2)
text('Sources: Xinhua · Reuters · AP · NOS · TBS News · AFP · Al Jazeera',42,962,1.35,max_width=940)
text('WORLD IN ONE DAY',42,990,0.95,MUTED)
text('25 NOV 2026 / 01',982-width('25 NOV 2026 / 01',.95),990,.95,MUTED)

# Unknown glyphs have a blank fallback; all actual publication text is checked.
assert all(c in FONT for s in PRINTED for c in s), sorted({c for s in PRINTED for c in s if c not in FONT})
assert all(c in FONT for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,;:!?\'"-()/&%$')


def png_bytes():
    """Box-filter the 2x RGB canvas and encode PNG with adaptive row filters."""
    scan = bytearray()
    previous = bytes(W*3)
    stride = W*S*3
    for y in range(H):
        row = bytearray(W*3)
        for x in range(W):
            p = y*S*stride+x*S*3
            for c in range(3):
                row[x*3+c] = (pixels[p+c]+pixels[p+3+c]+pixels[p+stride+c]+pixels[p+stride+3+c]+2)//4
        # Sub and Up filters make flat paper and repeated glyph strokes compact.
        candidates = [(0, bytes(row))]
        candidates.append((1,bytes((v-(row[i-3] if i>=3 else 0))&255 for i,v in enumerate(row))))
        candidates.append((2,bytes((v-previous[i])&255 for i,v in enumerate(row))))
        kind,data = min(candidates,key=lambda item:sum(min(v,256-v) for v in item[1]))
        scan.append(kind)
        scan.extend(data)
        previous = row
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',W,H,8,2,0,0,0))
            +chunk(b'IDAT',zlib.compress(scan,9))+chunk(b'IEND',b''))


if __name__ == '__main__':
    output = Path(os.environ.get('MAKEFUN_OUTPUT_DIR','out'))
    output.mkdir(parents=True,exist_ok=True)
    (output/'entry.png').write_bytes(png_bytes())
