#!/usr/bin/env python3
"""Builds the talk's PowerPoint decks next to this script: beyond-skia.pptx (light) and beyond-skia-dark.pptx.

usage: python3 build_pptx.py        (needs python-pptx and Pillow)

Each slide teaches one topic in full, with its diagram and text together. Speaker notes come from
speaker_notes.json and icons from icons/. Videos are not embedded: the speaker notes say when to
play each clip from local/clips-stage/. Colours come only from the theme, so one setting changes
the whole deck. Sizes are in pixels on a 1280 x 720 slide.
"""
import io
import json
import math
import os
import re

from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_MARKER_STYLE
from pptx.enum.dml import MSO_THEME_COLOR as TC
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(HERE, 'local')
A = os.path.join(L, 'pptx')
REPO = 'https://github.com/cm-collins/fluttercon-demo-app'

# Theme slots: text, background, secondary text, card, accent, event blue, over budget, body, hairline, axis.
TEXT, BG, SUB, CARD, ACC, EVENT, RED, BODY, HAIR, AXIS = (
    TC.TEXT_1, TC.BACKGROUND_1, TC.TEXT_2, TC.BACKGROUND_2, TC.ACCENT_1, TC.ACCENT_2,
    TC.ACCENT_3, TC.ACCENT_4, TC.ACCENT_5, TC.ACCENT_6)
THEMES = {
    'light': dict(dk1='1D1D1F', lt1='FFFFFF', dk2='6E6E73', lt2='F5F5F7', accent1='0055FF', accent2='0055FF',
                  accent3='D92D20', accent4='424245', accent5='E5E5EA', accent6='AEAEB2', hlink='0055FF', folHlink='6E6E73'),
    'dark': dict(dk1='F5F5F7', lt1='000000', dk2='A1A1A6', lt2='1C1C1E', accent1='4D8DFF', accent2='0055FF',
                 accent3='FF453A', accent4='D1D1D6', accent5='2C2C2E', accent6='636366', hlink='4D8DFF', folHlink='A1A1A6'),
}
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
INK = RGBColor(0x1D, 0x1D, 0x1F)
PREVIEW = RGBColor(0x8F, 0xB3, 0xFF)
HEAD, MONO = 'Inter Tight', 'JetBrains Mono'
NS = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
CLIPS = {1: '01-broken-chart-8x.mp4', 2: '02-skia-to-impeller-concept.mp4', 3: '03-skia-first-reveal.mp4',
         4: '04-skia-repeat.mp4', 5: '05-impeller-first-reveal.mp4', 6: '06-dial-1x-to-8x.mp4',
         7: '07-xray.mp4', 8: '08-simplify-paths.mp4'}


def px(v):
    return Emu(int(round(v * 9525)))


def fs(v):
    return Pt(v * 0.75)


def paint(color_format, c):
    if isinstance(c, RGBColor):
        color_format.rgb = c
    elif isinstance(c, tuple):
        color_format.theme_color = c[0]
        color_format.brightness = c[1]
    else:
        color_format.theme_color = c


# --- Theme and layouts --------------------------------------------------------------------
def set_theme(prs, theme):
    master = prs.slide_master
    part = next(r.target_part for r in master.part.rels.values() if r.reltype.endswith('/theme'))
    root = etree.fromstring(part.blob)
    root.set('name', 'Beyond Skia')
    scheme = root.find('.//a:clrScheme', NS)
    scheme.set('name', 'Beyond Skia')
    for key, value in theme.items():
        node = scheme.find(f'a:{key}', NS)
        for child in list(node):
            node.remove(child)
        etree.SubElement(node, qn('a:srgbClr')).set('val', value)
    fonts = root.find('.//a:fontScheme', NS)
    fonts.set('name', 'Beyond Skia')
    fonts.find('a:majorFont/a:latin', NS).set('typeface', HEAD)
    fonts.find('a:minorFont/a:latin', NS).set('typeface', 'Inter')
    part._blob = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
    title = master.element.find('.//p:txStyles/p:titleStyle/a:lvl1pPr', NS)
    title.set('algn', 'l')
    rpr = title.find('a:defRPr', NS)
    rpr.set('sz', '4500')
    rpr.set('b', '1')
    rpr.set('spc', '-120')
    for shape in master.placeholders:
        if shape.placeholder_format.idx == 0:
            shape.left, shape.top, shape.width, shape.height = px(80), px(50), px(1120), px(90)
        elif shape.placeholder_format.idx == 1:
            shape.left, shape.top, shape.width, shape.height = px(80), px(150), px(1120), px(480)
        else:
            shape.left, shape.top, shape.width, shape.height = px(80), px(690), px(200), px(24)


def layout_title(layout):
    for shape in list(layout.placeholders):
        if shape.placeholder_format.idx == 0:
            shape.left, shape.top, shape.width, shape.height = px(80), px(50), px(1120), px(90)
            body = shape._element.find(qn('p:txBody')).find(qn('a:bodyPr'))
            for k in ('lIns', 'rIns', 'tIns', 'bIns'):
                body.set(k, '0')
            body.set('anchor', 't')
            for child in list(body):
                body.remove(child)
            etree.SubElement(body, qn('a:noAutofit'))
        else:
            shape._element.getparent().remove(shape._element)


def brand(layout, logo, chip=False):
    """FlutterCon wordmark, bottom right. On the blue layout it sits on a white chip, because "CON" is blue."""
    _, rid = layout.part.get_or_add_image_part(os.path.join(L, f'fluttercon-{logo}.png'))
    tree = layout.shapes._spTree
    if chip:
        tree.append(etree.fromstring(f'''<p:sp xmlns:p="{NS['p']}" xmlns:a="{NS['a']}">
      <p:nvSpPr><p:cNvPr id="903" name="Logo chip"/><p:cNvSpPr/><p:nvPr userDrawn="1"/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="{px(1082)}" y="{px(672)}"/><a:ext cx="{px(156)}" cy="{px(38)}"/></a:xfrm><a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val 50000"/></a:avLst></a:prstGeom><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="en-GB"/></a:p></p:txBody></p:sp>'''))
    tree.append(etree.fromstring(f'''<p:pic xmlns:p="{NS['p']}" xmlns:a="{NS['a']}" xmlns:r="{NS['r']}">
      <p:nvPicPr><p:cNvPr id="901" name="FlutterCon logo" descr="FlutterCon logo"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr userDrawn="1"/></p:nvPicPr>
      <p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
      <p:spPr><a:xfrm><a:off x="{px(1096)}" y="{px(680)}"/><a:ext cx="{px(128)}" cy="{px(22)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>'''))


def make_layouts(prs, dark):
    by_name = {x.name: x for x in prs.slide_layouts}
    content, blue = by_name['Title Only'], by_name['Section Header']
    content.name, blue.name = 'Statement', 'Blue'
    layout_title(content)
    layout_title(blue)
    fill = blue.background.fill
    fill.solid()
    fill.fore_color.theme_color = EVENT
    for shape in blue.placeholders:
        lst = shape._element.find(qn('p:txBody')).find(qn('a:lstStyle'))
        for child in list(lst):
            lst.remove(child)
        rpr = etree.SubElement(etree.SubElement(lst, qn('a:lvl1pPr')), qn('a:defRPr'))
        etree.SubElement(etree.SubElement(rpr, qn('a:solidFill')), qn('a:srgbClr')).set('val', 'FFFFFF')
    brand(content, 'dark' if dark else 'light')
    brand(blue, 'light', chip=True)
    for layout in list(prs.slide_layouts):
        if layout.name not in ('Statement', 'Blue'):
            prs.slide_layouts.remove(layout)
    return content, blue


# --- Drawing helpers ----------------------------------------------------------------------
def text(slide, x, y, w, h, lines, size=30, color=BODY, bold=False, font=None, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.TOP, spacing=1.08, track=None, name=None, gap=0):
    box_ = slide.shapes.add_textbox(px(x), px(y), px(w), px(h))
    tf = box_.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    if isinstance(lines, str):
        lines = [lines]
    for i, line in enumerate(lines):
        par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        par.alignment = align
        par.line_spacing = spacing
        if gap and i:
            par.space_before = fs(gap)
        runs = [(line, {})] if isinstance(line, str) else line
        for value, opt in runs:
            run = par.add_run()
            run.text = value
            f = run.font
            f.size = fs(opt.get('size', size))
            f.bold = opt.get('bold', bold)
            paint(f.color, opt.get('color', color))
            face = opt.get('font', font)
            if face:
                f.name = face
            spc = opt.get('track', track)
            if spc is not None:
                run._r.get_or_add_rPr().set('spc', str(int(spc)))
    if name:
        box_.name = name
    return box_


def big(slide, x, y, w, h, value, size, color=TEXT, align=PP_ALIGN.CENTER, name=None):
    """A headline number: tight, bold, display cut."""
    return text(slide, x, y, w, h, value, size, color, True, HEAD, align, spacing=1.0, track=-size * 2.4, name=name)


def box(slide, x, y, w, h, fill=CARD, radius=0, name=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE, px(x), px(y), px(w), px(h))
    if radius:
        shape.adjustments[0] = min(0.5, radius / min(w, h))
    shape.fill.solid()
    paint(shape.fill.fore_color, fill)
    shape.line.fill.background()
    if name:
        shape.name = name
    return shape


def rule(slide, x1, y1, x2, y2, color=HAIR, width=1.5):
    ln = slide.shapes.add_connector(1, px(x1), px(y1), px(x2), px(y2))
    paint(ln.line.color, color)
    ln.line.width = fs(width)
    return ln


def set_title(slide, value, size=None, x=80, y=50, w=1120, h=90, color=None):
    shape = slide.shapes.title
    shape.left, shape.top, shape.width, shape.height = px(x), px(y), px(w), px(h)
    tf = shape.text_frame
    tf.word_wrap = True
    par = tf.paragraphs[0]
    par.line_spacing = 0.96
    for i, part in enumerate(value.split('\n')):
        if i:
            par.add_line_break()
        run = par.add_run()
        run.text = part
        if size:
            run.font.size = fs(size)
            run._r.get_or_add_rPr().set('spc', str(int(-size * 2.2)))
        if color is not None:
            paint(run.font.color, color)
    return shape


# --- Animation ----------------------------------------------------------------------------
class Timeline:
    """Click steps for one slide. Each step is a list of effects that run together."""

    def __init__(self, slide):
        self.slide = slide
        self.steps = []
        self.ids = 2
        self.bld = []

    def click(self, *effects):
        self.steps.append(list(effects))

    def nid(self):
        self.ids += 1
        return self.ids

    def grp(self, spid):
        if self.by_id[spid].tag == qn('p:sp'):
            if spid not in self.bld:
                self.bld.append(spid)
            return 'grpId="0"'
        return ''

    def entrance(self, spid, kind, delay, dur, node):
        preset, sub, flt = {'fade': ('10', '0', 'fade'), 'left': ('22', '8', 'wipe(left)'), 'up': ('22', '4', 'wipe(up)')}[kind]
        return f'''<p:par><p:cTn id="{self.nid()}" presetID="{preset}" presetClass="entr" presetSubtype="{sub}" fill="hold" {self.grp(spid)} nodeType="{node}"><p:stCondLst><p:cond delay="{delay}"/></p:stCondLst><p:childTnLst>
<p:set><p:cBhvr><p:cTn id="{self.nid()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>
<p:animEffect transition="in" filter="{flt}"><p:cBhvr><p:cTn id="{self.nid()}" dur="{dur}"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect></p:childTnLst></p:cTn></p:par>'''

    def write(self):
        sld = self.slide._element
        node = etree.Element(qn('p:transition'))
        node.set('spd', 'med')
        etree.SubElement(node, qn('p:fade'))
        sld.find(qn('p:clrMapOvr')).addnext(node)
        if not self.steps:
            return
        self.by_id = {int(n.get('id')): n.getparent().getparent() for n in sld.iter(qn('p:cNvPr'))}
        out = []
        for effects in self.steps:
            inner = ''.join(self.entrance(e['id'], e['kind'], e.get('delay', 0), e.get('dur', 450), 'clickEffect' if j == 0 else 'withEffect')
                            for j, e in enumerate(effects))
            out.append(f'''<p:par><p:cTn id="{self.nid()}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst><p:par><p:cTn id="{self.nid()}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>{inner}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>''')
        bld = ''
        for s in self.bld:
            has_fill = self.by_id[s].find(qn('p:spPr')).find(qn('a:noFill')) is None
            bld += f'<p:bldP spid="{s}" grpId="0"' + (' animBg="1"' if has_fill else '') + '/>'
        sld.append(etree.fromstring(f'''<p:timing xmlns:p="{NS['p']}"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>{''.join(out)}</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst><p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq></p:childTnLst></p:cTn></p:par></p:tnLst>{f'<p:bldLst>{bld}</p:bldLst>' if bld else ''}</p:timing>'''))


def fx(shape, kind='fade', **kw):
    return dict(id=shape.shape_id, kind=kind, **kw)


# --- Drawings -----------------------------------------------------------------------------
def bezier():
    p0 = (10, 170)
    points = []
    for c1, c2, end in (((70, 40), (120, 40), (170, 110)), ((220, 180), (270, 190), (320, 90)), ((370, -10), (420, 30), (460, 70))):
        for k in range(24):
            t = k / 24
            m = 1 - t
            points.append(tuple(m ** 3 * p0[i] + 3 * m * m * t * c1[i] + 3 * m * t * t * c2[i] + t ** 3 * end[i] for i in (0, 1)))
        p0 = end
    points.append(p0)
    return points


def squares(slide, x, y, count, color, per_row=20, cell=24):
    group = slide.shapes.add_group_shape()
    for i in range(count):
        sq = group.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px(x + (i % per_row) * cell), px(y + (i // per_row) * cell), px(cell - 5), px(cell - 5))
        sq.adjustments[0] = 0.24
        sq.fill.solid()
        paint(sq.fill.fore_color, color)
        sq.line.fill.background()
    group.name = f'{count} squares'
    return group


def trace_row(slide, x, y, w, spans, color, label, back=CARD):
    group = slide.shapes.add_group_shape()
    bg = group.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px(x), px(y), px(w), px(44))
    bg.adjustments[0] = 0.2
    bg.fill.solid()
    paint(bg.fill.fore_color, back)
    bg.line.fill.background()
    t = 0.0
    while t < 100:
        ln = group.shapes.add_connector(1, px(x + t / 100 * w), px(y), px(x + t / 100 * w), px(y + 44))
        paint(ln.line.color, HAIR)
        ln.line.width = fs(1.5)
        t += 8.33
    for start, ms in spans:
        if 0 <= start < 100:
            r = group.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(x + start / 100 * w), px(y + 6), px(max(min(ms, 100 - start) / 100 * w - 1, 2)), px(32))
            r.fill.solid()
            paint(r.fill.fore_color, color)
            r.line.fill.background()
    group.name = label
    return group


def bar_chart(slide, x, y, w, h, cats, vals, colors, fmt, maxv, name, alt):
    data = CategoryChartData()
    data.categories = cats
    data.add_series('ms', vals)
    frame = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, px(x), px(y), px(w), px(h), data)
    frame.name = name
    frame._element.find('.//' + qn('p:cNvPr')).set('descr', alt)
    chart = frame.chart
    chart.has_legend = chart.has_title = False
    chart.font.name = 'Inter'
    cat = chart.category_axis
    cat.reverse_order = True
    cat.has_major_gridlines = False
    cat.format.line.fill.background()
    cat.major_tick_mark = 2
    cat.tick_labels.font.size = fs(24)
    paint(cat.tick_labels.font.color, TEXT)
    val = chart.value_axis
    val.visible = val.has_major_gridlines = False
    val.minimum_scale, val.maximum_scale = 0, maxv
    plot = chart.plots[0]
    plot.gap_width = 40
    plot.vary_by_categories = False
    for i, color in enumerate(colors):
        pt = plot.series[0].points[i]
        pt.format.fill.solid()
        paint(pt.format.fill.fore_color, color)
    plot.has_data_labels = True
    labels = plot.data_labels
    labels.number_format, labels.number_format_is_linked = fmt, False
    labels.position = XL_LABEL_POSITION.OUTSIDE_END
    labels.show_value = True
    labels.font.size, labels.font.bold, labels.font.name = fs(30), True, HEAD
    paint(labels.font.color, TEXT)
    return frame


def line_chart(slide, x, y, w, h):
    data = CategoryChartData()
    data.categories = ['48', '96', '144']
    data.add_series('Skia', (687, 1310, 1863))
    data.add_series('Impeller', (127, 145, 145))
    frame = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, px(x), px(y), px(w), px(h), data)
    frame.name = 'Freeze time by number of new effects'
    frame._element.find('.//' + qn('p:cNvPr')).set('descr', 'At 48, 96 and 144 new effects, Skia freezes for 687, 1,310 and 1,863 ms; Impeller for 127, 145 and 145 ms.')
    chart = frame.chart
    chart.has_legend = chart.has_title = False
    chart.font.name = 'Inter'
    val = chart.value_axis
    val.visible = val.has_major_gridlines = False
    val.minimum_scale, val.maximum_scale = 0, 2100
    cat = chart.category_axis
    cat.has_major_gridlines = False
    cat.major_tick_mark = 2
    cat.tick_labels.font.size = fs(22)
    paint(cat.tick_labels.font.color, SUB)
    paint(cat.format.line.color, HAIR)
    for series, color in zip(chart.plots[0].series, (TEXT, ACC)):
        series.smooth = False
        paint(series.format.line.color, color)
        series.format.line.width = fs(7)
        series.marker.style = XL_MARKER_STYLE.CIRCLE
        series.marker.size = 13
        series.marker.format.fill.solid()
        paint(series.marker.format.fill.fore_color, color)
        series.marker.format.line.fill.background()
    return frame


# --- Design system ------------------------------------------------------------------------
# Every slide uses one grid: 56 px side margins, 16 px gutters, content from y=128 (or y=164 under
# a subtitle) down to y=648, and the source line beside the logo at the very bottom.
ML, CW, GAP, RAD = 56, 1168, 16, 24
LS, LS_TIGHT, LS_CODE = 1.08, 0.96, 1.1
TRACK = ('How Flutter draws', 'Before: Skia', 'Now: Impeller', 'The proof', 'Inside a frame', "What it didn't fix", 'Prove it', 'Finish')


def col(i, n, x=ML, w=CW, gap=GAP):
    """Left edge and width of column i of n."""
    cw = (w - (n - 1) * gap) / n
    return x + i * (cw + gap), cw


def grad(shape, scheme, light=True):
    """A soft diagonal gradient from a theme colour to a lighter or deeper version of it."""
    shape.fill.gradient()
    fill = shape._element.spPr.find(qn('a:gradFill'))
    for child in list(fill):
        fill.remove(child)
    second = '<a:lumMod val="72000"/><a:lumOff val="28000"/>' if light else '<a:lumMod val="72000"/>'
    fill.append(etree.fromstring(f'''<a:gsLst xmlns:a="{NS['a']}"><a:gs pos="0"><a:schemeClr val="{scheme}"/></a:gs><a:gs pos="100000"><a:schemeClr val="{scheme}">{second}</a:schemeClr></a:gs></a:gsLst>'''))
    fill.append(etree.fromstring(f'<a:lin xmlns:a="{NS["a"]}" ang="2700000" scaled="0"/>'))
    return shape


def outline(shape, color, width=1.5, dash=None):
    paint(shape.line.color, color)
    shape.line.width = fs(width)
    if dash:
        etree.SubElement(shape.line._get_or_add_ln(), qn('a:prstDash')).set('val', dash)
    return shape


def arrow(slide, x1, y1, x2, y2, color=SUB, width=2.5):
    ln = rule(slide, x1, y1, x2, y2, color, width)
    etree.SubElement(ln.line._get_or_add_ln(), qn('a:tailEnd')).set('type', 'triangle')
    return ln


def chip(slide, x, y, w, h, label, fill=BG, color=TEXT, size=20, bold=True, radius=14, font=HEAD, name=None, align=PP_ALIGN.CENTER, pad=10):
    """A rounded box with text inside. A newline starts a new paragraph."""
    c = box(slide, x, y, w, h, fill, radius, name or label.replace('\n', ' '))
    tf = c.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = px(pad)
    tf.margin_top = tf.margin_bottom = px(2)
    for j, part in enumerate(label.split('\n')):
        p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = LS_TIGHT
        r = p.add_run()
        r.text = part
        r.font.size, r.font.bold, r.font.name = fs(size), bold, font
        paint(r.font.color, color)
    return c


_masks = {}


def icon_png(name, rgb):
    """Lucide icons are stored as white masks, and tinted here so they follow the theme."""
    key = (name, rgb)
    if key not in _masks:
        mask = Image.open(os.path.join(HERE, 'icons', f'{name}.png')).convert('RGBA')
        alpha = mask.getchannel('A')
        tinted = Image.new('RGBA', mask.size, tuple(int(rgb[i:i + 2], 16) for i in (0, 2, 4)) + (0,))
        tinted.putalpha(alpha)
        data = io.BytesIO()
        tinted.save(data, 'PNG')
        _masks[key] = data.getvalue()
    return io.BytesIO(_masks[key])


def dots(slide, points, color, size=6, name='Points'):
    group = slide.shapes.add_group_shape()
    for a, b in points:
        o = group.shapes.add_shape(MSO_SHAPE.OVAL, px(a - size / 2), px(b - size / 2), px(size), px(size))
        o.fill.solid()
        paint(o.fill.fore_color, color)
        o.line.fill.background()
    group.name = name
    return group


def strip_edges(half):
    all_pts = bezier()
    pts = all_pts[::2]
    if pts[-1] != all_pts[-1]:
        pts.append(all_pts[-1])
    edges = []
    for i, p in enumerate(pts):
        q, o = pts[min(i + 1, len(pts) - 1)], pts[max(i - 1, 0)]
        dx, dy = q[0] - o[0], q[1] - o[1]
        d = math.hypot(dx, dy) or 1
        edges.append(((p[0] - dy / d * half, p[1] + dx / d * half), (p[0] + dy / d * half, p[1] - dx / d * half)))
    return pts, edges


def polyline(slide, pts, color, width, name):
    fb = slide.shapes.build_freeform(px(pts[0][0]), px(pts[0][1]), scale=1.0)
    fb.add_line_segments([(px(a), px(b)) for a, b in pts[1:]], close=False)
    shape = fb.convert_to_shape()
    shape.fill.background()
    paint(shape.line.color, color)
    shape.line.width = fs(width)
    shape.name = name
    return shape


def add_sections(prs, sections):
    root = prs.part._element
    ids = [x.get('id') for x in root.find(qn('p:sldIdLst'))]
    p14 = 'http://schemas.microsoft.com/office/powerpoint/2010/main'
    xml = f'<p:ext xmlns:p="{NS["p"]}" uri="{{521415D9-36F7-43E2-AB2F-B90AF26B5E84}}"><p14:sectionLst xmlns:p14="{p14}">'
    for i, (name, first) in enumerate(sections):
        end = sections[i + 1][1] - 1 if i + 1 < len(sections) else len(ids)
        xml += f'<p14:section name="{name.replace("&", "&amp;")}" id="{{{i + 1:08X}-0000-4000-8000-{i + 1:012X}}}"><p14:sldIdLst>'
        xml += ''.join(f'<p14:sldId id="{sid}"/>' for sid in ids[first - 1:end]) + '</p14:sldIdLst></p14:section>'
    xml += '</p14:sectionLst></p:ext>'
    ext = root.find(qn('p:extLst'))
    if ext is None:
        ext = etree.SubElement(root, qn('p:extLst'))
    ext.append(etree.fromstring(xml))


# --- The deck -----------------------------------------------------------------------------
def build(variant):
    dark = variant == 'dark'
    prs = Presentation()
    prs.slide_width, prs.slide_height = px(1280), px(720)
    theme = THEMES[variant]
    set_theme(prs, theme)
    statement, blue = make_layouts(prs, dark)
    prs.core_properties.title = 'Beyond Skia: GPU scheduling and profiling with Impeller on Android 10+'
    prs.core_properties.author = 'Collins Munene'
    prs.core_properties.subject = 'FlutterCon Kenya 2026'
    trace = json.loads(re.search(r'window\.TRACE=(\{.*\});', open(os.path.join(HERE, 'trace-data.js')).read()).group(1))
    speech = json.load(open(os.path.join(HERE, 'speaker_notes.json')))
    sections, timelines = [], []
    LEFT, RIGHT, CENTER = PP_ALIGN.LEFT, PP_ALIGN.RIGHT, PP_ALIGN.CENTER
    ON_ACC = RGBColor(0, 0, 0) if dark else WHITE
    GREY = RGBColor(0x42, 0x42, 0x45)
    # Tints stay on the theme: a pale wash in light, a deep wash in dark.
    ACC_T = (ACC, -0.74) if dark else (ACC, 0.9)
    RED_T = (RED, -0.76) if dark else (RED, 0.9)
    # The spotlight tile: ink on the light deck, raised grey on the dark deck.
    SPOT, ON_SPOT = (CARD, TEXT) if dark else (TEXT, BG)
    HEX = {TEXT: theme['dk1'], BG: theme['lt1'], SUB: theme['dk2'], ACC: theme['accent1'], EVENT: theme['accent2'], RED: theme['accent3'], BODY: theme['accent4'], AXIS: theme['accent6']}

    def hex_of(c):
        if isinstance(c, RGBColor):
            return str(c)
        return HEX[c]

    def new(section=None, layout=None):
        slide = prs.slides.add_slide(layout or statement)
        if section:
            sections.append((section, len(prs.slides)))
        tl = Timeline(slide)
        timelines.append(tl)
        slide.notes_slide.notes_text_frame.text = speech[len(prs.slides) - 1]
        return slide, tl

    def head(kicker, title, section=None, size=46, sub=None):
        """Section label and journey marker, a left-aligned title and an optional line of explanation."""
        s, t = new(section)
        text(s, ML, 30, 700, 26, kicker, 20, ACC, True, HEAD, LEFT)
        if kicker in TRACK:
            at = TRACK.index(kicker)
            for i in range(len(TRACK)):
                box(s, 1224 - (len(TRACK) - i) * 34 + 6, 39, 28, 6, ACC if i == at else (AXIS if i < at else HAIR), 3, 'Progress')
        set_title(s, title, size, ML, 58, CW, size * 1.15)
        if sub:
            text(s, ML, 116, CW, 32, sub, 23, SUB, align=LEFT, spacing=1.0)
        return s, t

    def source(s, value):
        """Where the numbers came from: one quiet line, on the same line as the logo."""
        return text(s, ML, 676, 1024, 26, value, 18, SUB, align=LEFT, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0, name='Source')

    def ico(s, name, x, y, size=48, tile=ACC_T, color=ACC, radius=None):
        """A Lucide icon on a rounded tile. tile=None draws the icon alone."""
        group = s.shapes.add_group_shape()
        if tile is not None:
            back = group.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px(x), px(y), px(size), px(size))
            back.adjustments[0] = (radius if radius is not None else size * 0.28) / size
            back.fill.solid()
            paint(back.fill.fore_color, tile)
            back.line.fill.background()
            inner = size * 0.56
        else:
            inner = size
        off = (size - inner) / 2
        pic = group.shapes.add_picture(icon_png(name, hex_of(color)), px(x + off), px(y + off), px(inner), px(inner))
        pic._element.find('.//' + qn('p:cNvPr')).set('descr', '')
        group.name = f'{name} icon'
        return group

    def card(s, x, y, w, h, fill=CARD, name='Card', radius=RAD):
        return box(s, x, y, w, h, fill, radius, name)

    def hero(s, x, y, w, h, kind='blue', name='Hero tile', radius=RAD):
        shape = box(s, x, y, w, h, EVENT if kind == 'blue' else RED, radius, name)
        return grad(shape, 'accent2' if kind == 'blue' else 'accent3', kind == 'blue')

    def point(s, value, icon_name='lightbulb', y=568, h=80, size=27, sub=None):
        """The one sentence to remember, on a spotlight bar. Returns its shapes."""
        bar = box(s, ML, y, CW, h, SPOT, 22, 'Key point')
        tile = ico(s, icon_name, ML + 18, y + (h - 44) / 2, 44, ACC, ON_ACC)
        lines = [[(value, {'size': size, 'bold': True, 'font': HEAD, 'color': ON_SPOT, 'track': -30})]]
        if sub:
            lines.append([(sub, {'size': 21, 'color': ON_SPOT})])
        words = text(s, ML + 80, y, CW - 104, h, lines, size, ON_SPOT, align=LEFT, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0, gap=2)
        return bar, tile, words

    def stacked(s, x, y, w, heading, body, hsize=26, bsize=22, hcolor=TEXT, bcolor=SUB, hh=None):
        """A heading and its text, with the same gap everywhere."""
        hh = hh or hsize * 1.3
        a = text(s, x, y, w, hh, heading, hsize, hcolor, True, HEAD, LEFT, spacing=LS_TIGHT, track=-hsize * 1.1)
        b = text(s, x, y + hh + 4, w, 140, body, bsize, bcolor, align=LEFT, spacing=LS)
        return a, b

    def stat(s, x, y, w, label, frm, to, size=42, color=ACC, align=LEFT, labcolor=SUB, frmcolor=SUB, arrowcolor=SUB):
        a = text(s, x, y, w, 26, label, 19, labcolor, align=align, spacing=1.0)
        b = text(s, x, y + 28, w, size * 1.25, [[(frm, {'color': frmcolor}), ('  →  ', {'color': arrowcolor, 'bold': False}), (to, {'color': color})]],
                 size, TEXT, True, HEAD, align, spacing=1.0, track=-size * 1.4)
        return a, b

    def code(s, x, y, w, h, lines, size=19, fill=CARD, radius=20, pad=22):
        """Code on a tile. Comments are grey; `!!` marks the broken version and `++` the fixed one."""
        panel = box(s, x, y, w, h, fill, radius, 'Code')
        out = []
        for line in lines:
            c = TEXT
            if line.startswith('!!'):
                line, c = '// ' + line[2:].strip(), RED
            elif line.startswith('++'):
                line, c = '// ' + line[2:].strip(), ACC
            elif line.startswith(('//', '#')):
                c = SUB
            out.append([(line, {'color': c})])
        return panel, text(s, x + pad, y, w - pad - 10, h, out, size, TEXT, False, MONO, LEFT, MSO_ANCHOR.MIDDLE, spacing=LS_CODE)

    def table(s, x, y, widths, heights, rows, style=None, name='Table', header_fill=None):
        """A native, editable table: a header band, hairline rows, room to breathe in every cell."""
        frame = s.shapes.add_table(len(rows), len(widths), px(x), px(y), px(sum(widths)), px(sum(heights)))
        frame.name = name
        tbl = frame.table
        tp = tbl._tbl.tblPr
        for a in ('firstRow', 'bandRow'):
            tp.set(a, '0')
        sid = tp.find(qn('a:tableStyleId'))
        if sid is not None:
            sid.text = '{2D5ABB26-0587-4C30-8999-92F81FD0307C}'
        for j, w in enumerate(widths):
            tbl.columns[j].width = px(w)
        for i, row_ in enumerate(rows):
            tbl.rows[i].height = px(heights[i])
            for j, val in enumerate(row_):
                cell = tbl.cell(i, j)
                st = dict(size=22, color=TEXT, bold=False, font=None, fill=None, left=18, align=LEFT)
                if i == 0:
                    st.update(size=19, color=ON_SPOT, bold=True, font=HEAD, fill=header_fill or SPOT)
                if style:
                    st.update(style(i, j, val) or {})
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                cell.margin_left, cell.margin_right = px(st['left']), px(12)
                cell.margin_top = cell.margin_bottom = px(4)
                par = cell.text_frame.paragraphs[0]
                par.alignment = st['align']
                par.line_spacing = LS_TIGHT
                run = par.add_run()
                run.text = val
                run.font.size, run.font.bold = fs(st['size']), st['bold']
                if st['font']:
                    run.font.name = st['font']
                paint(run.font.color, st['color'])
                if st['fill'] is not None:
                    cell.fill.solid()
                    paint(cell.fill.fore_color, st['fill'])
                else:
                    cell.fill.background()
                tcpr = cell._tc.get_or_add_tcPr()
                if i and i < len(rows):
                    ln = etree.Element(qn('a:lnB'))
                    ln.set('w', str(int(fs(1.25))))
                    sf = etree.SubElement(ln, qn('a:solidFill'))
                    etree.SubElement(sf, qn('a:schemeClr')).set('val', 'accent5')
                    tcpr.insert(0, ln)
        return frame

    # ------------------------------------------------------------ Opening
    s, t = new('Opening', blue)
    pill = box(s, -240, 96, 1040, 464, WHITE, 232, 'Title pill')
    s.shapes._spTree.remove(pill._element)
    s.shapes._spTree.insert(2, pill._element)
    set_title(s, 'Beyond\nSkia', 112, 72, 126, 640, 250, INK)
    text(s, 72, 416, 610, 90, 'GPU scheduling and profiling with Impeller on Android 10+', 28, GREY, align=LEFT, spacing=1.1)
    photo = s.shapes.add_picture(os.path.join(L, 'speaker.jpg'), px(868), px(96), px(340), px(400))
    photo._element.find('.//' + qn('p:cNvPr')).set('descr', 'Collins Munene')
    geom = photo._element.find('.//' + qn('a:prstGeom'))
    geom.set('prst', 'round2SameRect')
    av = geom.find(qn('a:avLst'))
    for key, val in (('adj1', 50000), ('adj2', 0)):
        gd = etree.SubElement(av, qn('a:gd'))
        gd.set('name', key)
        gd.set('fmla', f'val {val}')
    text(s, 868, 510, 400, 40, 'Collins Munene', 30, WHITE, True, HEAD, LEFT)
    text(s, 868, 550, 404, 32, 'DevOps and Software Engineer, Shipht', 20, WHITE, align=LEFT)

    # ------------------------------------------------------------ The map
    s, t = new()
    set_title(s, 'Impeller fixed one kind of jank.', 62, ML, 50, CW, 76)
    text(s, ML, 126, CW, 44, 'So what is still making frames late?', 32, SUB, align=LEFT, spacing=1.0)
    tiles = (('blue', 'circle-check', 'The kind it fixed', 'Compilation jank', 'A new effect makes a GPU program compile inside a frame. It freezes once, then it is gone.'),
             ('red', 'flame', "The kind it didn't", 'Drawing cost', 'Too many points, draws and layers. It is paid on every frame, for as long as the screen animates.'),
             ('spot', 'search', 'How to tell them apart', 'Profile it', 'Which thread is late? Which event? Which code? One fix, then measure again.'))
    for i, (kind, ic, k, h_, d) in enumerate(tiles):
        x, w = col(i, 3)
        if kind == 'spot':
            box(s, x, 192, w, 452, SPOT, 28, h_)
            fg = ON_SPOT
        else:
            hero(s, x, 192, w, 452, kind, h_, 28)
            fg = WHITE
        ico(s, ic, x + 28, 220, 64, fg if kind == 'spot' else WHITE, RGBColor(0, 0, 0) if (kind == 'spot' and dark) else (TEXT if kind == 'spot' else (EVENT if kind == 'blue' else RED)))
        text(s, x + 28, 306, w - 56, 30, k, 22, fg, align=LEFT, spacing=1.0)
        text(s, x + 28, 340, w - 56, 56, h_, 40, fg, True, HEAD, LEFT, spacing=1.0, track=-60)
        text(s, x + 28, 404, w - 56, 220, d, 29, fg, align=LEFT, spacing=LS)

    # ------------------------------------------------------------ How Flutter draws
    s, t = head(TRACK[0], 'Dart and the engine are different things.', 'How Flutter draws')
    rows_ = ((128, 112, 'layers', 'Framework', 'Dart', ('Material,\nCupertino', 'Widgets', 'Rendering', 'Animation, Painting,\nGestures'), 'You write here', 'Widgets, layout and paint() are all Dart.', False),
             (264, 112, 'settings', 'Engine', 'C++', ('Dart runtime', 'Impeller', 'Text layout', 'Platform\nchannels'), 'It ships inside your app', 'It runs your Dart, renders your frames and lays out text.', True),
             (388, 96, 'smartphone', 'Embedder', 'Java and C++', ('FlutterActivity,\nFlutterView', 'Rendering\nsurface', 'Input, lifecycle,\nthreads'), 'It hosts the engine', 'It provides the surface, input and threads.', False))
    for y, h, ic, name, lang, labels, a, b, hot in rows_:
        card(s, ML, y, CW, h, ACC_T if hot else CARD, name)
        ico(s, ic, ML + 18, y + (h - 52) / 2, 52, ACC if hot else BG, ON_ACC if hot else ACC)
        text(s, ML + 84, y + (h - 60) / 2, 150, 34, name, 26, TEXT, True, HEAD, LEFT, spacing=1.0, track=-30)
        text(s, ML + 84, y + (h - 60) / 2 + 34, 150, 26, lang, 19, SUB, align=LEFT, spacing=1.0)
        n = len(labels)
        for i, lab in enumerate(labels):
            cx, cw = col(i, n, ML + 240, 520, 8)
            is_imp = lab == 'Impeller'
            chip(s, cx, y + 14, cw, h - 28, lab, ACC if is_imp else BG, ON_ACC if is_imp else TEXT, 18 if len(lab) > 12 else 20, True, 12)
        text(s, ML + 780, y + 14, 370, 30, a, 23, TEXT, True, HEAD, LEFT, spacing=1.0, track=-20)
        text(s, ML + 780, y + 44, 370, h - 50, b, 20, SUB, align=LEFT, spacing=LS)
    chip(s, ML + 420, 240, 160, 24, 'dart:ui', SPOT, ON_SPOT, 18, False, 12, MONO)
    card(s, ML, 496, CW, 56, HAIR, 'Android', 18)
    ico(s, 'cpu', ML + 18, 504, 40, None, TEXT)
    text(s, ML + 84, 496, 1000, 56, 'Android: SurfaceFlinger, GPU driver, GPU', 23, TEXT, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=1.0)
    point(s, "Flutter doesn't ask Android to draw widgets. It asks the GPU to draw triangles.", 'triangle', 568, 80, 27)

    s, t = head(TRACK[0], 'One frame, from vsync to pixels.')
    groups = ((ML, 440, 'code', 'Main thread', 'DevTools: UI. Perfetto: app main thread.', ('Animate', 'Build', 'Layout', 'Paint', 'Composite'), CARD, 'paint() draws nothing.', 'It records a DisplayList: a list of drawing commands.'),
              (ML + 456, 404, 'zap', 'Raster thread', 'DevTools: Raster. Perfetto: 1.raster.', ('Replay the DisplayList', 'Bind or build pipelines', 'Tessellate paths', 'Record and submit commands'), ACC_T, 'Raster time is CPU time.', 'It prepares GPU work, plus any wait on the GPU.'),
              (ML + 876, 292, 'cpu', 'GPU', 'Hardware.', ('Run commands', 'Write pixels', 'SurfaceFlinger', 'Display'), CARD, 'Not a Flutter thread.', 'It runs later, on its own.'))
    for i, (x, w, ic, name, sub, labels, fill, h_, d) in enumerate(groups):
        g = card(s, x, 128, w, 520, fill, name)
        i1 = ico(s, ic, x + 20, 144, 52, ACC, ON_ACC)
        a = text(s, x + 84, 144, w - 96, 30, name, 27, TEXT, True, HEAD, LEFT, spacing=1.0, track=-30)
        b = text(s, x + 84, 174, w - 96, 26, sub, 18, SUB, align=LEFT, spacing=1.0)
        hh = (250 - (len(labels) - 1) * 8) / len(labels)
        chips = [chip(s, x + 20, 212 + j * (hh + 8), w - 40, hh, lab, BG, TEXT, 21, True, 12) for j, lab in enumerate(labels)]
        k = text(s, x + 20, 480, w - 36, 36, h_, 27, TEXT, True, HEAD, LEFT, spacing=1.0, track=-40)
        m = text(s, x + 20, 518, w - 36, 120, d, 22, SUB, align=LEFT, spacing=LS)
        extra = []
        if i:
            disc = box(s, x - 22, 320, 28, 28, TEXT, 14, 'Next')
            extra = [fx(disc), fx(ico(s, 'chevron-right', x - 18, 324, 20, None, BG))]
        t.click(*extra, fx(g), fx(i1), fx(a), fx(b), *[fx(c_, delay=110 * j) for j, c_ in enumerate(chips)], fx(k, delay=500), fx(m, delay=500))
    source(s, 'Since Flutter 3.29, Dart runs on the platform main thread. DevTools still calls that work UI.')

    s, t = head(TRACK[0], 'Every frame gets 8.3 ms.', sub='120 refreshes a second. Two threads work on each frame, and they overlap.')
    X0, WW = 320, 620
    SCALE = WW / 33.33

    def lanes(y, ui, raster, rc):
        panel = s.shapes.add_group_shape()
        bg = panel.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px(X0), px(y), px(WW), px(124))
        bg.adjustments[0] = 0.12
        bg.fill.solid()
        paint(bg.fill.fore_color, BG)
        bg.line.fill.background()
        for n in range(1, 4):
            ln = panel.shapes.add_connector(1, px(X0 + n * 8.33 * SCALE), px(y), px(X0 + n * 8.33 * SCALE), px(y + 124))
            paint(ln.line.color, AXIS)
            ln.line.width = fs(1.5)
        for spans, yy, c in ((ui, y + 16, TEXT), (raster, y + 68, rc)):
            for start, ms in spans:
                if start >= 33.33:
                    continue
                r = panel.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px(X0 + start * SCALE), px(yy), px(max(min(ms, 33.33 - start) * SCALE - 3, 3)), px(40))
                r.adjustments[0] = 0.16
                r.fill.solid()
                paint(r.fill.fore_color, c)
                r.line.fill.background()
        panel.name = 'Frames on the UI and raster lanes'
        text(s, X0 - 64, y + 22, 56, 28, 'UI', 18, SUB, align=RIGHT, spacing=1.0)
        text(s, X0 - 64, y + 74, 56, 28, 'Raster', 18, SUB, align=RIGHT, spacing=1.0)
        return panel
    rows2 = ((160, 'target', 'Target', '~4 + ~4 ms', [(k * 8.33, 4) for k in range(4)], [(k * 8.33 + 4, 4) for k in range(4)], ACC, 'One refresh', 'A frame fits in one refresh. Lowest latency, with headroom.', ACC_T, ACC, CARD),
             (324, 'gauge', 'Limit', '8.3 ms each', [(k * 8.33, 8) for k in range(4)], [(k * 8.33, 8) for k in range(1, 4)], ACC, 'Still 120 fps', 'The threads overlap, but each frame arrives later.', BG, TEXT, CARD),
             (488, 'flame', 'Over', 'Real broken frames', trace['broken']['ui'], trace['broken']['raster'], RED, '1000 ÷ 28 = 36 fps', 'The slowest thread sets the frame rate.', RED, WHITE, RED_T))
    for y, ic, h_, d, ui, ra, rc, a, b, tile, tc, fill in rows2:
        c0 = card(s, ML, y, CW, 152, fill, h_)
        i0 = ico(s, ic, ML + 18, y + 18, 44, tile, tc)
        l1 = text(s, ML + 18, y + 68, 180, 40, h_, 32, RED if h_ == 'Over' else TEXT, True, HEAD, LEFT, spacing=1.0, track=-50)
        l2 = text(s, ML + 18, y + 108, 190, 28, d, 18, SUB, align=LEFT, spacing=1.0)
        p = lanes(y + 14, ui, ra, rc)
        r1 = text(s, 958, y + 26, 250, 34, a, 25, TEXT, True, HEAD, LEFT, spacing=1.0, track=-30)
        r2 = text(s, 958, y + 62, 250, 80, b, 20, SUB, align=LEFT, spacing=LS)
        t.click(fx(c0), fx(i0), fx(l1), fx(l2), fx(p, 'left', dur=900), fx(r1, delay=600), fx(r2, delay=600))
    source(s, 'Each faint line is a 120 Hz deadline. Top rows drawn to scale. Bottom row is a system trace from the phone.')

    # ------------------------------------------------------------ Engine diagrams
    AX, AW, CX0, CWD = 304, 920, 564, 646

    def build_card(s, fill):
        c = card(s, ML, 164, 232, 484, fill, 'When Flutter is built', 22)
        return c

    def lane_heads(s):
        ico(s, 'hammer', ML, 128, 28, None, SUB)
        text(s, ML + 36, 128, 200, 28, 'When Flutter is built', 21, SUB, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=1.0)
        ico(s, 'play', AX, 128, 28, None, SUB)
        text(s, AX + 36, 128, 400, 28, 'When the app runs', 21, SUB, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=1.0)

    def row(s, y, h, ic, name, sub=''):
        card(s, AX, y, AW, h, CARD, name, 20)
        ico(s, ic, AX + 14, y + (h - 42) / 2, 42, BG, ACC)
        if sub:
            text(s, AX + 68, y + 8, 186, 28, name, 22, TEXT, True, HEAD, LEFT, spacing=1.0, track=-20)
            text(s, AX + 68, y + 36, 188, h - 40, sub, 18, SUB, align=LEFT, spacing=1.0)
        else:
            text(s, AX + 68, y, 186, h, name, 22, TEXT, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=1.0, track=-20)

    def row_chips(s, y, h, labels, fill=BG, color=TEXT):
        out = []
        for i, lab in enumerate(labels):
            x, w = col(i, len(labels), CX0, CWD, 8)
            out.append(chip(s, x, y, w, h, lab, fill, color, 20, True, 12))
        return out

    def down(s, *ys):
        for y in ys:
            ico(s, 'chevron-down', AX + AW / 2 - 9, y, 18, None, SUB)

    s, t = head(TRACK[1], 'The engine before: Skia on OpenGL ES.', 'Before: Skia')
    lane_heads(s)
    empty = build_card(s, BG)
    outline(empty, AXIS, 2, 'dash')
    ico(s, 'ban', ML + 84, 330, 64, None, AXIS)
    text(s, ML + 20, 410, 192, 150, 'Nothing here. No shader for your screen exists yet.', 23, SUB, align=CENTER, spacing=LS)
    row(s, 164, 62, 'smartphone', 'Platform thread')
    row_chips(s, 174, 42, ['Android views, input, lifecycle. It talks to Dart by message.'])
    row(s, 244, 86, 'code', '1.ui thread', 'Dart')
    row_chips(s, 256, 62, ['Animate', 'Build', 'Layout', 'Paint'])
    row(s, 348, 124, 'zap', '1.raster thread', 'Skia. Keeps a raster cache for stable layers.')
    cc = row_chips(s, 362, 96, ['Replay the\nrecording', 'Write a\nshader (SkSL)', 'Driver\ncompiles it', 'Draw'])
    row(s, 490, 70, 'settings', 'OpenGL ES', 'The driver')
    row_chips(s, 500, 50, ['Hides the work, and decides when it happens.'])
    row(s, 578, 70, 'cpu', 'GPU')
    row_chips(s, 588, 50, ['Runs the compiled program and fills the pixels.'])
    down(s, 226, 330, 472, 560)
    red1 = grad(chip(s, cc[1].left / 9525, 362, cc[1].width / 9525, 96, 'Write a\nshader (SkSL)', RED, WHITE, 20, True, 12), 'accent3', False)
    red2 = grad(chip(s, cc[2].left / 9525, 362, cc[2].width / 9525, 96, 'Driver\ncompiles it', RED, WHITE, 20, True, 12), 'accent3', False)
    t.click(fx(red1), fx(red2, delay=300))
    source(s, 'Android, simplified. Sky drew with Skia from 2015. Flutter 1.0 shipped on it in December 2018.')

    s, t = head(TRACK[1], 'Compilation jank.', size=46, sub='A shader is a small GPU program. The driver must compile it for that exact chip before it can run.')
    steps = ['A new mix of paint,\nblend and clip', 'Skia writes\nSkSL', 'Translated\nto GLSL', 'Driver compiles it,\non raster thread', 'The frame misses\nits deadline']
    shapes = []
    for i, label in enumerate(steps):
        x, w = col(i, 5, gap=24)
        c = chip(s, x, 160, w, 76, label, RED if i == 4 else CARD, WHITE if i == 4 else TEXT, 20, True, 16)
        if i == 4:
            grad(c, 'accent3', False)
        shapes.append(c)
        if i:
            shapes.append(ico(s, 'chevron-right', x - 22, 188, 20, None, SUB))
    t.click(*[fx(c, delay=i * 110) for i, c in enumerate(shapes)])
    panel = box(s, ML, 250, CW, 148, SPOT, RAD, 'One real frame')
    PX, PW = ML + 28, CW - 56
    K = PW / 1820
    bud = box(s, PX, 270, 8.33 * K, 26, PREVIEW, 0, 'One frame budget, 8.3 ms')
    budl = text(s, PX + 16, 268, 700, 30, '8.3 ms: one frame’s budget', 22, PREVIEW, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=1.0)
    prog = s.shapes.add_group_shape()
    for i in range(118):
        r = prog.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(PX + i * 14.525 * K), px(304), px(14.6 * K - 1.5), px(46))
        r.fill.solid()
        paint(r.fill.fore_color, RED)
        r.line.fill.background()
    prog.name = '118 shader programs, one frame, drawn to scale'
    lab = text(s, PX, 356, PW, 30, '118 programs, 14.6 ms each. One frame: 1,820 ms. Real trace, drawn to scale: Skia, 144 new effects.', 21, ON_SPOT, align=LEFT, spacing=1.0)
    t.click(fx(bud), fx(budl), fx(prog, 'left', dur=1800), fx(lab, delay=1500))
    facts = (('repeat', 'Once per shader, per install', 'The cache is keyed to the engine version, so a Flutter upgrade starts your users cold again.'), ('eye-off', 'Your own phone hides it', "Your test phone's cache is warm. Your user's first run isn't, and a test may never hit it."), ('code', "You can't fix it in Dart", 'It runs on the raster thread, so Dart has finished. The UI bar stays green.'))
    for i, (ic, h_, d) in enumerate(facts):
        x, w = col(i, 3)
        c = card(s, x, 412, w, 236, CARD, h_)
        ii = ico(s, ic, x + 22, 428, 44)
        a, b = stacked(s, x + 22, 480, w - 40, h_, d, 24, 21)
        t.click(fx(c), fx(ii), fx(a), fx(b))

    s, t = head(TRACK[1], 'Three years of workarounds.')
    for i, (yr, ic, h_, cmd, why) in enumerate((('2019', 'flag', 'Warm up at startup', 'PaintingBinding.shaderWarmUp', 'Draw common shapes offscreen. You had to guess the calls, and startup got slower.'),
                                                ('2020', 'package', 'Record and bundle', '--cache-sksl --bundle-sksl-path', 'Flutter 1.20. Tied to device and driver. Captured again after every engine upgrade.'),
                                                ('2021', 'x', 'Default removed', 'Warm-up is now opt-in', "The default warm-up came out. It didn't scale."))):
        x, w = col(i, 3)
        card(s, x, 128, w, 268, CARD, yr)
        big(s, x + 24, 142, 200, 62, yr, 54, ACC, LEFT)
        ico(s, ic, x + w - 68, 146, 44, BG, ACC)
        text(s, x + 24, 208, w - 44, 34, h_, 27, TEXT, True, HEAD, LEFT, spacing=1.0, track=-30)
        text(s, x + 24, 244, w - 40, 26, cmd, 16.5, SUB, False, MONO if i < 2 else None, LEFT, spacing=1.0)
        text(s, x + 24, 280, w - 44, 110, why, 22, BODY, align=LEFT, spacing=LS)
    box(s, ML, 412, CW, 236, SPOT, RAD, 'Quote')
    text(s, ML + 40, 430, CW - 80, 60, '“requires 0 extra effort from developers”', 44, ON_SPOT, True, HEAD, LEFT, spacing=1.0, track=-90)
    text(s, ML + 40, 490, CW - 80, 34, '“handles all cases that may have never been encountered during any tests or warmups.”', 24, ON_SPOT, align=LEFT, spacing=1.0)
    text(s, ML + 40, 534, CW - 80, 30, 'Flutter issue #32170, May 2019. Closed August 2023, pointing to Impeller.', 21, SUB if dark else HAIR, align=LEFT, spacing=1.0)
    text(s, ML + 40, 578, CW - 80, 44, 'You cannot fix this with a cache. You fix it by not compiling at run time.', 28, PREVIEW, True, HEAD, LEFT, spacing=1.0, track=-30)

    # ------------------------------------------------------------ Now: Impeller
    s, t = head(TRACK[2], 'The engine now: Impeller on Vulkan.', 'Now: Impeller')
    lane_heads(s)
    build_card(s, ACC_T)
    b1 = chip(s, ML + 16, 180, 200, 72, 'GLSL shaders,\na small fixed set', BG, TEXT, 19, True, 14)
    a1 = ico(s, 'chevron-down', ML + 107, 254, 18, None, ACC)
    b2 = grad(chip(s, ML + 16, 274, 200, 54, 'impellerc', EVENT, WHITE, 23, True, 14, MONO), 'accent2')
    a2 = ico(s, 'chevron-down', ML + 107, 330, 18, None, ACC)
    b3 = chip(s, ML + 16, 350, 200, 112, 'SPIR-V for Vulkan\nMetal for iOS\nGLSL ES', BG, TEXT, 19, True, 14)
    a3 = ico(s, 'chevron-down', ML + 107, 464, 18, None, ACC)
    b4 = chip(s, ML + 16, 484, 200, 72, 'Inside the\nengine binary', BG, TEXT, 19, True, 14)
    arrowr = arrow(s, 288, 410, 304, 410, ACC, 4)
    t.click(fx(b1), fx(a1, delay=200), fx(b2, delay=300), fx(a2, delay=500), fx(b3, delay=600), fx(a3, delay=800), fx(b4, delay=900), fx(arrowr, delay=1100))
    row(s, 164, 166, 'code', 'Main thread', 'Dart and Android, together, since Flutter 3.29. DevTools still says UI.')
    row_chips(s, 174, 42, ['Android views, input, lifecycle. Same thread as Dart.'])
    row_chips(s, 224, 94, ['Animate', 'Build', 'Layout', 'Paint:\nDisplayList'])
    row(s, 348, 124, 'zap', '1.raster thread', 'Impeller. No raster cache.')
    cc = row_chips(s, 362, 96, ['Replay the\nDisplayList', 'Bind or build\na pipeline', 'Tessellate\npaths', 'Record\ncommands'])
    row(s, 490, 70, 'settings', 'Vulkan', 'Android 10+')
    row_chips(s, 500, 50, ['Explicit. Impeller says what runs and when.'])
    row(s, 578, 70, 'cpu', 'GPU')
    row_chips(s, 588, 50, ['Runs the commands and fills the pixels.'])
    down(s, 330, 472, 560)
    hot = grad(chip(s, cc[2].left / 9525, 362, cc[2].width / 9525, 96, 'Tessellate\npaths', EVENT, WHITE, 20, True, 12), 'accent2')
    t.click(fx(hot))
    source(s, 'Android 10+ with Vulkan, simplified. The two shader boxes are gone from the raster thread.')

    s, t = head(TRACK[2], 'Skia compiles late. Impeller compiles early.', sub='A pipeline is a compiled shader plus fixed GPU state, such as blending.')
    stages = (('hammer', 'Engine build'), ('package', 'App build'), ('power', 'App start'), ('sparkles', 'First use of an effect'), ('repeat', 'Every frame'))
    LX, LW = ML, 124
    for i, (ic, h_) in enumerate(stages):
        x, w = col(i, 5, LX + LW + 12, CW - LW - 12, 10)
        ico(s, ic, x, 164, 34, None, SUB)
        text(s, x + 42, 164, w - 42, 34, h_, 19, TEXT, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=0.92)
    arrow(s, LX + LW + 12, 208, ML + CW, 208, AXIS, 2.5)
    skia = ('No shader for\nyour screen', 'Your .frag stays\nas SkSL text', 'Warm-up, if\nyou wrote one', 'Write + compile,\nin the frame:\n14.6 ms each', 'Bind the\ncached program')
    imp = ('impellerc compiles\nthe fixed shaders', 'impellerc compiles\nyour .frag too', 'Most pipelines\nare built', 'Build a missing\npipeline, in the frame:\n2.2 ms each', 'Bind a\nbuilt pipeline')
    text(s, ML, 268, LW, 50, 'Skia', 32, TEXT, True, HEAD, LEFT, spacing=1.0, track=-50)
    text(s, ML, 464, LW, 50, 'Impeller', 28, ACC, True, HEAD, LEFT, spacing=1.0, track=-50)
    sk_shapes, im_shapes = [], []
    for i in range(5):
        x, w = col(i, 5, LX + LW + 12, CW - LW - 12, 10)
        hotk = i == 3
        c = chip(s, x, 222, w, 204, skia[i], RED if hotk else CARD, WHITE if hotk else (SUB if i < 2 else TEXT), 21, True, 20)
        if hotk:
            grad(c, 'accent3', False)
        sk_shapes.append(c)
        hoti = i in (0, 1)
        c = chip(s, x, 438, w, 210, imp[i], EVENT if hoti else (ACC_T if i == 3 else CARD), WHITE if hoti else TEXT, 21, True, 20)
        if hoti:
            grad(c, 'accent2')
        im_shapes.append(c)
    t.click(*[fx(c, delay=i * 120) for i, c in enumerate(sk_shapes)])
    t.click(*[fx(c, delay=i * 120) for i, c in enumerate(im_shapes)])
    source(s, 'From system traces of one cold reveal, 144 effects. Built pipelines are also saved to disk (vkcache).')

    s, t = head(TRACK[2], 'One rule. One platform at a time.', sub='No shader compilation while the app runs.')
    X0_, W0 = 232, 972
    xpos = lambda y, m=1: X0_ + (y - 2018 - 11 / 12 + (m - 1) / 12) * W0 / (2027 - 2018 - 11 / 12)
    for yr in range(2019, 2027):
        text(s, xpos(yr) - 30, 160, 60, 26, str(yr), 18, SUB, spacing=1.0)

    def lane(y, ic, name, parts, caption):
        c0 = card(s, ML, y, CW, 132, CARD, name)
        i0 = ico(s, ic, ML + 18, y + 16, 44, BG, ACC)
        lab = text(s, ML + 18, y + 68, 150, 40, name, 28, TEXT, True, HEAD, LEFT, spacing=1.0, track=-40)
        g = s.shapes.add_group_shape()
        g.name = f'{name} renderer timeline'
        for (y1, m1), (y2, m2), kind in parts:
            r = g.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(xpos(y1, m1)), px(y + 18), px(xpos(y2, m2) - xpos(y1, m1)), px(54))
            r.fill.solid()
            if kind == 'pv':
                r.fill.fore_color.rgb = PREVIEW
            else:
                paint(r.fill.fore_color, TEXT if kind == 'sk' else EVENT)
            r.line.fill.background()
        cap = text(s, X0_, y + 84, W0, 30, caption, 21, BODY, align=LEFT, spacing=1.0)
        return c0, i0, lab, g, cap
    all_lanes = [lane(190, 'smartphone', 'iOS', [((2018, 12), (2023, 1), 'sk'), ((2023, 1), (2023, 5), 'pv'), ((2023, 5), (2027, 1), 'im')], 'Preview in 3.7. Default in 3.10, May 2023. Skia removed in 3.29, Feb 2025.'),
                 lane(332, 'smartphone', 'Android', [((2018, 12), (2023, 11), 'sk'), ((2023, 11), (2024, 12), 'pv'), ((2024, 12), (2027, 1), 'im')], 'Preview in 3.16. Default on Vulkan in 3.27, Dec 2024. Android 10+ today.'),
                 lane(474, 'monitor', 'Desktop', [((2022, 2), (2026, 8), 'sk'), ((2026, 8), (2027, 1), 'im')], 'Default in 3.47, 2026.')]
    for c0, i0, lab, g, cap in all_lanes:
        t.click(fx(c0), fx(i0), fx(lab), fx(g, 'left', dur=1100), fx(cap, delay=500))
    for i, (name, c) in enumerate((('Skia', TEXT), ('Impeller preview', PREVIEW), ('Impeller default', EVENT))):
        x = 330 + i * 190
        box(s, x, 626, 22, 14, c, 4, f'{name} key')
        text(s, x + 30, 619, 160, 28, name, 19, SUB, align=LEFT, spacing=1.0)
    source(s, 'Flutter docs and release notes. Web still renders with Skia. Older Android stays on the legacy renderer.')

    s, t = head(TRACK[2], 'A trade, not a free upgrade.')
    trade = [('', 'Before', 'Now', 'What it means for you'),
             ('Shaders', 'Compiled in the frame', 'Compiled with the engine', 'No first-use shader compile'),
             ('Cache', 'Automatic raster cache', 'No raster cache', 'Expensive drawing repeats every frame'),
             ('Paths', 'GPU and mask techniques', 'Tessellated on the CPU', 'Complex paths cost raster-thread time'),
             ('GPU API', 'OpenGL ES, driver decides', 'Vulkan, explicit commands', 'The cost is the volume you record'),
             ('Dart', 'Its own 1.ui thread', 'Main thread, since 3.29', 'Blocking Dart blocks Android too')]

    def trade_style(i, j, val):
        if i == 0:
            return dict(fill=EVENT, color=WHITE, size=21) if j == 2 else None
        if j == 0:
            return dict(size=27, bold=True, font=HEAD, left=72)
        if j == 1:
            return dict(color=SUB)
        if j == 2:
            return dict(color=ACC, bold=True, font=HEAD, fill=ACC_T, size=24)
        return dict()
    table(s, ML, 128, (230, 300, 318, 320), (50, 94, 94, 94, 94, 94), trade, trade_style, 'What changed and what it costs')
    for i, ic in enumerate(('zap', 'database', 'spline', 'cpu', 'code')):
        ico(s, ic, ML + 14, 178 + i * 94 + 23, 46, CARD, ACC)

    # ------------------------------------------------------------ The proof
    s, t = head(TRACK[3], 'Same app. Same phone. Two renderers.', 'The proof', sub='Shader Storm: 144 tiles, each its own mix of paint settings, appear in one frame.')
    card(s, ML, 160, CW, 76, CARD, 'Engine logs', 18)
    ico(s, 'terminal', ML + 16, 176, 44, BG, ACC)
    text(s, ML + 76, 160, CW - 90, 76, [[('Skia build     ', {'color': SUB}), ('The application opted out of Impeller', {'color': TEXT})], [('Impeller build ', {'color': SUB}), ('Using the Impeller rendering backend (Vulkan).', {'color': ACC})]], 20, TEXT, False, MONO, LEFT, MSO_ANCHOR.MIDDLE, spacing=LS_CODE)
    TX1, TX2, TW = ML + 180, ML + 180 + 502, 486
    for x, h_ in ((TX1, 'First reveal'), (TX2, 'Second time: will it freeze?')):
        text(s, x, 246, TW, 30, h_, 23, SUB, True, HEAD, LEFT, spacing=1.0)
    for y, h_, c in ((282, 'Skia', TEXT), (468, 'Impeller', ACC)):
        text(s, ML, y + 60, 170, 50, h_, 34, c, True, HEAD, LEFT, spacing=1.0, track=-50)
    for x, y in ((TX1, 282), (TX2, 282), (TX1, 468), (TX2, 468)):
        card(s, x, y, TW, 174 if y == 282 else 180, CARD, 'Score')

    def score(x, y, h, value, tile=None, color=TEXT):
        shapes_ = []
        if tile:
            shapes_.append(hero(s, x, y, TW, h, tile, value))
        shapes_.append(big(s, x, y + (h - 110) / 2, TW, 110, value, 92, color))
        return shapes_
    n1 = score(TX1, 282, 174, '1,863 ms', 'red', WHITE)
    n2 = score(TX2, 282, 174, '23 ms')
    n3 = score(TX1, 468, 180, '145 ms', 'blue', WHITE)
    n4 = score(TX2, 468, 180, '48 ms', None, ACC)
    t.click(*[fx(x) for x in n1])
    t.click(*[fx(x) for x in n2])
    t.click(*[fx(x) for x in n3], *[fx(x, delay=400) for x in n4])
    source(s, 'Worst frame, median of 3 rounds. Skia on OpenGL ES, Impeller on Vulkan. Infinix X6873, Mali-G615, 120 Hz.')

    s, t = head(TRACK[3], "Skia's freeze grows. Impeller's barely does.")
    card(s, ML, 128, 760, 520, CARD, 'Chart')
    text(s, ML + 24, 142, 500, 28, 'Freeze in ms. Lower is better.', 20, SUB, align=LEFT, spacing=1.0)
    chart = line_chart(s, ML + 12, 170, 736, 430)
    text(s, ML + 610, 186, 130, 34, 'Skia', 25, TEXT, True, HEAD, RIGHT, spacing=1.0)
    text(s, ML + 610, 490, 130, 34, 'Impeller', 25, ACC, True, HEAD, RIGHT, spacing=1.0)
    text(s, ML + 12, 604, 736, 30, 'New effects on screen', 20, SUB, spacing=1.0)
    t.click(fx(chart, 'left', dur=1200))
    RX, RW = 832, 392
    hero(s, RX, 128, RW, 216, 'blue', '13 times shorter')
    big(s, RX + 24, 138, RW - 48, 116, '13×', 104, WHITE, LEFT)
    text(s, RX + 24, 258, RW - 48, 76, 'shorter freeze at 144 new effects: 1,863 against 145 ms.', 23, WHITE, True, HEAD, LEFT, spacing=LS, track=-20)
    for y, ic, h_, d in ((360, 'refresh-cw', 'After a relaunch', 'Disk caches help both: Skia 102 ms, Impeller 73 ms.'), (504, 'rocket', 'After a Flutter upgrade', "Skia's cache is keyed to the engine version, so users go cold again.")):
        card(s, RX, y, RW, 144 if y == 504 else 128, CARD, h_)
        ico(s, ic, RX + 18, y + 16, 40)
        text(s, RX + 68, y + 16, RW - 84, 40, h_, 24, TEXT, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=1.0, track=-20)
        text(s, RX + 18, y + 64, RW - 36, 76, d, 21, SUB, align=LEFT, spacing=LS)

    s, t = head(TRACK[3], "The cost shrank and moved. It didn't vanish.")
    card(s, ML, 128, 700, 424, CARD, 'Compiling, one cold reveal')
    text(s, ML + 24, 142, 650, 34, 'Why it barely grows', 28, TEXT, True, HEAD, LEFT, spacing=1.0, track=-40)
    text(s, ML + 24, 188, 400, 30, 'Skia: 118 programs', 24, TEXT, True, HEAD, LEFT, spacing=1.0)
    n1 = big(s, ML + 400, 180, 276, 40, '1,714 ms', 36, TEXT, RIGHT)
    g1 = squares(s, ML + 24, 226, 118, TEXT, per_row=27, cell=24)
    l1 = text(s, ML + 24, 350, 650, 28, '14.6 ms each', 21, SUB, align=LEFT, spacing=1.0)
    text(s, ML + 24, 398, 400, 30, 'Impeller: 40 pipelines', 24, ACC, True, HEAD, LEFT, spacing=1.0)
    n2 = big(s, ML + 400, 390, 276, 40, '87 ms', 36, ACC, RIGHT)
    g2 = squares(s, ML + 24, 436, 40, ACC, per_row=27, cell=24)
    l2 = text(s, ML + 24, 496, 650, 28, '2.2 ms each', 21, SUB, align=LEFT, spacing=1.0)
    t.click(fx(g1, 'left', dur=1000), fx(n1, delay=700), fx(l1, delay=700), fx(g2, 'left', dur=500, delay=1000), fx(n2, delay=1300), fx(l2, delay=1300))
    card(s, ML + 716, 128, 452, 424, CARD, 'Second reveal')
    text(s, ML + 740, 142, 410, 34, 'Predictable. Not always faster.', 26, TEXT, True, HEAD, LEFT, spacing=1.0, track=-40)
    bchart = bar_chart(s, ML + 728, 186, 428, 190, ['Skia', 'Impeller'], (23, 48), (TEXT, ACC), '0', 70, 'Second reveal', 'Second reveal: Skia 23 ms, Impeller 48 ms')
    bchart.chart.category_axis.tick_labels.font.size = fs(21)
    bchart.chart.plots[0].data_labels.font.size = fs(26)
    text(s, ML + 740, 384, 410, 160, ['Worst frame in ms, the same 144 effects redrawn in the same session.', 'Once warm, Skia can win. Impeller moved the worst work out of the frame.'], 21, BODY, align=LEFT, spacing=LS, gap=8)
    t.click(fx(bchart, 'left', dur=800))
    point(s, 'Both on the raster thread, inside the frame. Impeller only builds from what is compiled.', 'zap', 568, 80, 26)
    source(s, 'Left: system traces of one cold reveal at 144 effects, tracing on. Right: median of 3 rounds, tracing off.')

    # ------------------------------------------------------------ Inside a frame
    s, t = head(TRACK[4], 'Tessellation: how a path becomes triangles.', 'Inside a frame', sub='The GPU fills triangles, so the CPU must cut every path into triangles first.')
    pts, edges = strip_edges(13)
    scale_ = 0.52
    labels = (('1', 'Path', 'What paint() asks for: lines and curves.'), ('2', 'Points', 'Curves flatten into points. Larger on screen means more points.'),
              ('3', 'Vertices', 'Two per point, half the stroke width each side. Two more at a corner.'), ('4', 'Triangles', 'One strip. v vertices make v − 2 triangles.'))
    panels = []
    for i, (n, h_, d) in enumerate(labels):
        x, w = col(i, 4)
        last_panel = i == 3
        c0 = card(s, x, 160, w, 272, ACC_T if last_panel else CARD, f'{h_} drawing')
        tx = lambda a: x + (w - 460 * scale_) / 2 - 5 * scale_ + a * scale_
        ty = lambda b: 182 + b * scale_
        items = []
        if i == 0:
            items.append(polyline(s, [(tx(a), ty(b)) for a, b in bezier()], TEXT, 5, 'A smooth path'))
        elif i == 1:
            items.append(dots(s, [(tx(a), ty(b)) for a, b in pts], ACC, 8, 'Points along the path'))
        elif i == 2:
            items.append(dots(s, [(tx(a), ty(b)) for pair in edges for (a, b) in pair], ACC, 6, 'Two vertices per point'))
        else:
            g = s.shapes.add_group_shape()
            for (a, b), (c, e) in zip(edges, edges[1:]):
                for tri in ((a, b, c), (b, c, e)):
                    vv = [(tx(u), ty(w_)) for u, w_ in tri]
                    fb = g.shapes.build_freeform(px(vv[0][0]), px(vv[0][1]), scale=1.0)
                    fb.add_line_segments([(px(u), px(w_)) for u, w_ in vv[1:]], close=True)
                    tr = fb.convert_to_shape()
                    tr.fill.solid()
                    paint(tr.fill.fore_color, BG)
                    paint(tr.line.color, ACC)
                    tr.line.width = fs(1.5)
            g.name = 'The path as a triangle strip'
            items.append(g)
        disc = chip(s, x + 16, 288, 34, 34, n, ACC, ON_ACC, 20, True, 17)
        a_ = text(s, x + 58, 288, w - 70, 34, h_, 27, TEXT, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=1.0, track=-30)
        b_ = text(s, x + 16, 328, w - 28, 100, d, 20, SUB, align=LEFT, spacing=LS)
        panels.append((items, disc, a_, b_, c0))
    for items, disc, a_, b_, c0 in panels:
        t.click(fx(c0), *[fx(k, 'left', dur=900) for k in items], fx(disc), fx(a_), fx(b_))
    fact_items = (('cpu', 'On the CPU, raster thread'), ('memory-stick', 'Copied to per-frame memory'), ('send', 'One draw for the GPU'), ('repeat', 'Every frame. No cache.'))
    fact_fx = []
    for i, (ic, lab) in enumerate(fact_items):
        x, w = col(i, 4)
        c = card(s, x, 444, w, 64, CARD, lab, 16)
        ii = ico(s, ic, x + 12, 456, 40, BG, ACC)
        tt = text(s, x + 60, 444, w - 68, 64, lab, 19, TEXT, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=LS_TIGHT)
        fact_fx += [fx(c, delay=i * 110), fx(ii, delay=i * 110), fx(tt, delay=i * 110)]
    t.click(*fact_fx)
    bar_, tile_, words_ = point(s, 'Path is what you ask for. Tessellation is the work Impeller does with it.', 'lightbulb', 520, 128, 28, 'The broken chart: 16 lines × 8,000 points × 2 = at least 256,000 vertices, every frame.')
    t.click(fx(bar_), fx(tile_), fx(words_))
    source(s, 'Illustration. Rules from stroke_path_geometry.cc. Convex fills have a fast path; 4× MSAA smooths edges.')

    s, t = head(TRACK[4], 'The CPU records. The GPU executes.', sub='That handoff is GPU scheduling. A command buffer is a recorded list of GPU work.')
    code(s, ML, 164, 360, 300, ['begin render pass', '  bind pipeline', '  bind vertex buffer', '  bind uniforms', '  draw', '  ...', 'end render pass', 'submit to queue, fence'], 20)
    x0, w0 = 564, 660
    for name, y, ic in (('Raster thread', 164, 'zap'), ('Queue', 268, 'list-ordered'), ('GPU', 372, 'cpu')):
        ico(s, ic, 432, y + 22, 44)
        text(s, 484, y, 80, 92, name, 19, TEXT, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=LS_TIGHT)
        box(s, x0, y, w0, 92, CARD, 18, f'{name} lane')
    seg = lambda frac, width, y, c=ACC: box(s, x0 + w0 * frac, y + 16, w0 * width, 60, c, 12)
    r1, q1, g1 = seg(.02, .30, 164), seg(.31, .05, 268, TEXT), seg(.37, .30, 372)
    r2, q2, g2 = seg(.37, .30, 164), seg(.66, .05, 268, TEXT), seg(.72, .26, 372)
    t.click(fx(r1, 'left', dur=900), fx(q1, delay=900, dur=200), fx(g1, 'left', delay=1100, dur=900), fx(r2, 'left', delay=1100, dur=900), fx(q2, delay=2000, dur=200), fx(g2, 'left', delay=2200, dur=900))
    for i, (ic, h_, d) in enumerate((('pen-tool', 'Record', 'On 1.raster: every bind and draw, for every frame.'), ('send', 'Submit', 'QueueSubmit hands it over and moves on. A fence reports when it is done.'), ('play', 'Execute', 'The GPU runs it while the raster thread starts the next frame.'))):
        x, w = col(i, 3)
        card(s, x, 480, w, 168, CARD, h_)
        ico(s, ic, x + 18, 494, 40)
        text(s, x + 68, 494, w - 80, 40, h_, 26, TEXT, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=1.0, track=-30)
        text(s, x + 18, 544, w - 36, 100, d, 21, SUB, align=LEFT, spacing=LS)
    source(s, 'Illustration of the order of work, not a measured trace.')

    s, t = head(TRACK[4], 'Why a layer costs more than a draw.', sub='Each saveLayer makes the GPU leave the screen, draw offscreen, then come back.')
    card(s, ML, 164, 256, 284, CARD, 'Tiles')
    grid = s.shapes.add_group_shape()
    lit = {(1, 1), (2, 1), (1, 2), (2, 2), (3, 2)}
    for gx in range(5):
        for gy in range(4):
            sq = grid.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px(ML + 26 + gx * 41), px(182 + gy * 34), px(36), px(29))
            sq.adjustments[0] = 0.18
            sq.fill.solid()
            paint(sq.fill.fore_color, ACC if (gx, gy) in lit else (AXIS if dark else HAIR))
            sq.line.fill.background()
    grid.name = 'The screen split into tiles'
    text(s, ML + 22, 326, 216, 116, 'Mobile GPUs draw the screen tile by tile, in fast on-chip memory.', 21, BODY, align=LEFT, spacing=LS)
    FX, FW = 328, 896

    def flow(y, label, color, items, fill):
        c0 = card(s, FX, y, FW, 136, fill, label, 20)
        l0 = text(s, FX + 20, y + 10, 500, 32, label, 24, color, True, HEAD, LEFT, spacing=1.0, track=-30)
        out = [c0, l0]
        for i, (lab, f, c) in enumerate(items):
            x, w = col(i, 4, FX + 20, FW - 40, 26)
            k = chip(s, x, y + 48, w, 74, lab, f, c, 20, True, 14)
            if f == RED:
                grad(k, 'accent3', False)
            elif f == EVENT:
                grad(k, 'accent2')
            out.append(k)
            if i:
                out.append(ico(s, 'chevron-right', x - 23, y + 76, 20, None, SUB))
        return out
    flow(164, 'One render pass', ACC, (('Clear', BG, TEXT), ('All draws, in\ntile memory', BG, TEXT), ('Resolve MSAA\non the chip', BG, TEXT), ('Store once', EVENT, WHITE)), CARD)
    r2s = flow(312, 'With one saveLayer', RED, (('Draws so far', BG, TEXT), ('Store tiles\nto memory', RED, WHITE), ('Offscreen pass:\ndraw, blur, store', BG, TEXT), ('Load tiles back,\ncomposite', RED, WHITE)), RED_T)
    t.click(*[fx(k, delay=i * 70) for i, k in enumerate(r2s)])
    text(s, ML, 460, 96, 36, 'Triggers', 20, SUB, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=1.0)
    pills = (('saveLayer with a filter', 222), ('Opacity over overlapping children', 326), ('ShaderMask', 136), ('BackdropFilter', 160), ('Advanced blends', 172))
    px_ = ML + 92
    for lab, w in pills:
        chip(s, px_, 460, w, 36, lab, HAIR, TEXT, 18, False, 18, 'Inter', pad=4)
        px_ += w + 8
    for i, (ic, h_, d, tile, tc) in enumerate((('activity', 'Measured on the phone', '64 saveLayer and 2 queue submits per frame, costing about 9 ms of raster-thread CPU.', ACC_T, ACC), ('microscope', 'The model, not my trace', "The phone's driver exposes no GPU render stages, so tile stores and loads are not measured.", BG, SUB))):
        x, w = col(i, 2)
        card(s, x, 508, w, 140, CARD, h_)
        ico(s, ic, x + 18, 522, 40, tile, tc)
        text(s, x + 68, 522, w - 80, 40, h_, 24, TEXT, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=1.0, track=-20)
        text(s, x + 18, 570, w - 36, 76, d, 21, SUB, align=LEFT, spacing=LS)

    # ------------------------------------------------------------ What it didn't fix
    s, t = new("What it didn't fix", blue)
    text(s, 72, 66, 1100, 44, "So if compiling shaders isn't the problem, what is?", 30, WHITE, align=LEFT, spacing=1.0)
    set_title(s, "What Impeller\ndidn't fix.", 120, 72, 170, 1136, 270, WHITE)
    for i, (ic, lab) in enumerate((('spline', 'Points'), ('pen-tool', 'Draws'), ('layers', 'Layers'))):
        x = 72 + i * 212
        box(s, x, 498, 196, 76, WHITE, 38, lab)
        ico(s, ic, x + 12, 510, 52, EVENT, WHITE, 26)
        text(s, x + 74, 498, 116, 76, lab, 25, INK, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=1.0, track=-30)

    s, t = head(TRACK[5], 'Nothing is compiling. This is pure drawing cost.')
    data = (('spline', 'Path points', 'The detail you ask for. Impeller tessellates it on the CPU.', (2240, 8480, 32960, 129920)),
            ('pen-tool', 'Draw calls', 'Each records binds and a draw in the command buffer.', (78, 156, 312, 624)),
            ('layers', 'Offscreen layers', 'Each saveLayer adds an offscreen pass.', (8, 16, 32, 64)))
    for i, (ic, h_, d, vals) in enumerate(data):
        x, w = col(i, 3)
        card(s, x, 128, w, 424, CARD, h_)
        ico(s, ic, x + 20, 144, 48)
        text(s, x + 80, 144, w - 96, 48, h_, 28, TEXT, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=1.0, track=-40)
        text(s, x + 20, 202, w - 40, 70, d, 21, SUB, align=LEFT, spacing=LS)
        for j, v in enumerate(vals):
            y = 288 + j * 62
            text(s, x + 20, y, 44, 46, ['1×', '2×', '4×', '8×'][j], 21, SUB, align=LEFT, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0)
            box(s, x + 64, y + 6, max(150 * v / vals[-1], 6), 34, RED if j == 3 else ACC, 8, f'{h_} {v}')
            text(s, x + w - 128, y, 108, 46, f'{v:,}', 25, TEXT, True, HEAD, RIGHT, MSO_ANCHOR.MIDDLE, spacing=1.0, track=-30)
    point(s, 'At 8×: UI 15.9 ms, raster 29.7 ms. Dart finishes. The engine is the one struggling.', 'flame', 568, 80, 26)
    source(s, 'What the painter asks for, from the live counters. Times are p90, median of 3 rounds, on Impeller.')

    s, t = head(TRACK[5], 'Which fix helps most, on its own?')
    card(s, ML, 128, CW, 520, CARD, 'Each fix alone')
    bars = (('flame', 'No fixes', 'The broken chart at 8×', 29.7, RED, False), ('spline', 'Simplify paths', 'Fewer points to tessellate', 18.6, ACC, True), ('pen-tool', 'Batch draws', 'Fewer draw calls', 28.6, AXIS, True),
            ('layers', 'Glow without layers', 'No offscreen passes', 21.2, AXIS, True), ('scissors', 'Isolate repaints', 'Less Dart re-recording', 25.2, AXIS, True))
    BX, BS = 390, 700 / 34
    fxs = []
    for i, (ic, h_, d, v, c, anim) in enumerate(bars):
        y = 150 + i * 90
        ico(s, ic, ML + 18, y + 8, 48, RED_T if i == 0 else BG, RED if i == 0 else ACC)
        text(s, ML + 78, y + 2, 250, 34, h_, 24, TEXT, True, HEAD, LEFT, spacing=1.0, track=-30)
        text(s, ML + 78, y + 36, 250, 28, d, 18, SUB, align=LEFT, spacing=1.0)
        b = box(s, BX, y + 2, v * BS, 60, c, 12, f'{h_}: {v} ms')
        n = text(s, BX + v * BS + 12, y + 2, 100, 60, f'{v}', 32, TEXT, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=1.0, track=-40)
        if anim:
            fxs += [fx(b, 'left', dur=800, delay=(i - 1) * 150), fx(n, delay=(i - 1) * 150 + 600)]
    bud_x = BX + 8.33 * BS
    rule(s, bud_x, 142, bud_x, 604, TEXT, 2.5)
    chip(s, bud_x - 76, 606, 152, 28, '8.3 ms budget', SPOT, ON_SPOT, 17, True, 14)
    t.click(*fxs)
    source(s, 'Raster p90 in ms, each fix alone at 8× on Impeller. Median of 3 rounds; rounds varied, so small gaps mean little.')

    s, t = head(TRACK[5], 'Fix 1: Simplify paths.', sub='It cuts the input to tessellation, and the Dart that builds it.')
    random_state = 7

    def noise(n, w, x, y, amp):
        nonlocal random_state
        out = []
        for k in range(n):
            random_state = (random_state * 1103515245 + 12345) & 0x7fffffff
            jitter = (random_state % 1000) / 1000 - 0.5
            out.append((x + w * k / (n - 1), y + 16 * math.sin(k / n * 9) + 12 * math.sin(k / n * 31) + amp * jitter))
        return out
    LW2 = 500
    card(s, ML, 164, LW2, 134, RED_T, 'Before', 20)
    text(s, ML + 20, 174, LW2 - 40, 30, 'Before: 8,000 points a line', 23, RED, True, HEAD, LEFT, spacing=1.0)
    polyline(s, noise(320, LW2 - 40, ML + 20, 252, 26), RED, 1.25, 'A line with too many points')
    c_after = card(s, ML, 306, LW2, 134, ACC_T, 'After', 20)
    a_ = text(s, ML + 20, 316, LW2 - 40, 30, 'After: at most 2 per pixel column', 23, ACC, True, HEAD, LEFT, spacing=1.0)
    b_ = polyline(s, noise(46, LW2 - 40, ML + 20, 394, 14), ACC, 2.5, 'The same line, simplified')
    t.click(fx(c_after), fx(a_), fx(b_, 'left', dur=900))
    code(s, ML + LW2 + GAP, 164, CW - LW2 - GAP, 276, ['!!Broken: a new path, every frame', 'final path = Path();', 'for (var k = 0; k < 8000; k++) path.lineTo(x(k), y(k));', '', '++Fixed: simplify once, then only move it', 'final xy = decimate(series, plot.width);', 'canvas', '  ..translate(shift, 0)', '  ..drawPath(cached, stroke);'], 17.5)
    for i, (lab, a, b, fill) in enumerate((('Path points', '129,920', '12,032', None), ('Raster p90, ms', '29.7', '18.6', None), ('UI p90, ms', '15.9', '6.3', None))):
        x, w = col(i, 3)
        card(s, x, 454, w, 100, CARD, lab, 20)
        stat(s, x + 20, 464, w - 30, lab, a, b, 38)
    point(s, 'A line 330 px wide keeps about 632 points. The other 7,000 or so never changed the picture.', 'scissors', 568, 80, 24)
    source(s, 'Code condensed from thrash_canvas.dart. Times are p90, median of 3 rounds.')

    s, t = head(TRACK[5], 'Fixes 2 and 3: fewer draws, no layers.')
    cards = ((0, 'pen-tool', 'Batch draws', '640', '161', 'draw calls', '18.6', '13.7', ['!!480 segments, 480 draws', 'canvas.drawPath(segment, paint);', '', '++All segments, one draw', 'canvas.drawVertices(', '  Vertices.raw(triangles, positions,', '    colors: colors), BlendMode.dst, p);'], 'The smallest win. On Vulkan a draw is a few small commands, so volume is the cost.', False),
             (1, 'layers', 'Glow without layers', '64', '0', 'offscreen layers', '13.7', '6.6', ['!!Per dot: a pass, a blur, a composite', 'canvas.saveLayer(bounds,', '  Paint()..imageFilter = blur);', '', '++The same soft edge, in the main pass', 'canvas.drawCircle(c, r,', '  Paint()..shader = Gradient.radial(...));'], 'The biggest raster win. Queue submits fall from 2 to 1 per frame.', True))
    for i, ic, h_, a, b, unit, r1_, r2_, lines, why, win in cards:
        x, w = col(i, 2)
        card(s, x, 128, w, 520, ACC_T if win else CARD, h_, 28)
        ico(s, ic, x + 22, 144, 48, ACC if win else BG, ON_ACC if win else ACC)
        text(s, x + 82, 144, w - 100, 48, h_, 32, TEXT, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=1.0, track=-50)
        stat(s, x + 24, 204, 268, unit, a, b, 38)
        stat(s, x + 292, 204, 262, 'raster p90, ms', r1_, r2_, 38)
        code(s, x + 22, 292, w - 44, 232, lines, 17.5, BG, 16, 18)
        text(s, x + 24, 536, w - 48, 100, why, 22, BODY, align=LEFT, spacing=LS)
    source(s, 'Code condensed from thrash_canvas.dart. Fixes applied in order, at 8×. p90, median of 3 rounds.')

    s, t = head(TRACK[5], 'Fix 4: A RepaintBoundary, on its own?', sub='Hands up: how much did it save at 8×?')
    x, w = col(0, 3)
    card(s, x, 164, w, 282, CARD, 'Before')
    text(s, x + 20, 176, w - 40, 32, 'Before: one layer', 24, TEXT, True, HEAD, LEFT, spacing=1.0)
    chip(s, x + 20, 216, w - 40, 106, 'Grid + labels +\nlines + dots', BG, TEXT, 22, True, 14)
    text(s, x + 20, 332, w - 40, 110, 'All of it is recorded again every frame, and the labels are laid out again.', 21, SUB, align=LEFT, spacing=LS)
    x, w = col(1, 3)
    card(s, x, 164, w, 282, ACC_T, 'After')
    text(s, x + 20, 176, w - 40, 32, 'After: two layers', 24, ACC, True, HEAD, LEFT, spacing=1.0)
    chip(s, x + 20, 216, w - 40, 50, 'Grid: recorded once', ACC, ON_ACC, 21, True, 14)
    chip(s, x + 20, 272, w - 40, 50, 'Lines, dots: re-recorded', BG, TEXT, 21, True, 14)
    text(s, x + 20, 332, w - 40, 110, '1.raster still draws both layers, every frame. There is no raster cache.', 21, SUB, align=LEFT, spacing=LS)
    x, w = col(2, 3)
    c1 = card(s, x, 164, w, 112, RED_T, 'Alone at 8×', 20)
    a1_, a2_ = stacked(s, x + 20, 174, w - 36, 'Alone at 8×', 'Almost nothing. A grid is nothing next to 130,000 path points.', 24, 20, RED)
    t.click(fx(c1), fx(a1_), fx(a2_))
    c2 = card(s, x, 286, w, 160, CARD, 'After the other fixes', 20)
    a3_ = text(s, x + 20, 296, w - 36, 32, 'After the other fixes', 24, TEXT, True, HEAD, LEFT, spacing=1.0, track=-30)
    a4_ = text(s, x + 20, 332, w - 36, 110, ['UI 4.4 → 3.4 ms', 'Raster 6.6 → 6.5 ms', 'Grid repaints 120 → 0 a second'], 21, TEXT, align=LEFT, spacing=LS, gap=2)
    t.click(fx(c2), fx(a3_), fx(a4_))
    code(s, ML, 460, CW, 92, ['// Give the static grid its own layer', 'RepaintBoundary(child: CustomPaint(painter: ThrashGridPainter(ledger)))'], 21, CARD, 20)
    bar_, tile_, words_ = point(s, 'On Impeller, a RepaintBoundary saves Dart work, not GPU work.', 'lightbulb', 568, 80, 30)
    t.click(fx(bar_), fx(tile_), fx(words_))

    s, t = head(TRACK[5], 'Four fixes. From 36 fps to 120.')
    card(s, ML, 128, 760, 520, CARD, 'Raster at each step')
    text(s, ML + 24, 142, 700, 28, 'Raster p90 in ms, on Impeller at 8×. The line is the 8.3 ms budget.', 20, SUB, align=LEFT, spacing=1.0)
    base, unit_ = 578, 11.6
    limit_y = base - 8.33 * unit_
    for i, (v, lab, c) in enumerate((('29.7', 'No fixes', RED), ('18.6', '+ Simplify\npaths', RED), ('13.7', '+ Batch\ndraws', RED), ('6.6', '+ Glow, no\nlayers', ACC), ('6.5', '+ Isolate\nrepaints', ACC))):
        x = ML + 40 + i * 140
        h = float(v) * unit_
        b = box(s, x, base - h, 112, h, c, 12, f'{lab}: {v} ms')
        topy = base - h - 44 if float(v) > 8.33 else limit_y - 44
        n = text(s, x - 14, topy, 140, 40, v, 30, TEXT, True, HEAD, spacing=1.0, track=-40)
        text(s, x - 14, base + 8, 140, 52, lab.split('\n'), 18, SUB, spacing=LS_TIGHT)
        t.click(fx(b, 'up', dur=500), fx(n))
    rule(s, ML + 20, limit_y, ML + 740, limit_y, TEXT, 3)
    RX, RW = 832, 392
    hero(s, RX, 128, RW, 248, 'blue', 'Frame rate')
    big(s, RX + 24, 140, RW - 48, 150, '120', 136, WHITE, LEFT)
    text(s, RX + 24, 300, RW - 48, 50, 'fps, from about 36', 30, WHITE, True, HEAD, LEFT, spacing=1.0, track=-40)
    for i, (ic, lab, val, sub) in enumerate((('code', 'UI', '3.4 ms', 'from 15.9'), ('layers', 'Layers', '0', 'from 64'), ('spline', 'Path points', '10,112', 'from 129,920'), ('pen-tool', 'Draw calls', '161', 'from 624'))):
        x = RX + (i % 2) * (RW / 2 + 6)
        y = 388 + (i // 2) * 134
        w = RW / 2 - 6
        card(s, x, y, w, 126, CARD, lab, 20)
        ico(s, ic, x + w - 40, y + 12, 26, None, ACC)
        text(s, x + 16, y + 12, w - 56, 26, lab, 19, SUB, True, HEAD, LEFT, spacing=1.0)
        text(s, x + 16, y + 44, w - 24, 44, val, 32, TEXT, True, HEAD, LEFT, spacing=1.0, track=-40)
        text(s, x + 16, y + 90, w - 24, 26, sub, 18, SUB, align=LEFT, spacing=1.0)
    source(s, 'Median of 3 rounds. Frame rates from 5 s system traces: 35.5 and 119.8 fps.')

    s, t = head(TRACK[6], 'Your effects can be pre-compiled too.', 'Your own shader', sub='Instead of a layer, write the effect once as a fragment shader.')
    code(s, ML, 164, 640, 390, ['# pubspec.yaml', 'flutter:', '  shaders: [shaders/depth_fill.frag]', '', '// Once, before it is needed', 'final program = await', '    FragmentProgram.fromAsset(path);', 'final shader = program.fragmentShader();', '', '// paint(): uniforms only, one draw', 'canvas.drawPath(depth, Paint()..shader = shader);'], 19)
    RX, RW = 712, 512
    hero(s, RX, 164, RW, 136, 'blue', 'Build output')
    text(s, RX + 24, 172, RW - 48, 80, [[('503 B', {'color': PREVIEW}), ('  →  ', {'color': PREVIEW, 'bold': False}), ('4,008 B', {'color': WHITE})]], 54, WHITE, True, HEAD, LEFT, spacing=1.0, track=-90)
    text(s, RX + 24, 254, RW - 48, 30, 'depth_fill.frag, in the profile APK', 21, WHITE, align=LEFT, spacing=1.0)
    for i, (a, b, c, ic, tile) in enumerate((('SPIR-V', 'For Vulkan: already compiled', ACC, 'circle-check', ACC_T), ('GLSL ES', "For Impeller's OpenGL ES backend", TEXT, 'file-code', BG), ('SkSL text', 'For Skia: compiled on the device, at first use', RED, 'flame', RED_T))):
        y = 312 + i * 82
        card(s, RX, y, RW, 76, CARD, a, 18)
        ico(s, ic, RX + 14, y + 16, 44, tile, c)
        text(s, RX + 70, y, 128, 76, a, 23, c, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=1.0, track=-30)
        text(s, RX + 196, y, RW - 208, 76, b, 20, BODY, align=LEFT, anchor=MSO_ANCHOR.MIDDLE, spacing=LS_TIGHT)
    point(s, 'One draw. Any procedural effect. No layer.', 'sparkles', 568, 80, 30)
    source(s, 'Code condensed. This custom shader was not timed on the phone.')

    # ------------------------------------------------------------ Prove it with tools
    s, t = head(TRACK[6], 'DevTools: which thread, then which code.', 'Prove it')
    pic = s.shapes.add_picture(os.path.join(A, 'devtools-frames-crop.png'), px(ML), px(128), px(CW), px(CW * 195 / 1160))
    pic._element.find('.//' + qn('p:cNvPr')).set('descr', 'DevTools frames chart at 8×: every frame is red, and raster is taller than UI')
    g = pic._element.find('.//' + qn('a:prstGeom'))
    g.set('prst', 'roundRect')
    gd = etree.SubElement(g.find(qn('a:avLst')), qn('a:gd'))
    gd.set('name', 'adj')
    gd.set('fmla', 'val 9000')
    for i, (h_, d) in enumerate((('Read the bars', 'One pair is one frame: UI left, raster right. Red is over budget.'), ('Pick the taller', 'If raster is taller, your widgets are not the first suspect.'), ('Select a frame', 'Timeline Events names the work. Name your own spans so it names your code.'))):
        x, w = col(i, 3)
        card(s, x, 340, w, 152, CARD, h_, 20)
        chip(s, x + 16, 352, 36, 36, str(i + 1), ACC, ON_ACC, 20, True, 18)
        text(s, x + 62, 352, w - 76, 36, h_, 25, TEXT, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=1.0, track=-30)
        text(s, x + 16, 396, w - 30, 92, d, 21, SUB, align=LEFT, spacing=LS)
    code(s, ML, 504, CW, 58, ["Timeline.timeSync('KILN::Thrash::grid', () { ... })"], 21, CARD, 16)
    words = (('Which thread?', 'zap'), ('Which event?', 'activity'), ('Which code?', 'code'), ('One fix', 'wrench'), ('Measure again', 'target'))
    for i, (w_, ic) in enumerate(words):
        x, w = col(i, 5, gap=26)
        hot_ = i == 4
        c = chip(s, x, 576, w, 72, '', EVENT if hot_ else SPOT, WHITE, 22, True, 36, name=w_)
        if hot_:
            grad(c, 'accent2')
        ico(s, ic, x + 14, 594, 36, None, WHITE if hot_ else ON_SPOT)
        text(s, x + 54, 576, w - 60, 72, w_, 20, WHITE if hot_ else ON_SPOT, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=LS_TIGHT)
        if i:
            ico(s, 'chevron-right', x - 23, 602, 20, None, SUB)
    source(s, 'Emulator in debug mode: read the shape, ignore the milliseconds.')

    s, t = head(TRACK[6], 'Perfetto: 100 ms on the phone.')
    card(s, ML, 128, CW, 212, CARD, 'Real frames')
    TRX, TRW = 176, 1032
    text(s, ML + 16, 140, 110, 42, 'Broken UI', 19, RED, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=1.0)
    text(s, ML + 16, 186, 110, 42, 'Raster', 19, SUB, align=LEFT, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0)
    trace_row(s, TRX, 138, TRW, trace['broken']['ui'], TEXT, 'Broken: UI frames', BG)
    trace_row(s, TRX, 186, TRW, trace['broken']['raster'], RED, 'Broken: raster frames', BG)
    l1_ = text(s, ML + 16, 236, 110, 42, 'Fixed UI', 19, ACC, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=1.0)
    l2_ = text(s, ML + 16, 282, 110, 42, 'Raster', 19, SUB, align=LEFT, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0)
    f1 = trace_row(s, TRX, 234, TRW, trace['fixed']['ui'], TEXT, 'Fixed: UI frames', BG)
    f2 = trace_row(s, TRX, 282, TRW, trace['fixed']['raster'], ACC, 'Fixed: raster frames', BG)
    t.click(fx(l1_), fx(l2_), fx(f1, 'left', dur=800), fx(f2, 'left', dur=800))
    ms = (('Raster frame, p50', '27.9 ms', '4.8 ms'), ('SurfaceFrame::Encode', '27.1 ms', '3.7 ms'), ('saveLayer per frame', '64', '0'), ('QueueSubmit per frame', '2', '1'), ('Frames in 5 s', '179', '604'))
    effects = []
    for i, (lab, a, b) in enumerate(ms):
        x, w = col(i, 5, gap=12)
        d_ = i * 90
        effects.append(fx(card(s, x, 352, w, 124, CARD, lab, 18), delay=d_))
        effects.append(fx(text(s, x + 12, 362, w - 20, 26, lab, 17, SUB, spacing=1.0), delay=d_))
        effects.append(fx(text(s, x + 8, 392, w - 16, 76, [[(a, {'color': SUB, 'size': 21, 'bold': False})], [(b, {'color': ACC, 'size': 33, 'bold': True})]], 24, TEXT, False, HEAD, spacing=1.0), delay=d_))
    t.click(*effects)
    box(s, ML, 488, CW, 160, SPOT, RAD, 'The vote')
    ico(s, 'hand', ML + 22, 504, 44, ACC, ON_ACC)
    text(s, ML + 80, 504, 900, 44, 'Is it waiting on the GPU?', 28, ON_SPOT, True, HEAD, LEFT, MSO_ANCHOR.MIDDLE, spacing=1.0, track=-30)
    ans = text(s, ML + 24, 552, CW - 48, 46, 'No. 1.raster is running for 24 of its 28 ms.', 34, PREVIEW, True, HEAD, LEFT, spacing=1.0, track=-40)
    det = text(s, ML + 24, 602, CW - 48, 32, 'Encode is Impeller turning the DisplayList into triangles and command buffers, on the CPU.', 22, ON_SPOT, align=LEFT, spacing=1.0)
    t.click(fx(ans), fx(det, delay=300))
    source(s, "System traces, tracing on. Each faint line is a 120 Hz deadline. This phone's driver exposes no GPU render stages.")

    s, t = head(TRACK[6], 'Read the budget from the trace.')
    bt = [('', 'UI p50', 'Raster p50', '1000 ÷ raster', 'Measured'),
          ('Broken', '13.5 ms', '27.9 ms', '36 fps', '35.5 fps'),
          ('Halfway', '2.7 ms', '13.8 ms', '72 fps', '70.4 fps'),
          ('All fixes', '2.3 ms', '4.8 ms', '208: screen caps at 120', '119.8 fps')]

    def bt_style(i, j, val):
        if i == 0:
            return None
        if j == 0:
            return dict(size=28, bold=True, font=HEAD)
        if j == 2:
            return dict(size=29, bold=True, font=HEAD, color=ACC if i == 3 else RED, fill=ACC_T if i == 3 else RED_T)
        if j == 3:
            return dict(size=21 if i == 3 else 27, color=SUB, font=HEAD)
        if j == 4:
            return dict(size=29, bold=True, font=HEAD)
        return dict(size=27, font=HEAD)
    table(s, ML, 128, (220, 200, 230, 298, 220), (46, 70, 70, 70), bt, bt_style, 'Budget from the traces')
    for i, (ic, h_, d) in enumerate((('gauge', 'Slowest thread sets the rate', 'Divide 1000 by its time. It matched what we measured.'), ('eye-off', 'Green UI proves nothing', 'Halfway, UI is inside 4 ms on 94% of frames, and it still runs at 70 fps.'), ('combine', 'The threads overlap', 'Fixed, UI + raster passed 8.3 ms on 28% of frames, and it still held 120.'))):
        x, w = col(i, 3)
        c = card(s, x, 400, w, 248, CARD, h_)
        ii = ico(s, ic, x + 20, 416, 48)
        a, b = stacked(s, x + 20, 476, w - 36, h_, d, 24, 22)
        t.click(fx(c), fx(ii), fx(a), fx(b))
    source(s, '5 s system traces at 8×, tracing on. Halfway is Simplify plus Batch. Bench p90s are separate: 3.4 and 6.5 ms.')

    # ------------------------------------------------------------ Finish
    s, t = head(TRACK[7], 'Three honest limits.', 'Finish', size=52)
    for i, (ic, h_, d) in enumerate((('list-ordered', 'Order matters', 'Isolate repaints did nothing until the big cost was gone. Measure each fix, in order.'), ('microscope', 'CPU side only', "The GPU's render passes here are the model, not my trace. This phone's driver doesn't expose them."), ('flame', 'Skia copes worse', 'Same phone, same chart: 188 ms a frame broken, 58 ms with every fix. Impeller made this workload possible, not free.'))):
        x, w = col(i, 3)
        card(s, x, 140, w, 508, CARD, h_, 28)
        ico(s, ic, x + 28, 168, 72)
        text(s, x + 28, 262, w - 56, 50, h_, 36, TEXT, True, HEAD, LEFT, spacing=1.0, track=-60)
        text(s, x + 28, 320, w - 56, 310, d, 30, SUB, align=LEFT, spacing=LS)

    s, t = head(TRACK[7], 'Take this home.', size=52)
    for i, (n, ic, h_, d, kind) in enumerate((('1', 'book-open', 'Demystify the engine.', 'Skia compiles in the frame. Impeller compiles ahead, tessellates on the CPU and records command buffers.', 'blue'), ('2', 'activity', 'Profile low-level.', 'About 4 ms UI, 4 ms raster. The slowest thread sets your frame rate. DevTools for the frame, Perfetto for the system.', 'spot'), ('3', 'wrench', 'Tame your painters.', "Fewer points, fewer draws, no saveLayer you don't need. Pre-compile your own effects. Prove every fix.", 'red'))):
        x, w = col(i, 3)
        if kind == 'spot':
            box(s, x, 140, w, 508, SPOT, 28, h_)
            fg = ON_SPOT
        else:
            hero(s, x, 140, w, 508, 'blue' if kind == 'blue' else 'red', h_, 28)
            fg = WHITE
        big(s, x + 28, 156, 120, 100, n, 88, fg, LEFT)
        ico(s, ic, x + w - 92, 168, 64, fg, RGBColor(0, 0, 0) if (kind == 'spot' and dark) else (TEXT if kind == 'spot' else (EVENT if kind == 'blue' else RED)))
        text(s, x + 28, 270, w - 56, 50, h_, 31, fg, True, HEAD, LEFT, spacing=1.0, track=-50)
        text(s, x + 28, 326, w - 56, 310, d, 29, fg, align=LEFT, spacing=LS)

    s, t = new(layout=blue)
    set_title(s, "Impeller made performance predictable.\nIt didn't make expensive work free.", 52, 72, 110, 720, 290, WHITE)
    text(s, 72, 420, 720, 44, 'Thread, event, code, fix, measure.', 30, WHITE, align=LEFT, spacing=1.0)
    text(s, 72, 520, 720, 36, 'Collins Munene, Shipht', 24, WHITE, True, HEAD, LEFT, spacing=1.0)
    text(s, 72, 556, 720, 32, 'FlutterCon Kenya, Nairobi, 5–6 Nov 2026', 22, WHITE, align=LEFT, spacing=1.0)
    box(s, 836, 96, 372, 500, WHITE, 28, 'QR card')
    qr = s.shapes.add_picture(os.path.join(A, 'qr-repo.png'), px(866), px(118), px(312), px(312))
    qr._element.find('.//' + qn('p:cNvPr')).set('descr', f'QR code linking to {REPO}')
    qr.click_action.hyperlink.address = REPO
    text(s, 866, 442, 312, 40, 'Scan to run it yourself', 26, INK, True, HEAD, spacing=1.0)
    link = text(s, 850, 490, 344, 80, ['github.com/cm-collins/', 'fluttercon-demo-app'], 20, GREY, spacing=1.0)
    for par in link.text_frame.paragraphs:
        par.runs[0].hyperlink.address = REPO

    # ------------------------------------------------------------ Backups
    def table_slide(heading, rows, widths, heights, foot, style, section=None):
        s, t = new(section)
        text(s, ML, 30, 700, 26, 'Backup for Q&A', 20, ACC, True, HEAD, LEFT)
        set_title(s, heading, 46, ML, 58, CW, 54)
        table(s, ML, 136, widths, heights, rows, style, heading)
        source(s, foot)

    def storm_style(i, j, val):
        if i == 0:
            return dict(size=18)
        if j == 0:
            return dict(size=27, bold=True, font=HEAD)
        base_ = dict(size=27, font=HEAD)
        if j in (1, 2):
            base_.update(bold=True)
        if j == 1:
            base_.update(color=RED, fill=RED_T)
        if j == 2:
            base_.update(color=ACC, fill=ACC_T)
        return base_
    table_slide('Shader Storm medians', [('Effects', 'Skia cold', 'Impeller cold', 'Skia repeat', 'Impeller repeat', 'Skia relaunch', 'Impeller relaunch'),
                                         ('48', '687', '127', '18', '45', '58', '66'), ('96', '1,310', '145', '19', '43', '81', '73'), ('144', '1,863', '145', '23', '48', '102', '73')],
                (118, 150, 170, 150, 190, 180, 210), (54, 110, 110, 110), 'Worst frame in ms, median of 3 rounds, 120 Hz, tracing off. Infinix X6873, Flutter 3.47.8 profile builds.', storm_style, 'Backup for Q&A')

    def thrash_style(i, j, val):
        if i == 0:
            return dict(size=19)
        if j == 0:
            return dict(size=26, bold=True, font=HEAD)
        base_ = dict(size=27, font=HEAD)
        if j == 2:
            base_.update(bold=True, color=ACC, fill=ACC_T)
        if j == 4:
            base_.update(bold=True, color=RED, fill=RED_T)
        return base_
    table_slide('Canvas Thrash medians at 8×', [('Fixes on', 'Impeller UI', 'Impeller raster', 'Skia UI', 'Skia raster'),
                                                ('None', '15.9', '29.7', '21.8', '188.4'), ('Simplify', '6.3', '18.6', '23.7', '187.7'), ('Simplify + Batch', '4.9', '13.7', '23.5', '202.3'),
                                                ('+ Glow', '4.4', '6.6', '3.9', '61.5'), ('+ Isolate', '3.4', '6.5', '3.9', '57.7')],
                (368, 200, 220, 170, 210), (54, 88, 88, 88, 88, 88), 'Frame p90 in ms, median of 3 rounds. Skia trace with all fixes: 47 of 53 ms inside 32 line draws.', thrash_style)

    # Native shapes carry a theme style with a soft shadow: remove it everywhere.
    for slide in prs.slides:
        for tag in ('p:sp', 'p:cxnSp'):
            for node in slide._element.iter(qn(tag)):
                style = node.find(qn('p:style'))
                if style is not None:
                    node.remove(style)
    for tl in timelines:
        tl.write()
    add_sections(prs, sections)
    out = os.path.join(HERE, 'beyond-skia-dark.pptx' if dark else 'beyond-skia.pptx')
    prs.save(out)
    print(variant, os.path.getsize(out) // 1024, 'KB,', len(prs.slides), 'slides')


if __name__ == '__main__':
    build('light')
    build('dark')
