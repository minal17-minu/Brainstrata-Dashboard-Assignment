from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.platypus import Flowable
import math

W, H = A4  # 210 x 297 mm

# ── Color Palette ──────────────────────────────────────────────
BG_DARK   = colors.HexColor('#0A0E1A')
BG_CARD   = colors.HexColor('#111827')
BG_CARD2  = colors.HexColor('#1C2333')
ACCENT    = colors.HexColor('#6EE7B7')   # mint green
ACCENT2   = colors.HexColor('#818CF8')   # indigo
ACCENT3   = colors.HexColor('#F472B6')   # pink
AMBER     = colors.HexColor('#FBBF24')
TEXT_HI   = colors.HexColor('#F9FAFB')
TEXT_MID  = colors.HexColor('#9CA3AF')
TEXT_LOW  = colors.HexColor('#4B5563')
BORDER    = colors.HexColor('#1F2937')
WHITE     = colors.white

# ── Paragraph Styles ───────────────────────────────────────────
def make_styles():
    s = {}
    s['hero_tag'] = ParagraphStyle('hero_tag',
        fontName='Helvetica', fontSize=8, textColor=ACCENT,
        spaceAfter=3, alignment=TA_CENTER, leading=10,
        letterSpacing=3)
    s['hero_title'] = ParagraphStyle('hero_title',
        fontName='Helvetica-Bold', fontSize=28, textColor=TEXT_HI,
        spaceAfter=6, alignment=TA_CENTER, leading=34)
    s['hero_sub'] = ParagraphStyle('hero_sub',
        fontName='Helvetica', fontSize=11, textColor=TEXT_MID,
        spaceAfter=4, alignment=TA_CENTER, leading=17)
    s['section_label'] = ParagraphStyle('section_label',
        fontName='Helvetica-Bold', fontSize=7, textColor=ACCENT,
        spaceAfter=2, leading=9, letterSpacing=2)
    s['section_title'] = ParagraphStyle('section_title',
        fontName='Helvetica-Bold', fontSize=16, textColor=TEXT_HI,
        spaceAfter=6, leading=20)
    s['body'] = ParagraphStyle('body',
        fontName='Helvetica', fontSize=9.5, textColor=TEXT_MID,
        spaceAfter=5, leading=15, alignment=TA_JUSTIFY)
    s['card_label'] = ParagraphStyle('card_label',
        fontName='Helvetica', fontSize=7.5, textColor=TEXT_MID,
        spaceAfter=2, leading=10)
    s['card_value'] = ParagraphStyle('card_value',
        fontName='Helvetica-Bold', fontSize=22, textColor=TEXT_HI,
        spaceAfter=1, leading=26)
    s['card_delta'] = ParagraphStyle('card_delta',
        fontName='Helvetica-Bold', fontSize=8, textColor=ACCENT,
        spaceAfter=0, leading=10)
    s['tag'] = ParagraphStyle('tag',
        fontName='Helvetica-Bold', fontSize=7, textColor=ACCENT2,
        spaceAfter=0, leading=9)
    s['nav'] = ParagraphStyle('nav',
        fontName='Helvetica', fontSize=8.5, textColor=TEXT_MID,
        spaceAfter=0, leading=11, alignment=TA_CENTER)
    s['nav_active'] = ParagraphStyle('nav_active',
        fontName='Helvetica-Bold', fontSize=8.5, textColor=ACCENT,
        spaceAfter=0, leading=11, alignment=TA_CENTER)
    s['caption'] = ParagraphStyle('caption',
        fontName='Helvetica', fontSize=7.5, textColor=TEXT_LOW,
        spaceAfter=0, leading=10, alignment=TA_CENTER)
    s['page_num'] = ParagraphStyle('page_num',
        fontName='Helvetica', fontSize=7, textColor=TEXT_LOW,
        spaceAfter=0, leading=9, alignment=TA_RIGHT)
    s['designer_credit'] = ParagraphStyle('designer_credit',
        fontName='Helvetica-Bold', fontSize=7, textColor=ACCENT,
        spaceAfter=0, leading=9, alignment=TA_CENTER)
    return s

ST = make_styles()

# ── Custom Flowables ───────────────────────────────────────────

class DarkRect(Flowable):
    """Filled rectangle background."""
    def __init__(self, w, h, fill=BG_CARD, radius=6, stroke=None):
        self.w, self.h = w, h
        self.fill = fill
        self.radius = radius
        self.stroke = stroke
        Flowable.__init__(self)
    def wrap(self, *args): return self.w, self.h
    def draw(self):
        c = self.canv
        c.setFillColor(self.fill)
        if self.stroke:
            c.setStrokeColor(self.stroke)
            c.setLineWidth(0.5)
            c.roundRect(0, 0, self.w, self.h, self.radius, fill=1, stroke=1)
        else:
            c.roundRect(0, 0, self.w, self.h, self.radius, fill=1, stroke=0)

class Pill(Flowable):
    def __init__(self, text, bg=ACCENT2, fg=WHITE, fontsize=7):
        self.text = text
        self.bg = bg
        self.fg = fg
        self.fontsize = fontsize
        self.pad_x = 6
        self.pad_y = 3
        Flowable.__init__(self)
    def wrap(self, *args):
        from reportlab.pdfbase.pdfmetrics import stringWidth
        tw = stringWidth(self.text, 'Helvetica-Bold', self.fontsize)
        self.tw = tw
        self.rw = tw + self.pad_x * 2
        self.rh = self.fontsize + self.pad_y * 2
        return self.rw, self.rh
    def draw(self):
        c = self.canv
        c.setFillColor(self.bg)
        c.roundRect(0, 0, self.rw, self.rh, self.rh/2, fill=1, stroke=0)
        c.setFillColor(self.fg)
        c.setFont('Helvetica-Bold', self.fontsize)
        c.drawString(self.pad_x, self.pad_y + 1, self.text)

class BarChart(Flowable):
    """Mini bar chart for analytics."""
    def __init__(self, w, h, data, color=ACCENT, labels=None):
        self.w, self.h = w, h
        self.data = data
        self.color = color
        self.labels = labels
        Flowable.__init__(self)
    def wrap(self, *a): return self.w, self.h
    def draw(self):
        c = self.canv
        n = len(self.data)
        mx = max(self.data) if self.data else 1
        gap = 3
        bar_w = (self.w - gap*(n-1)) / n
        chart_h = self.h - 14
        for i, v in enumerate(self.data):
            x = i * (bar_w + gap)
            bh = (v / mx) * chart_h
            # background bar
            c.setFillColor(colors.HexColor('#1F2937'))
            c.roundRect(x, 14, bar_w, chart_h, 2, fill=1, stroke=0)
            # value bar
            alpha_color = self.color
            c.setFillColor(alpha_color)
            c.roundRect(x, 14, bar_w, bh, 2, fill=1, stroke=0)
            if self.labels:
                c.setFillColor(TEXT_LOW)
                c.setFont('Helvetica', 5.5)
                c.drawCentredString(x + bar_w/2, 4, self.labels[i])

class LineGraph(Flowable):
    """Smooth area line chart."""
    def __init__(self, w, h, data, color=ACCENT):
        self.w, self.h = w, h
        self.data = data
        self.color = color
        Flowable.__init__(self)
    def wrap(self, *a): return self.w, self.h
    def draw(self):
        c = self.canv
        n = len(self.data)
        mx = max(self.data)
        mn = min(self.data)
        rng = mx - mn if mx != mn else 1
        pad = 8
        def px(i): return pad + i * (self.w - 2*pad) / (n - 1)
        def py(v): return pad + (v - mn) / rng * (self.h - 2*pad)
        # gradient area fill approximation
        from reportlab.lib.colors import HexColor
        pts = [(px(i), py(v)) for i, v in enumerate(self.data)]
        path = c.beginPath()
        path.moveTo(pts[0][0], pad)
        for x, y in pts:
            path.lineTo(x, y)
        path.lineTo(pts[-1][0], pad)
        path.close()
        c.setFillColor(colors.HexColor('#1a3a2a'))
        c.drawPath(path, fill=1, stroke=0)
        # line
        c.setStrokeColor(self.color)
        c.setLineWidth(1.5)
        path2 = c.beginPath()
        path2.moveTo(*pts[0])
        for x, y in pts[1:]:
            path2.lineTo(x, y)
        c.drawPath(path2, fill=0, stroke=1)
        # dots
        for x, y in pts:
            c.setFillColor(self.color)
            c.circle(x, y, 2, fill=1, stroke=0)

class DonutChart(Flowable):
    def __init__(self, size, segments, colors_list):
        self.size = size
        self.segments = segments
        self.colors_list = colors_list
        Flowable.__init__(self)
    def wrap(self, *a): return self.size, self.size
    def draw(self):
        c = self.canv
        cx = cy = self.size / 2
        r_out = self.size / 2 - 2
        r_in  = r_out * 0.58
        total = sum(self.segments)
        start = 90
        for seg, col in zip(self.segments, self.colors_list):
            sweep = 360 * seg / total
            c.setFillColor(col)
            c.wedge(cx-r_out, cy-r_out, cx+r_out, cy+r_out,
                    start, sweep, fill=1, stroke=0)
            start += sweep
        # center hole
        c.setFillColor(BG_CARD)
        c.circle(cx, cy, r_in, fill=1, stroke=0)

class HeatRow(Flowable):
    """Activity heatmap row."""
    def __init__(self, w, values, label=''):
        self.w = w
        self.values = values
        self.label = label
        self.cell = 8
        self.gap  = 2
        Flowable.__init__(self)
    def wrap(self, *a):
        self.rh = self.cell + self.gap
        return self.w, self.rh
    def draw(self):
        c = self.canv
        n = len(self.values)
        start_x = 22
        cell_w = (self.w - start_x - 4) / n
        mx = max(self.values) if max(self.values) else 1
        if self.label:
            c.setFillColor(TEXT_LOW)
            c.setFont('Helvetica', 5.5)
            c.drawString(0, self.gap + 1, self.label)
        for i, v in enumerate(self.values):
            x = start_x + i * cell_w
            intensity = v / mx
            if intensity < 0.2:   col = colors.HexColor('#1F2937')
            elif intensity < 0.4: col = colors.HexColor('#134e3a')
            elif intensity < 0.6: col = colors.HexColor('#166534')
            elif intensity < 0.8: col = colors.HexColor('#15803d')
            else:                 col = ACCENT
            c.setFillColor(col)
            c.roundRect(x, self.gap, cell_w - 1, self.cell, 1.5, fill=1, stroke=0)

class PageBackground(canvas.Canvas):
    pass

# ── Page background drawing ────────────────────────────────────

def draw_bg(canv, doc):
    canv.saveState()
    canv.setFillColor(BG_DARK)
    canv.rect(0, 0, W, H, fill=1, stroke=0)
    # subtle grid lines
    canv.setStrokeColor(colors.HexColor('#111827'))
    canv.setLineWidth(0.3)
    for x in range(0, int(W)+1, 18):
        canv.line(x, 0, x, H)
    for y in range(0, int(H)+1, 18):
        canv.line(0, y, W, y)
    # top glow
    for i in range(30):
        a = 0.04 - i*0.0012
        if a <= 0: break
        canv.setFillColorRGB(0.43, 0.91, 0.72, alpha=a)
        r = 80 + i*8
        canv.circle(W/2, H+20, r, fill=1, stroke=0)
    canv.restoreState()

def draw_footer(canv, doc):
    canv.saveState()
    canv.setFillColor(colors.HexColor('#0D1220'))
    canv.rect(0, 0, W, 14*mm, fill=1, stroke=0)
    canv.setFillColor(TEXT_LOW)
    canv.setFont('Helvetica', 7)
    canv.drawString(20*mm, 5*mm, 'BrainStrata · Dashboard UI Design Task · Internshala Submission 2026')
    canv.drawRightString(W - 20*mm, 5*mm, f'Page {doc.page}')
    canv.restoreState()

def on_page(canv, doc):
    draw_bg(canv, doc)
    draw_footer(canv, doc)

# ── Build Story ────────────────────────────────────────────────

def build():
    doc = SimpleDocTemplate(
        '/mnt/user-data/outputs/BrainStrata_Dashboard_Design.pdf',
        pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=16*mm, bottomMargin=20*mm,
    )
    story = []
    CW = W - 36*mm  # content width

    # ══════════════════════════════════════════════════════
    # PAGE 1 — COVER / HERO
    # ══════════════════════════════════════════════════════

    story.append(Spacer(1, 18*mm))
    story.append(Paragraph('DESIGN TASK — INTERNSHALA SUBMISSION', ST['hero_tag']))
    story.append(Spacer(1, 5*mm))

    # Big title block
    title_tbl = Table(
        [[Paragraph('BrainStrata', ST['hero_title'])]],
        colWidths=[CW]
    )
    title_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0D1728')),
        ('ROUNDEDCORNERS', [12]),
        ('BOX', (0,0), (-1,-1), 1, ACCENT),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(title_tbl)
    story.append(Spacer(1, 3*mm))

    sub_tbl = Table([[
        Paragraph('Analytics', ParagraphStyle('at', parent=ST['hero_title'], fontSize=28,
                  textColor=ACCENT, alignment=TA_CENTER)),
        Paragraph('Dashboard', ParagraphStyle('dt', parent=ST['hero_title'], fontSize=28,
                  textColor=ACCENT2, alignment=TA_CENTER)),
    ]], colWidths=[CW/2, CW/2])
    sub_tbl.setStyle(TableStyle([('BOTTOMPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0)]))
    story.append(sub_tbl)

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        'A complete UI design concept for a neuroscience-powered workplace intelligence platform —\n'
        'featuring real-time cognitive load tracking, team flow states, and adaptive insights.',
        ST['hero_sub']))
    story.append(Spacer(1, 8*mm))

    # Cover meta pills
    pills_data = [['ROLE', 'UI/UX DESIGN INTERN'], ['PLATFORM', 'Web Dashboard'],
                  ['THEME', 'Dark / Neuro-Tech'], ['YEAR', '2026']]
    pill_rows = []
    for k, v in pills_data:
        pill_rows.append(Table([[
            Paragraph(k, ParagraphStyle('pk', fontName='Helvetica', fontSize=6.5,
                      textColor=TEXT_LOW, leading=8)),
            Paragraph(v, ParagraphStyle('pv', fontName='Helvetica-Bold', fontSize=8.5,
                      textColor=TEXT_HI, leading=11)),
        ]], colWidths=[18*mm, 28*mm]))
    cover_pills = Table([pill_rows], colWidths=[47*mm]*4)
    cover_pills.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_CARD),
        ('ROUNDEDCORNERS', [6]),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(cover_pills)
    story.append(Spacer(1, 8*mm))

    # Mini mockup preview strip — nav bar simulation
    story.append(Paragraph('DASHBOARD PREVIEW — NAVIGATION STRUCTURE', ST['section_label']))
    story.append(Spacer(1, 2*mm))
    nav_items = [('⬡  Overview', True), ('◈  Cognitive', False),
                 ('◉  Team Flow', False), ('⊞  Projects', False),
                 ('◎  Reports', False), ('⚙  Settings', False)]
    nav_cells = [[Paragraph(label, ST['nav_active'] if active else ST['nav'])
                  for label, active in nav_items]]
    nav_tbl = Table(nav_cells, colWidths=[CW/6]*6)
    nav_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0D1220')),
        ('BACKGROUND', (0,0), (0,0), colors.HexColor('#0f2318')),
        ('LINEBELOW', (0,0), (0,0), 2, ACCENT),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
    ]))
    story.append(nav_tbl)
    story.append(Spacer(1, 14*mm))

    # Designer credit
    story.append(HRFlowable(width=CW, thickness=0.5, color=BORDER))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        'Designed for BrainStrata Design Task  ·  Submitted via Internshala  ·  2026',
        ST['designer_credit']))

    story.append(Spacer(1, 100))  # page break filler - force page 2

    # ══════════════════════════════════════════════════════
    # PAGE 2 — OVERVIEW DASHBOARD SCREEN
    # ══════════════════════════════════════════════════════
    from reportlab.platypus import PageBreak
    story.append(PageBreak())

    story.append(Paragraph('SCREEN 1  ·  OVERVIEW DASHBOARD', ST['section_label']))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph('Real-Time Cognitive Intelligence Hub', ST['section_title']))
    story.append(Paragraph(
        'The Overview screen gives team leads and managers a live pulse on team performance, '
        'focus quality, and cognitive load distribution. KPI cards update every 60 seconds '
        'and are colour-coded to reflect thresholds defined in Settings.',
        ST['body']))
    story.append(Spacer(1, 3*mm))

    # ── KPI Cards row ──
    kpi_data = [
        ('FOCUS SCORE', '87.4', '↑ 12% vs last week', ACCENT),
        ('COGNITIVE LOAD', '64%', '↓ 8% — healthy', ACCENT2),
        ('FLOW SESSIONS', '23', '↑ 5 today', AMBER),
        ('TEAM SYNC', '91%', 'Peak alignment', ACCENT3),
    ]
    kpi_cells = []
    for label, value, delta, col in kpi_data:
        cell = Table([[
            Paragraph(label, ST['card_label']),
        ],[
            Paragraph(value, ST['card_value']),
        ],[
            Paragraph(delta, ParagraphStyle('cd', parent=ST['card_delta'], textColor=col)),
        ]], colWidths=[(CW/4)-3*mm])
        cell.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), BG_CARD),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('LINEABOVE', (0,0), (-1,0), 3, col),
            ('BOX', (0,0), (-1,-1), 0.5, BORDER),
            ('ROUNDEDCORNERS', [4]),
        ]))
        kpi_cells.append(cell)

    kpi_row = Table([kpi_cells], colWidths=[(CW/4)]*4)
    kpi_row.setStyle(TableStyle([('LEFTPADDING',(0,0),(-1,-1),2),('RIGHTPADDING',(0,0),(-1,-1),2)]))
    story.append(kpi_row)
    story.append(Spacer(1, 4*mm))

    # ── Main chart + sidebar ──
    # Line chart
    lc_data = [62, 58, 71, 69, 80, 84, 79, 87, 83, 90, 87, 85]
    lc_labels = ['9am','','','12','','','3pm','','','6pm','','']
    chart_inner = [
        [Paragraph('FOCUS TREND — TODAY', ST['section_label'])],
        [LineGraph(w=95*mm, h=32*mm, data=lc_data, color=ACCENT)],
        [Paragraph('Hourly average focus score across active team members', ST['caption'])],
    ]
    chart_tbl = Table(chart_inner, colWidths=[97*mm])
    chart_tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1), BG_CARD),
        ('BOX',(0,0),(-1,-1),0.5, BORDER),
        ('TOPPADDING',(0,0),(-1,-1),8),
        ('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('LEFTPADDING',(0,0),(-1,-1),8),
        ('RIGHTPADDING',(0,0),(-1,-1),6),
    ]))

    # Donut chart
    donut_inner = [
        [Paragraph('COGNITIVE DISTRIBUTION', ST['section_label'])],
        [DonutChart(42*mm, [34,26,22,18], [ACCENT, ACCENT2, AMBER, ACCENT3])],
        [Table([[
            Table([[Paragraph('● Deep Work', ParagraphStyle('dl',fontName='Helvetica',fontSize=7,textColor=ACCENT,leading=9))]], colWidths=[35*mm]),
            Table([[Paragraph('34%', ParagraphStyle('dv',fontName='Helvetica-Bold',fontSize=7,textColor=TEXT_HI,leading=9))]], colWidths=[10*mm]),
        ]],colWidths=[35*mm,10*mm])],
        [Table([[
            Table([[Paragraph('● Collaborative', ParagraphStyle('dl2',fontName='Helvetica',fontSize=7,textColor=ACCENT2,leading=9))]], colWidths=[35*mm]),
            Table([[Paragraph('26%', ParagraphStyle('dv2',fontName='Helvetica-Bold',fontSize=7,textColor=TEXT_HI,leading=9))]], colWidths=[10*mm]),
        ]],colWidths=[35*mm,10*mm])],
        [Table([[
            Table([[Paragraph('● Reactive', ParagraphStyle('dl3',fontName='Helvetica',fontSize=7,textColor=AMBER,leading=9))]], colWidths=[35*mm]),
            Table([[Paragraph('22%', ParagraphStyle('dv3',fontName='Helvetica-Bold',fontSize=7,textColor=TEXT_HI,leading=9))]], colWidths=[10*mm]),
        ]],colWidths=[35*mm,10*mm])],
        [Table([[
            Table([[Paragraph('● Idle/Admin', ParagraphStyle('dl4',fontName='Helvetica',fontSize=7,textColor=ACCENT3,leading=9))]], colWidths=[35*mm]),
            Table([[Paragraph('18%', ParagraphStyle('dv4',fontName='Helvetica-Bold',fontSize=7,textColor=TEXT_HI,leading=9))]], colWidths=[10*mm]),
        ]],colWidths=[35*mm,10*mm])],
    ]
    donut_tbl = Table(donut_inner, colWidths=[55*mm])
    donut_tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1), BG_CARD),
        ('BOX',(0,0),(-1,-1),0.5,BORDER),
        ('TOPPADDING',(0,0),(-1,-1),8),
        ('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),8),
        ('ALIGN',(0,1),(0,1),'CENTER'),
    ]))

    mid_row = Table([[chart_tbl, Spacer(3*mm, 1), donut_tbl]], colWidths=[97*mm, 3*mm, 55*mm+4*mm])
    mid_row.setStyle(TableStyle([('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    story.append(mid_row)
    story.append(Spacer(1, 4*mm))

    # ── Activity heatmap ──
    story.append(Paragraph('WEEKLY ACTIVITY HEATMAP', ST['section_label']))
    story.append(Spacer(1, 1*mm))
    days = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    heat_data = [
        ([0,1,2,3,4,3,2,3,5,7,8,8,6,5,4,3,3,4,5,4,3,2,1,0], 'Mon'),
        ([0,0,1,2,3,5,7,8,9,8,7,6,5,4,3,4,5,6,7,5,3,2,1,0], 'Tue'),
        ([1,2,3,4,5,6,7,8,9,9,8,7,6,5,4,3,2,3,4,3,2,1,0,0], 'Wed'),
        ([0,1,2,3,4,5,6,7,8,7,6,5,4,3,2,3,4,5,6,4,3,2,1,0], 'Thu'),
        ([0,0,1,2,3,4,5,6,7,6,5,4,3,2,1,2,3,4,5,3,2,1,0,0], 'Fri'),
    ]
    heat_tbl_inner = [[HeatRow(CW, v, l)] for v, l in heat_data]
    heat_tbl = Table(heat_tbl_inner, colWidths=[CW])
    heat_tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),BG_CARD),
        ('BOX',(0,0),(-1,-1),0.5,BORDER),
        ('TOPPADDING',(0,0),(-1,-1),4),
        ('BOTTOMPADDING',(0,0),(-1,-1),2),
        ('LEFTPADDING',(0,0),(-1,-1),8),
        ('RIGHTPADDING',(0,0),(-1,-1),8),
    ]))
    story.append(heat_tbl)
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph('Hourly cognitive activity (midnight → 11pm) · Darker = higher engagement', ST['caption']))

    # ══════════════════════════════════════════════════════
    # PAGE 3 — TEAM FLOW & DESIGN RATIONALE
    # ══════════════════════════════════════════════════════
    story.append(PageBreak())

    story.append(Paragraph('SCREEN 2  ·  TEAM FLOW MONITOR', ST['section_label']))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph('Individual & Team Cognitive Flow States', ST['section_title']))
    story.append(Paragraph(
        'The Team Flow screen maps each member\'s current cognitive state in real time. '
        'Flow state is calculated from calendar density, app-switching frequency, response '
        'latency, and self-reported focus ratings. Managers can set "Do Not Disturb" periods '
        'based on this data.',
        ST['body']))
    story.append(Spacer(1, 3*mm))

    # Member flow state cards
    members = [
        ('AS', 'Aryan S.', 'Senior Engineer', '94', 'Deep Flow', ACCENT, [80,85,88,91,94,93,94]),
        ('PK', 'Priya K.', 'Product Designer', '76', 'Focused', ACCENT2, [60,65,70,72,76,74,76]),
        ('RM', 'Rohan M.', 'Data Analyst', '58', 'Moderate', AMBER, [50,52,55,58,56,59,58]),
        ('NJ', 'Neha J.', 'Tech Lead', '88', 'High Flow', ACCENT, [75,80,82,85,88,87,88]),
        ('VT', 'Vikram T.', 'Backend Dev', '43', 'Distracted', ACCENT3, [60,55,50,48,44,42,43]),
        ('SL', 'Sara L.', 'QA Engineer', '67', 'Focused', ACCENT2, [55,58,62,65,67,66,67]),
    ]

    member_cells = []
    for av, name, role, score, state, col, sparkdata in members:
        # sparkline mini
        spark_h = 16*mm
        spark_w = 24*mm
        bar_inner = [
            [Paragraph(f'{av}', ParagraphStyle('av',fontName='Helvetica-Bold',fontSize=11,
                        textColor=col,leading=14,alignment=TA_CENTER))],
        ]
        avatar = Table(bar_inner, colWidths=[9*mm])
        avatar.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#1C2333')),
            ('BOX',(0,0),(-1,-1),1.5,col),
            ('ROUNDEDCORNERS',[4]),
            ('TOPPADDING',(0,0),(-1,-1),4),
            ('BOTTOMPADDING',(0,0),(-1,-1),4),
        ]))

        member_card = Table([
            [avatar, Table([
                [Paragraph(name, ParagraphStyle('mn',fontName='Helvetica-Bold',fontSize=8.5,
                            textColor=TEXT_HI,leading=11))],
                [Paragraph(role, ParagraphStyle('mr',fontName='Helvetica',fontSize=7,
                            textColor=TEXT_MID,leading=9))],
                [Paragraph(f'{state}  {score}/100', ParagraphStyle('ms',fontName='Helvetica-Bold',
                            fontSize=7,textColor=col,leading=9))],
            ], colWidths=[28*mm])],
            [Spacer(1,2), BarChart(w=37*mm, h=12*mm, data=sparkdata, color=col)],
        ], colWidths=[10*mm, 28*mm])
        member_card.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),BG_CARD),
            ('BOX',(0,0),(-1,-1),0.5,BORDER),
            ('LINEABOVE',(0,0),(-1,0),2,col),
            ('TOPPADDING',(0,0),(-1,-1),6),
            ('BOTTOMPADDING',(0,0),(-1,-1),4),
            ('LEFTPADDING',(0,0),(-1,-1),6),
            ('RIGHTPADDING',(0,0),(-1,-1),6),
            ('SPAN',(0,1),(1,1)),
        ]))
        member_cells.append(member_card)

    # 3x2 grid
    grid = Table(
        [member_cells[:3], member_cells[3:]],
        colWidths=[CW/3]*3
    )
    grid.setStyle(TableStyle([
        ('LEFTPADDING',(0,0),(-1,-1),2),
        ('RIGHTPADDING',(0,0),(-1,-1),2),
        ('TOPPADDING',(0,0),(-1,-1),2),
        ('BOTTOMPADDING',(0,0),(-1,-1),2),
    ]))
    story.append(grid)
    story.append(Spacer(1, 5*mm))

    # ── Design Rationale ──
    story.append(HRFlowable(width=CW, thickness=0.5, color=BORDER))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('DESIGN RATIONALE & SYSTEM THINKING', ST['section_label']))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph('Design Decisions', ST['section_title']))

    rationale = [
        ('Dark Neuro-Tech Aesthetic',
         'Cognitive/brain-data products benefit from dark interfaces — they reduce eye strain '
         'during long monitoring sessions and create a "mission control" authority. The deep '
         'navy-black base (#0A0E1A) pairs with mint accents to evoke both calm and precision.'),
        ('Colour-Coded State System',
         'Each cognitive state maps to a consistent colour: mint (deep flow / optimal), indigo '
         '(focused / collaborative), amber (moderate / reactive), pink/rose (distracted / overloaded). '
         'This creates an instant visual language without reading any numbers.'),
        ('Data Density vs Clarity',
         'Dashboards for knowledge work need high data density — but readability must not suffer. '
         'Cards use micro-typography at 7–8.5pt, generous internal padding, and strong value '
         'contrast (22pt bold white values vs 7.5pt grey labels) to separate hierarchy.'),
        ('Progressive Disclosure',
         'Overview → Cognitive → Team Flow → Reports follows a zoom-in logic: from "how is the '
         'team overall" to "what is this person doing right now." This matches how managers '
         'actually investigate performance data.'),
        ('Motion Design Intention',
         'In the live product, KPI cards would animate count-up on load, sparklines would draw '
         'progressively left-to-right, and heatmap cells would fade in row-by-row. These '
         'animations reinforce the "live data" feeling without being distracting.'),
    ]

    rat_cells = []
    for title, desc in rationale:
        cell = Table([[
            Table([[
                Paragraph(title, ParagraphStyle('rt', fontName='Helvetica-Bold', fontSize=9,
                          textColor=ACCENT, leading=12)),
                Paragraph(desc, ParagraphStyle('rd', fontName='Helvetica', fontSize=8.5,
                          textColor=TEXT_MID, leading=13, spaceAfter=0)),
            ]], colWidths=[(CW/2)-6*mm])
        ]], colWidths=[(CW/2)-4*mm])
        cell.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),BG_CARD2),
            ('BOX',(0,0),(-1,-1),0.5,BORDER),
            ('LINEBEFORE',(0,0),(0,-1),2,ACCENT2),
            ('TOPPADDING',(0,0),(-1,-1),7),
            ('BOTTOMPADDING',(0,0),(-1,-1),7),
            ('LEFTPADDING',(0,0),(-1,-1),8),
            ('RIGHTPADDING',(0,0),(-1,-1),8),
        ]))
        rat_cells.append(cell)

    # 2-column grid
    rat_rows = []
    for i in range(0, len(rat_cells), 2):
        row = rat_cells[i:i+2]
        if len(row) == 1:
            row.append(Spacer((CW/2)-4*mm, 1))
        rat_rows.append(row)

    rat_grid = Table(rat_rows, colWidths=[CW/2]*2)
    rat_grid.setStyle(TableStyle([
        ('LEFTPADDING',(0,0),(-1,-1),2),
        ('RIGHTPADDING',(0,0),(-1,-1),2),
        ('TOPPADDING',(0,0),(-1,-1),2),
        ('BOTTOMPADDING',(0,0),(-1,-1),2),
    ]))
    story.append(rat_grid)

    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width=CW, thickness=0.5, color=BORDER))
    story.append(Spacer(1, 3*mm))

    # Final footer strip
    final = Table([[
        Paragraph('BrainStrata Dashboard', ParagraphStyle('fl',fontName='Helvetica-Bold',
                  fontSize=9,textColor=ACCENT,leading=11)),
        Paragraph('UI Design Task — Internshala 2026', ParagraphStyle('fc',fontName='Helvetica',
                  fontSize=8,textColor=TEXT_MID,leading=11,alignment=TA_CENTER)),
        Paragraph('Crafted with intention ✦', ParagraphStyle('fr',fontName='Helvetica',
                  fontSize=8,textColor=TEXT_LOW,leading=11,alignment=TA_RIGHT)),
    ]], colWidths=[CW/3]*3)
    final.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    story.append(final)

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print("Done!")

build()
