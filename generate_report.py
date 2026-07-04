"""generate_report.py — called by Flask /api/report/pdf"""
import math, io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

W, H = A4
PAD = 22 * mm

BG=HexColor("#0f0f0f");CARD=HexColor("#1a1a1a");CARD2=HexColor("#202020")
HDR=HexColor("#111111");BDR=HexColor("#2e2e2e");AMBER=HexColor("#f59e0b")
GREEN=HexColor("#22c55e");RED=HexColor("#ef4444");YELL=HexColor("#eab308")
MUT=HexColor("#666666");MUT2=HexColor("#999999");WH=HexColor("#e8e8e8")

def _sc(s): return GREEN if s<40 else(AMBER if s<65 else RED)
def _lc(l): return{"Safe":GREEN,"Warning":YELL,"Critical":RED}.get(l,MUT2)
def _cc(c): return{"Deep Work":GREEN,"Context Switch":AMBER}.get(c,MUT2)
def _lb(l): return{"Safe":HexColor("#0d2818"),"Warning":HexColor("#2a1f00"),"Critical":HexColor("#2a0a0a")}.get(l,CARD)
def _cb(c): return{"Deep Work":HexColor("#0d2818"),"Context Switch":HexColor("#2a1f00"),"Passive":HexColor("#1e1e1e")}.get(c,CARD)
def _lvl(s): return"Safe"if s<40 else("Warning"if s<65 else"Critical")
def _status(s):
    if s<35: return"Focused Flow"
    if s<55: return"Mild Strain"
    if s<75: return"Moderate Fatigue"
    return"High Burnout Risk"

def _rr(cv,x,y,w,h,r=4,fill=None,stroke=None,sw=0.5):
    p=cv.beginPath()
    p.moveTo(x+r,y);p.lineTo(x+w-r,y)
    p.arcTo(x+w-r,y,x+w,y+r,270,90);p.lineTo(x+w,y+h-r)
    p.arcTo(x+w-r,y+h-r,x+w,y+h,0,90);p.lineTo(x+r,y+h)
    p.arcTo(x,y+h-r,x+r,y+h,90,90);p.lineTo(x,y+r)
    p.arcTo(x,y,x+r,y+r,180,90);p.close()
    if fill: cv.setFillColor(fill)
    if stroke: cv.setStrokeColor(stroke);cv.setLineWidth(sw)
    cv.drawPath(p,fill=1 if fill else 0,stroke=1 if stroke else 0)

def _pill(cv,x,y,w,h,txt,bg,fg,fs=7.5):
    _rr(cv,x,y,w,h,r=h/2,fill=bg)
    cv.setFillColor(fg);cv.setFont("Helvetica-Bold",fs)
    cv.drawCentredString(x+w/2,y+(h-fs)/2+1.2,txt)

def _hl(cv,x,y,w,col=None,lw=0.3):
    cv.setStrokeColor(col or BDR);cv.setLineWidth(lw);cv.line(x,y,x+w,y)

def _slbl(cv,x,y,txt):
    cv.setFont("Helvetica-Bold",7.5);cv.setFillColor(MUT);cv.drawString(x,y,txt.upper())

def _gauge(cv,cx,cy,r,score,col):
    steps=80
    cv.setStrokeColor(HexColor("#252525"));cv.setLineWidth(9);cv.setLineCap(1)
    for i in range(steps):
        a1=math.pi-(i/steps)*math.pi;a2=math.pi-((i+1)/steps)*math.pi
        cv.line(cx+r*math.cos(a1),cy+r*math.sin(a1),cx+r*math.cos(a2),cy+r*math.sin(a2))
    cv.setStrokeColor(col);cv.setLineWidth(9)
    for i in range(int(steps*score/100)):
        a1=math.pi-(i/steps)*math.pi;a2=math.pi-((i+1)/steps)*math.pi
        cv.line(cx+r*math.cos(a1),cy+r*math.sin(a1),cx+r*math.cos(a2),cy+r*math.sin(a2))

def _bar(cv,x,y,pct,bw=110,bh=4,cat=""):
    _rr(cv,x,y,bw,bh,r=2,fill=HexColor("#252525"))
    _rr(cv,x,y,max(3,bw*pct/100),bh,r=2,fill=_cc(cat))

def generate_pdf(data:dict)->bytes:
    buf=io.BytesIO()
    cv=canvas.Canvas(buf,pagesize=A4)
    cv.setTitle("Burnout Monitor Report")
    CW=W-2*PAD;CX=PAD
    generated=data.get("generated","Today")
    score=data.get("score",38)
    summary=data.get("summary",[("Focus Time","0h"),("Context Switches","0"),("Peak Load Time","--")])
    trend7=data.get("trend7",[])
    apps=data.get("apps",[])
    sc_col=_sc(score);status=_status(score)

    # BG
    cv.setFillColor(BG);cv.rect(0,0,W,H,fill=1,stroke=0)

    # Header
    cv.setFillColor(HDR);cv.rect(0,H-50,W,50,fill=1,stroke=0)
    _hl(cv,0,H-50,W,col=BDR,lw=0.5)
    cv.setFillColor(WH);cv.setFont("Helvetica-Bold",15);cv.drawString(PAD,H-22,"Burn Alert")
    cv.setFillColor(MUT2);cv.setFont("Helvetica",8.5);cv.drawString(PAD,H-36,"Burnout Monitor Report")
    cv.setFillColor(MUT);cv.setFont("Helvetica",8);cv.drawRightString(W-PAD,H-22,f"Generated: {generated}")
    _pill(cv,W-PAD-46,H-39,40,13,"● LIVE",HexColor("#0d2818"),GREEN,fs=7)

    y=H-50-16

    # Score card
    ch=142;cy0=y-ch
    _rr(cv,CX,cy0,CW,ch,r=7,fill=HexColor("#161616"),stroke=BDR,sw=0.5)
    gcx=CX+90;gcy=cy0+62
    _gauge(cv,gcx,gcy,48,score,sc_col)
    cv.setFillColor(sc_col);cv.setFont("Helvetica-Bold",34);cv.drawCentredString(gcx,gcy-8,str(score))
    cv.setFillColor(MUT);cv.setFont("Helvetica",9);cv.drawCentredString(gcx,gcy-22,"/100")
    cv.setFillColor(MUT);cv.setFont("Helvetica-Bold",7);cv.drawCentredString(gcx,cy0+16,"CURRENT STATE")
    cv.setFillColor(WH);cv.setFont("Helvetica-Bold",11);cv.drawCentredString(gcx,cy0+5,status)
    cv.setStrokeColor(BDR);cv.setLineWidth(0.5);cv.line(CX+172,cy0+10,CX+172,cy0+ch-10)
    mw=(CW-185)/3
    for i,(lbl,val) in enumerate(summary[:3]):
        mx=CX+185+i*mw+mw/2
        cv.setFillColor(WH);cv.setFont("Helvetica-Bold",19);cv.drawCentredString(mx,cy0+70,str(val))
        cv.setFillColor(MUT);cv.setFont("Helvetica",8);cv.drawCentredString(mx,cy0+55,lbl)
        cv.setFillColor(HexColor("#444444"));cv.setFont("Helvetica",7);cv.drawCentredString(mx,cy0+ch-16,"today")
        if i<2:
            cv.setStrokeColor(BDR);cv.setLineWidth(0.5)
            cv.line(CX+185+(i+1)*mw,cy0+10,CX+185+(i+1)*mw,cy0+ch-10)
    y=cy0-18

    # Today's Summary table
    _slbl(cv,CX,y,"Today's Summary");y-=10
    srh=22
    _rr(cv,CX,y-srh,CW,srh,r=4,fill=HexColor("#161616"))
    for txt,cx in zip(["METRIC","VALUE"],[CX+CW*0.45/2,CX+CW*0.45+CW*0.55/2]):
        cv.setFillColor(MUT);cv.setFont("Helvetica-Bold",7.5)
        cv.drawCentredString(cx,y-srh+(srh-7.5)/2+1.5,txt)
    _hl(cv,CX,y-srh,CW);y-=srh
    for i,(lbl,val) in enumerate(summary):
        ry=y-(i+1)*srh
        cv.setFillColor(CARD2 if i%2==0 else CARD);cv.rect(CX,ry,CW,srh,fill=1,stroke=0)
        ty=ry+(srh-9)/2+1.5
        cv.setFillColor(MUT2);cv.setFont("Helvetica",9);cv.drawCentredString(CX+CW*0.45/2,ty,lbl)
        cv.setFillColor(WH);cv.setFont("Helvetica-Bold",9);cv.drawCentredString(CX+CW*0.45+CW*0.55/2,ty,str(val))
        _hl(cv,CX,ry,CW)
    sb=y-len(summary)*srh;_hl(cv,CX,sb,CW);y=sb-18

    # 7-Day trend
    _slbl(cv,CX,y,"7-Day Burnout Scores");y-=10
    rh=23;t_cxs=[CX+CW*0.22/2,CX+CW*0.22+CW*0.38/2,CX+CW*0.22+CW*0.38+CW*0.40/2]
    _rr(cv,CX,y-rh,CW,rh,r=4,fill=HexColor("#161616"))
    for txt,cx in zip(["DAY","SCORE","LEVEL"],t_cxs):
        cv.setFillColor(MUT);cv.setFont("Helvetica-Bold",7.5)
        cv.drawCentredString(cx,y-rh+(rh-7.5)/2+1.5,txt)
    _hl(cv,CX,y-rh,CW);y-=rh
    for i,entry in enumerate(trend7[:7]):
        day=entry[0];sc_v=int(entry[1]);lvl=_lvl(sc_v)
        ry=y-(i+1)*rh
        cv.setFillColor(CARD2 if i%2==0 else CARD);cv.rect(CX,ry,CW,rh,fill=1,stroke=0)
        ty=ry+(rh-9)/2+1.5
        cv.setFillColor(WH);cv.setFont("Helvetica",9);cv.drawCentredString(t_cxs[0],ty,day)
        cv.setFillColor(_sc(sc_v));cv.setFont("Helvetica-Bold",11);cv.drawCentredString(t_cxs[1],ty-1,str(sc_v))
        _pill(cv,t_cxs[2]-27,ry+(rh-14)/2,54,14,lvl,_lb(lvl),_lc(lvl))
        _hl(cv,CX,ry,CW)
    tb=y-min(len(trend7),7)*rh;_hl(cv,CX,tb,CW);y=tb-18

    # App usage
    _slbl(cv,CX,y,"App Usage Breakdown");y-=10
    mxh=max((a[1] for a in apps),default=1)
    arh=25;hdh=22
    acols=[CX+6,CX+CW*0.28,CX+CW*0.50,CX+CW*0.76]
    _rr(cv,CX,y-hdh,CW,hdh,r=4,fill=HexColor("#161616"))
    for txt,ax in zip(["APPLICATION","HOURS","USAGE","CATEGORY"],acols):
        cv.setFillColor(MUT);cv.setFont("Helvetica-Bold",7.5)
        cv.drawString(ax,y-hdh+(hdh-7.5)/2+1.5,txt)
    _hl(cv,CX,y-hdh,CW);y-=hdh
    for i,(aname,hrs,cat) in enumerate(apps[:10]):
        ry=y-(i+1)*arh
        cv.setFillColor(CARD2 if i%2==0 else CARD);cv.rect(CX,ry,CW,arh,fill=1,stroke=0)
        ty=ry+(arh-9)/2+1.5
        cv.setFillColor(WH);cv.setFont("Helvetica",9);cv.drawString(acols[0],ty,aname)
        cv.setFillColor(WH);cv.setFont("Helvetica-Bold",10);cv.drawString(acols[1],ty,f"{hrs}h")
        _bar(cv,acols[2],ry+(arh-4)/2,pct=hrs/mxh*100,bw=CW*0.23,bh=4,cat=cat)
        _pill(cv,acols[3],ry+(arh-14)/2,82,14,cat,_cb(cat),_cc(cat))
        _hl(cv,CX,ry,CW)
    ab=y-min(len(apps),10)*arh;_hl(cv,CX,ab,CW)

    # Footer
    cv.setFillColor(HDR);cv.rect(0,0,W,26,fill=1,stroke=0)
    _hl(cv,0,26,W,col=BDR,lw=0.5)
    cv.setFillColor(MUT);cv.setFont("Helvetica",7.5)
    cv.drawCentredString(W/2,9,"Burnout Monitor  —  Privacy-first focus analytics")

    cv.save();buf.seek(0)
    return buf.read()
