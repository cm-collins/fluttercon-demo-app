#!/usr/bin/env python3
"""Builds the talk's PowerPoint decks next to this script: beyond-skia.pptx (light) and beyond-skia-dark.pptx.

usage: python3 build_pptx.py        (needs python-pptx)

One idea per slide, with very few words. Videos are not embedded: the speaker notes say when to
play each clip from local/clips-stage/. Colours come only from the theme, so one setting changes
the whole deck. Sizes are in pixels on a 1280 x 720 slide.
"""
import json
import math
import os
import re

from lxml import etree
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
    title.set('algn', 'ctr')
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
         anchor=MSO_ANCHOR.TOP, spacing=1.15, track=None, name=None, gap=0):
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
    par.line_spacing = 1.02
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


def fine(slide, value, y=640):
    return text(slide, 150, y, 980, 48, value, 18, SUB, spacing=1.1)


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


def curve(slide, x, y, s=1.0):
    pts = [(x + a * s, y + b * s) for a, b in bezier()]
    fb = slide.shapes.build_freeform(px(pts[0][0]), px(pts[0][1]), scale=1.0)
    fb.add_line_segments([(px(a), px(b)) for a, b in pts[1:]], close=False)
    shape = fb.convert_to_shape()
    shape.fill.background()
    paint(shape.line.color, TEXT)
    shape.line.width = fs(7)
    shape.name = 'A smooth path'
    return shape


def strip(slide, x, y, s=1.0, half=14):
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
    group = slide.shapes.add_group_shape()
    for (a, b), (c, e) in zip(edges, edges[1:]):
        for tri in ((a, b, c), (b, c, e)):
            v = [(x + u * s, y + w * s) for u, w in tri]
            fb = group.shapes.build_freeform(px(v[0][0]), px(v[0][1]), scale=1.0)
            fb.add_line_segments([(px(u), px(w)) for u, w in v[1:]], close=True)
            t = fb.convert_to_shape()
            t.fill.solid()
            paint(t.fill.fore_color, CARD)
            paint(t.line.color, ACC)
            t.line.width = fs(2.5)
    group.name = 'The same path as a triangle strip'
    return group


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


def trace_row(slide, x, y, w, spans, color, label):
    group = slide.shapes.add_group_shape()
    bg = group.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px(x), px(y), px(w), px(44))
    bg.adjustments[0] = 0.2
    bg.fill.solid()
    paint(bg.fill.fore_color, CARD)
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
    set_theme(prs, THEMES[variant])
    statement, blue = make_layouts(prs, dark)
    prs.core_properties.title = 'Beyond Skia: GPU scheduling and profiling with Impeller on Android 10+'
    prs.core_properties.author = 'Collins Munene'
    prs.core_properties.subject = 'FlutterCon Kenya 2026'
    trace = json.loads(re.search(r'window\.TRACE=(\{.*\});', open(os.path.join(HERE, 'trace-data.js')).read()).group(1))
    sections, timelines = [], []

    def new(section=None, layout=None):
        slide = prs.slides.add_slide(layout or statement)
        if section:
            sections.append((section, len(prs.slides)))
        tl = Timeline(slide)
        timelines.append(tl)
        return slide, tl

    def note(slide, speech, *clips):
        parts = [speech]
        for n in clips:
            parts.append(f'>>> AFTER THIS SLIDE: play {CLIPS[n]} from local/clips-stage/, then come back and press Next.')
        slide.notes_slide.notes_text_frame.text = '\n\n'.join(parts)

    def say(title, sub=None, speech='', *clips, section=None, size=88, color=None):
        """A statement slide: one centred sentence and at most one quiet line."""
        s, t = new(section)
        lines = title.count('\n') + 1
        h = size * 1.06 * lines
        top = 330 - h / 2 - (28 if sub else 0)
        set_title(s, title, size, 80, top, 1120, h + 10, color)
        if sub:
            text(s, 120, top + h + 40, 1040, 110, sub, 32, SUB)
        note(s, speech, *clips)
        return s, t

    def number(value, caption, foot, speech, *clips, section=None, size=300, color=ACC, capsize=40):
        s, t = new(section)
        h = size * 1.08
        top = max(70, 300 - h / 2)
        set_title(s, value, size, 40, top, 1200, h, color)
        text(s, 120, top + h + 10, 1040, 60, caption, capsize, TEXT, True, HEAD, track=-60)
        if foot:
            fine(s, foot)
        note(s, speech, *clips)
        return s, t

    def fix(n, name, frm, to, unit, line, speech, *clips):
        s, t = new()
        text(s, 80, 90, 1120, 40, f'Fix {n}', 26, ACC, True, HEAD)
        set_title(s, name, 60, 80, 128, 1120, 80)
        big(s, 40, 250, 540, 170, frm, 130, SUB, PP_ALIGN.RIGHT)
        text(s, 590, 280, 100, 110, '→', 72, SUB, False, 'Inter')
        big(s, 700, 250, 540, 170, to, 130, ACC, PP_ALIGN.LEFT)
        text(s, 80, 422, 1120, 50, unit, 30, TEXT, True, HEAD, track=-40)
        text(s, 140, 490, 1000, 90, line, 28, SUB, spacing=1.25)
        note(s, speech, *clips)
        return s, t

    # ------------------------------------------------------------ The problem
    s, t = new('The problem', blue)
    pill = box(s, -240, 96, 1040, 464, WHITE, 232, 'Title pill')
    s.shapes._spTree.remove(pill._element)
    s.shapes._spTree.insert(2, pill._element)
    set_title(s, 'Beyond\nSkia', 112, 72, 126, 640, 250, INK)
    s.shapes.title.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT
    text(s, 72, 416, 610, 90, 'GPU scheduling and profiling with Impeller on Android 10+', 28, RGBColor(0x42, 0x42, 0x45), align=PP_ALIGN.LEFT, spacing=1.25)
    photo = s.shapes.add_picture(os.path.join(L, 'speaker.jpg'), px(868), px(96), px(340), px(400))
    photo._element.find('.//' + qn('p:cNvPr')).set('descr', 'Collins Munene')
    geom = photo._element.find('.//' + qn('a:prstGeom'))
    geom.set('prst', 'round2SameRect')
    av = geom.find(qn('a:avLst'))
    for key, val in (('adj1', 50000), ('adj2', 0)):
        gd = etree.SubElement(av, qn('a:gd'))
        gd.set('name', key)
        gd.set('fmla', f'val {val}')
    text(s, 868, 510, 400, 40, 'Collins Munene', 30, WHITE, True, HEAD, PP_ALIGN.LEFT)
    text(s, 868, 550, 404, 32, 'DevOps and Software Engineer, Shipht', 20, WHITE, align=PP_ALIGN.LEFT)
    note(s, "Hi, I'm Collins. Let me show you a chart.", 1)

    say('Impeller fixed\none kind of jank.', 'So what is still making frames late?',
        "This is a live market chart in Flutter, on Impeller, on Vulkan, on a 120 hertz phone. Every red bar in that clip was a frame that missed its deadline. It ran at about a third of the frame rate the screen can show. Impeller was supposed to fix jank. It did fix one kind. In the next 30 minutes I'll show you which one, and how to find and fix the kind it didn't.")
    number('8.3 ms', 'for every frame, at 120 Hz', None, "The screen refreshes 120 times a second. Each frame gets 8.3 milliseconds. Miss it, and the user sees it.", size=210, color=TEXT)

    s, t = new()
    set_title(s, 'Two threads share it.', 64, 80, 96, 1120, 80)
    box(s, 200, 240, 436, 170, TEXT, 30, 'UI')
    box(s, 644, 240, 436, 170, ACC, 30, 'Raster')
    text(s, 200, 285, 436, 80, 'UI  ~4 ms', 44, BG, True, HEAD, anchor=MSO_ANCHOR.MIDDLE, track=-80)
    text(s, 644, 285, 436, 80, 'Raster  ~4 ms', 44, WHITE if not dark else RGBColor(0, 0, 0), True, HEAD, anchor=MSO_ANCHOR.MIDDLE, track=-80)
    text(s, 200, 430, 436, 80, 'Your Dart, on the main thread', 26, SUB)
    text(s, 644, 430, 436, 80, 'Impeller, on the raster thread', 26, SUB)
    text(s, 120, 540, 1040, 50, 'Four and four is the target. 8.3 per thread is the limit.', 30, TEXT, True, HEAD, track=-40)
    note(s, "Flutter spends that frame on two threads. UI is our Dart code. Raster is Impeller. Budget about 4 milliseconds for each. Strictly, the threads overlap, so each can stretch to 8.3 and still hit 120. But then you add a frame of latency and have no headroom. Four and four is the budget I design for.\n\nThat's what the budget is. So why did Flutter need a new engine?", 2)

    # ------------------------------------------------------------ Why Impeller exists
    s, t = new('Why Impeller exists')
    set_title(s, "A stutter you couldn't fix in Dart.", 60, 80, 74, 1120, 80)
    text(s, 120, 158, 1040, 40, '2015 Sky draws with Skia  ·  2018 Flutter 1.0 ships on Skia  ·  2019 issue #32170', 24, SUB)
    steps = ['New effect\non screen', 'Skia writes\na shader', 'The driver compiles\nit in the frame', 'The frame misses\nits deadline', 'The user sees\na stutter']
    shapes = []
    for i, label in enumerate(steps):
        x = 62 + i * 236
        last = i == 4
        c = box(s, x, 268, 214, 170, RED if last else CARD, 26, label.replace('\n', ' '))
        tf = c.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = tf.margin_right = px(10)
        for j, part in enumerate(label.split('\n')):
            p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
            p.alignment = PP_ALIGN.CENTER
            r = p.add_run()
            r.text = part
            r.font.size, r.font.bold, r.font.name = fs(22), True, HEAD
            paint(r.font.color, WHITE if last else TEXT)
        shapes.append(c)
    t.click(*[fx(c, delay=i * 260) for i, c in enumerate(shapes)])
    text(s, 120, 490, 1040, 60, 'Once per shader, per install.', 44, TEXT, True, HEAD, track=-80)
    note(s, "The title says Beyond Skia, so what are we beyond? Sky, the prototype that became Flutter, already drew with Skia in 2015. Flutter 1.0 shipped on it in December 2018. Skia is the 2D engine behind Chrome and Android's own UI: excellent, and general purpose.\n\nCLICK: here's the problem. A new effect appears. Skia writes a shader. The driver compiles it on the raster thread, in the middle of a frame. The frame is late, and the user sees it.\n\nOnce per shader, per install. You don't see it on the phone you test with every day, because the cache is warm, and no amount of optimising Dart fixes it.")

    s, t = new()
    set_title(s, 'Three years of workarounds.', 60, 80, 74, 1120, 80)
    for i, (yr, head, why) in enumerate((('2019', 'Warm up at startup', 'You had to guess the right draw calls.'), ('2020', 'Record and bundle', 'Tied to devices and drivers. Captured again after every upgrade.'), ('2021', 'Default removed', "An admission that it couldn't scale."))):
        x = 80 + i * 390
        big(s, x, 200, 340, 100, yr, 76, ACC, PP_ALIGN.LEFT)
        text(s, x, 310, 340, 50, head, 30, TEXT, True, HEAD, PP_ALIGN.LEFT, track=-40)
        text(s, x, 360, 340, 160, why, 26, SUB, align=PP_ALIGN.LEFT, spacing=1.25)
    note(s, "2019: draw common shapes offscreen at startup. You needed real Skia expertise to guess the right calls. 2020, Flutter 1.20: record the shaders with --cache-sksl and bundle them. It helped, it really did, but it was tied to devices and drivers. 2021: the default warm-up comes out.")

    s, t = new()
    set_title(s, '“requires 0 extra effort\nfrom developers”', 76, 80, 150, 1120, 170)
    text(s, 120, 350, 1040, 100, '“handles all cases that may have never been encountered during any tests or warmups.”', 32, BODY, spacing=1.25)
    text(s, 120, 490, 1040, 80, 'Flutter issue #32170, May 2019. Closed August 2023, pointing to Impeller.', 26, SUB)
    note(s, "This is from the Flutter team's own issue, opened in May 2019. That sentence is the spec for what came next. The issue was closed in August 2023, pointing to Impeller. Warm-up was the community trying to fix a renderer from the outside.")

    s, t = new()
    set_title(s, 'One platform at a time.', 60, 80, 44, 1120, 80)
    X0, W0 = 200, 1000
    xpos = lambda y, m=1: X0 + (y - 2018 + (m - 1) / 12) * W0 / 9
    for yr in range(2019, 2027):
        text(s, xpos(yr) - 30, 140, 60, 26, str(yr), 18, SUB)
    def lane(y, name, parts, caption):
        lab = text(s, 60, y + 6, 130, 44, name, 30, TEXT, True, HEAD, PP_ALIGN.LEFT, track=-40)
        g = s.shapes.add_group_shape()
        g.name = f'{name} renderer timeline'
        for (y1, m1), (y2, m2), kind in parts:
            r = g.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(xpos(y1, m1)), px(y), px(xpos(y2, m2) - xpos(y1, m1)), px(52))
            r.fill.solid()
            if kind == 'pv':
                r.fill.fore_color.rgb = PREVIEW
            else:
                paint(r.fill.fore_color, TEXT if kind == 'sk' else EVENT)
            r.line.fill.background()
        cap = text(s, X0, y + 60, W0, 30, caption, 21, SUB, align=PP_ALIGN.LEFT)
        return lab, g, cap
    lanes = [lane(174, 'iOS', [((2018, 12), (2023, 1), 'sk'), ((2023, 1), (2023, 5), 'pv'), ((2023, 5), (2027, 1), 'im')], 'Default in 3.10, May 2023. Skia removed in 3.29, Feb 2025.'),
             lane(290, 'Android', [((2018, 12), (2023, 11), 'sk'), ((2023, 11), (2024, 12), 'pv'), ((2024, 12), (2027, 1), 'im')], 'Default on Vulkan in 3.27, Dec 2024. Android 10+ today.'),
             lane(406, 'Desktop', [((2022, 2), (2026, 8), 'sk'), ((2026, 8), (2027, 1), 'im')], 'Default in 3.47, 2026.')]
    for lab, g, cap in lanes:
        t.click(fx(lab), fx(g, 'left', dur=1100), fx(cap, delay=500))
    for i, (name, c) in enumerate((('Skia', TEXT), ('Impeller preview', PREVIEW), ('Impeller default', EVENT))):
        x = 390 + i * 190
        box(s, x, 536, 22, 14, c, 4, f'{name} key')
        text(s, x + 30, 529, 160, 28, name, 19, SUB, align=PP_ALIGN.LEFT)
    fine(s, 'Flutter docs and release notes. Web still renders with Skia. Older Android stays on the legacy renderer.', 600)
    note(s, "So the team built a renderer with one rule: no shader compilation while the app runs. It rolled out one platform at a time.\n\nCLICK: iOS first. Default in 3.10, May 2023, and Skia gone from iOS in 3.29.\nCLICK: Android took longer. Default on Vulkan devices in 3.27, December 2024.\nCLICK: desktop, this year, in 3.47.\n\nIf asked: web still renders with Skia, and Android below API 29 stays on the legacy renderer. The Skia build's own log warns that opting out is deprecated, so this comparison won't be possible forever.")

    s, t = new()
    set_title(s, 'The trade.', 64, 80, 54, 1120, 80)
    rows = (('Shaders', 'Compiled in the frame', 'Compiled with the engine'), ('Caching', 'Automatic raster cache', 'No raster cache'), ('Paths', 'Rendered on the GPU', 'Tessellated on the CPU'))
    for x, h in ((360, 'Before'), (760, 'Now')):
        text(s, x, 160, 380, 30, h, 22, SUB, align=PP_ALIGN.LEFT)
    for i, (a, b, c) in enumerate(rows):
        y = 196 + i * 124
        rule(s, 80, y, 1200, y)
        text(s, 80, y + 34, 270, 60, a, 40, TEXT, True, HEAD, PP_ALIGN.LEFT, track=-70)
        text(s, 360, y + 38, 380, 60, b, 30, SUB, align=PP_ALIGN.LEFT)
        text(s, 760, y + 38, 440, 60, c, 30, ACC, True, HEAD, PP_ALIGN.LEFT, track=-30)
    note(s, "Impeller isn't free. It's a trade, and this table is the rest of the talk. Shaders: the big win, and the next section measures it. Caching: no raster cache, so some old fast code is now honestly slow. Paths: tessellated on the CPU, so very complex paths cost time on the raster thread. Separately, since 3.29, Dart runs on the platform main thread, and DevTools still calls it UI.")

    s, t = new()
    set_title(s, 'Same app. Two renderers.', 64, 80, 90, 1120, 90)
    for i, (who, line, c) in enumerate((('Skia build', 'The application opted out of Impeller', TEXT), ('Impeller build', 'Using the Impeller rendering backend (Vulkan).', ACC))):
        y = 226 + i * 130
        text(s, 120, y, 1040, 34, who, 24, SUB)
        text(s, 120, y + 40, 1040, 60, line, 32, c, False, MONO)
    fine(s, 'Engine logs. Infinix X6873, Mali-G615 MC6, Vulkan 1.3, Android 16, 120 Hz. Flutter 3.47.8 profile builds.', 610)
    note(s, "Don't trust the badge. Read what the engine writes at startup. Same Flutter SDK, same Dart code, same phone, one setting different.")

    say("Skia wasn't slow.\nIt was unpredictable.", "At 120 Hz, that's worse. Let's measure it.", "Skia wasn't slow. It was unpredictable. Let's measure it. Shader Storm reveals 144 new effects at once. These are recordings from the stage phone; the scoreboard numbers are medians of three clean runs. Watch the motion lane, and say nothing for two seconds.", 3)

    # ------------------------------------------------------------ What Impeller fixed
    number('Frozen.', '1,954 ms, in that recording', None, "The whole motion lane turned red. The UI lane stayed green: Dart was fine, the engine stopped to compile. Skia writes and compiles a GPU program for each new effect, inside the frame.", section='What Impeller fixed', size=210, color=RED)
    say('Same effects,\nsecond time.', 'Hands up: will it freeze again?', 'VOTE. Wait for hands, then play the clip.', 4)
    number('21 ms', 'The programs are already built.', None, "No freeze. The programs are cached. Now Impeller, same phone, same 144 effects, first time.", 5, size=210)
    number('148 ms', 'Impeller. Short, but not zero.', None, "Its shaders were compiled when the engine was built. About 145 milliseconds in the clean runs. Short, but not zero, and I'll show you why.", size=210)
    number('13×', 'shorter freeze with Impeller', '144 new effects, cold start. Worst frame, median of 3 rounds. Skia on OpenGL ES, Impeller on Vulkan.', "1,863 milliseconds against 145. Three runs each, medians.")

    s, t = new()
    set_title(s, "Skia's freeze grows. Impeller's doesn't.", 56, 80, 44, 1120, 80)
    chart = line_chart(s, 170, 130, 850, 480)
    text(s, 1030, 150, 230, 40, 'Skia', 32, TEXT, True, HEAD, PP_ALIGN.LEFT)
    text(s, 1030, 190, 230, 40, '1,863 ms', 28, SUB, align=PP_ALIGN.LEFT)
    text(s, 1030, 462, 230, 40, 'Impeller', 32, ACC, True, HEAD, PP_ALIGN.LEFT)
    text(s, 1030, 502, 230, 40, '145 ms', 28, SUB, align=PP_ALIGN.LEFT)
    text(s, 40, 300, 130, 90, ['Freeze', 'Lower is', 'better'], 19, SUB, align=PP_ALIGN.LEFT, spacing=1.2)
    text(s, 170, 612, 850, 30, 'New effects on screen', 20, SUB)
    t.click(fx(chart, 'left', dur=1200))
    note(s, "CLICK: the lines draw. As we tripled the effects, Skia went from 0.7 to 1.9 seconds. Impeller went from 127 to 145 milliseconds.")

    s, t = new()
    set_title(s, '118 programs. 40 pipelines.', 60, 80, 54, 1120, 80)
    text(s, 80, 164, 540, 50, 'Skia', 32, TEXT, True, HEAD, track=-40)
    text(s, 660, 164, 540, 50, 'Impeller', 32, ACC, True, HEAD, track=-40)
    g1 = squares(s, 112, 226, 118, TEXT)
    g2 = squares(s, 692, 226, 40, ACC)
    text(s, 80, 400, 540, 44, '14.6 ms each', 30, SUB)
    text(s, 660, 400, 540, 44, '2.2 ms each', 30, SUB)
    text(s, 120, 490, 1040, 50, "Both on the raster thread. That's where the cost moved.", 32, TEXT, True, HEAD, track=-40)
    fine(s, 'System traces of one cold reveal at 144 effects, tracing on.', 610)
    t.click(fx(g1, 'left', dur=1000), fx(g2, 'left', dur=500, delay=1000))
    note(s, "Here's why it barely grows. CLICK: Skia builds a program per effect, 118 in the reveal frame. Impeller only builds pipelines from shaders compiled when the engine was built: 40 of them, about two milliseconds each. Both on the raster thread, both in the frame. The cost moved and shrank. It did not vanish.")

    s, t = new()
    set_title(s, 'Predictable.\nNot always faster.', 72, 80, 60, 1120, 160)
    chart = bar_chart(s, 170, 270, 900, 230, ['Skia', 'Impeller'], (23, 48), (TEXT, ACC), '0', 62, 'Repeat reveal', 'Repeat reveal: Skia 23 ms, Impeller 48 ms')
    text(s, 120, 520, 1040, 90, 'Worst frame in ms. The same 144 effects, redrawn in the same session.', 28, SUB)
    t.click(fx(chart, 'left', dur=800))
    note(s, "CLICK: inside the same session Skia is actually faster: 23 against 48, because Impeller does some per-frame work that Skia doesn't. So this is not 'Impeller is always faster'. It moved the most expensive work out of the frame.")

    # ------------------------------------------------------------ How a frame works
    s, t = new('How a frame works')
    set_title(s, 'From paint() to triangles.', 60, 80, 54, 1120, 80)
    curve(s, 90, 210, 1.05)
    text(s, 590, 300, 100, 80, '→', 60, SUB)
    right = strip(s, 700, 210, 1.05)
    for i, (h, d) in enumerate((('Shaders', 'Built with the engine'), ('Pipelines', 'At startup or first use'), ('DisplayList', 'paint() only records'), ('Tessellation', 'Triangles, on the CPU'))):
        x = 80 + i * 285
        text(s, x, 470, 265, 44, h, 30, ACC if i == 3 else TEXT, True, HEAD, track=-40)
        text(s, x, 516, 265, 70, d, 22, SUB)
    fine(s, 'Illustration. Impeller redoes this every frame: there is no raster cache.', 610)
    t.click(fx(right, 'left', dur=1800))
    note(s, "Here's what Impeller does with one frame on Vulkan. Every shader is compiled when the engine is built. A pipeline is a shader plus fixed GPU state, mostly built at startup, the rest on first use. Your paint method doesn't touch the GPU: it records a DisplayList.\n\nCLICK: on the raster thread, Impeller tessellates. Every path is broken into triangles on the CPU, every frame.")

    s, t = new()
    set_title(s, 'The CPU records. The GPU executes.', 60, 80, 54, 1120, 80)
    x0, w0 = 240, 960
    for name, y in (('Raster thread', 180), ('Queue', 280), ('GPU', 380)):
        text(s, 60, y + 18, 175, 40, name, 24, TEXT, True, HEAD, PP_ALIGN.LEFT)
        box(s, x0, y, w0, 76, CARD, 18, f'{name} lane')
    seg = lambda frac, width, y, c=ACC: box(s, x0 + w0 * frac, y + 14, w0 * width, 48, c, 12)
    r1, q1, g1 = seg(.02, .30, 180), seg(.31, .04, 280, TEXT), seg(.36, .30, 380)
    r2, q2, g2 = seg(.36, .30, 180), seg(.65, .04, 280, TEXT), seg(.70, .28, 380)
    t.click(fx(r1, 'left', dur=900), fx(q1, delay=900, dur=200), fx(g1, 'left', delay=1100, dur=900), fx(r2, 'left', delay=1100, dur=900), fx(q2, delay=2000, dur=200), fx(g2, 'left', delay=2200, dur=900))
    text(s, 120, 490, 1040, 100, ["Under stress, the risk isn't compilation.", "It's how much you record."], 34, TEXT, True, HEAD, track=-50)
    fine(s, 'Illustration', 620)
    note(s, "CLICK: watch one frame go through. The raster thread records explicit command buffers: begin render pass, bind pipeline, bind buffers, draw, end. It submits them to the Vulkan queue and moves on. The GPU executes while the raster thread starts the next frame. That's GPU scheduling: the CPU records, the GPU executes, fences keep them in step. And Impeller has no raster cache: whatever we ask it to draw, it draws every frame.")

    s, t = new()
    set_title(s, 'Three names. Two CPU threads.', 60, 80, 54, 1120, 80)
    for i, (h, d) in enumerate((('Main thread', 'Your Dart.\nDevTools calls it UI.'), ('Raster thread', "Impeller's CPU work.\nDevTools calls it Raster."), ('GPU', 'Hardware downstream.\nNot a Flutter thread.'))):
        x = 80 + i * 390
        text(s, x, 210, 340, 60, h, 38, ACC if i == 1 else TEXT, True, HEAD, track=-60)
        text(s, x, 280, 340, 110, d.split('\n'), 26, SUB, spacing=1.3)
    text(s, 120, 450, 1040, 90, ['DevTools for the frame.', 'Perfetto for the system.'], 34, TEXT, True, HEAD, track=-50)
    note(s, "Since 3.29, Dart animation, build, layout and paint run on the platform main thread; DevTools labels that work UI. Impeller prepares GPU work on the raster thread, 1.raster in Perfetto. The GPU is hardware downstream. Perfetto replaced Systrace, and still opens its files; the system traces you'll see were recorded with atrace, the tool underneath Systrace.")

    say('Which thread?\nWhich event?\nWhich code?', 'One fix. Measure again.', "One method for everything that follows: which thread is over budget, which event, which code. One surgical fix. Measure again.", size=84)

    # ------------------------------------------------------------ What it didn't fix
    s, t = new("What it didn't fix", blue)
    text(s, 72, 66, 1100, 44, "So if compiling shaders isn't the problem, what is?", 28, WHITE, align=PP_ALIGN.LEFT)
    set_title(s, "What Impeller\ndidn't fix.", 120, 72, 230, 1136, 270, WHITE)
    s.shapes.title.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT
    note(s, "Skia pays at the worst moment, in the frame, in front of the user. Impeller paid when the engine was built. So if compiling shaders is no longer the problem, what is? Let's go break something. Each step doubles the lines and doubles the points on each line, so four times the path points. Watch which bar grows.", 6)
    number('129,920', 'path points, every frame', 'Canvas Thrash at 8×: 624 draw calls and 64 offscreen layers too.', "At 8×: almost 130,000 path points, 624 draw calls, 64 offscreen layers. RASTER is far taller than UI. My Dart finishes; the engine is the one struggling.", size=190, color=TEXT)
    say('Nothing is compiling.', 'This is pure drawing cost.', "Nothing is compiling here. This is pure drawing cost, and no renderer saves you from asking it to draw too much.")
    say('Which fix helps most,\non its own?', ['Simplify paths  ·  Batch draws', 'Glow without layers  ·  Isolate repaints'], 'VOTE. Wait for hands.', size=76)

    s, t = new()
    set_title(s, 'Simplify paths, by a distance.', 60, 80, 44, 1120, 80)
    chart = bar_chart(s, 120, 130, 1040, 480, ['No fixes', 'Simplify paths', 'Batch draws', 'Glow without layers', 'Isolate repaints'], (29.7, 18.6, 28.6, 21.2, 25.2), (RED, ACC, TEXT, TEXT, TEXT), '0.0', 34, 'Each fix alone', 'Raster p90 at 8×: no fixes 29.7, Simplify paths 18.6, Batch draws 28.6, Glow without layers 21.2, Isolate repaints 25.2 ms')
    fine(s, 'Raster p90 in ms, each fix on its own at 8×. Median of 3 rounds; rounds varied, so small gaps mean little.', 625)
    t.click(fx(chart, 'left', dur=900))
    note(s, "CLICK: Simplify paths, by a distance. We'll take them one at a time.")

    say('8,000 points per line.', 'On a chart a few hundred pixels wide.', "First suspect: points. That's about 25 points for every pixel column. The first clip is X-ray: a model of what Impeller does with a path. The GPU only draws triangles, so Impeller cuts every stroke into triangles on the CPU, every frame. X-ray costs work of its own, so it goes off before we judge anything. The second clip turns the fix on.", 7, 8)
    fix(1, 'Simplify paths', '129,920', '12,032', 'path points', 'Raster 29.7 → 18.6 ms.  UI 15.9 → 6.3 ms.', "Keep two points per pixel column: lowest and highest. Build once, then slide. Both bars drop, because building an 8,000-point path every frame was Dart work too.")
    fix(2, 'Batch draws', '640', '161', 'draw calls', 'Raster 18.6 → 13.7 ms. The smallest win of the four.', "The heat strip was 480 segments, each its own path and draw. Now every segment is two triangles, all in one drawVertices call. On Vulkan a draw call is cheap: a few commands, not a trip to the driver.")
    fix(3, 'Glow without layers', '64', '0', 'offscreen layers', 'Raster 13.7 → 6.6 ms. The biggest raster win.', "Each glowing dot was a saveLayer with a blur: an offscreen pass, a blur, a composite, 64 times a frame. Same glow, as a radial gradient. The raster thread was busy the whole time, not waiting for the GPU. The trace also shows two queue submits per frame become one.")
    say('A RepaintBoundary,\non its own?', 'Hands up: how much did it save at 8×?', 'VOTE. Wait for hands, then advance.', size=76)
    say('Almost nothing.', 'A grid is nothing next to 130,000 path points.', "Isolate repaints alone did not help at 8×. Fix the big cost first. Then it pays off.")
    fix(4, 'Isolate repaints', '4.4', '3.4', 'ms on the UI thread', 'Grid repaints: 0 a second. Raster barely moved.', "With the rest fixed: grid repaints zero, UI under the 4 millisecond target. Raster barely moves: on Impeller a RepaintBoundary saves Dart work, not GPU work.")

    s, t = new()
    set_title(s, 'Four fixes. Same picture.', 60, 80, 44, 1120, 80)
    base, unit = 560, 12.5
    limit_y = base - 8.33 * unit
    effects = []
    for i, (v, lab, c) in enumerate((('29.7', 'No fixes', RED), ('18.6', 'Simplify paths', RED), ('13.7', 'Batch draws', RED), ('6.6', 'Glow, no layers', ACC), ('6.5', 'Isolate repaints', ACC))):
        x = 170 + i * 190
        h = float(v) * unit
        b = box(s, x, base - h, 130, h, c, 14, f'{lab}: {v} ms')
        top = base - h - 52 if float(v) > 8.33 else limit_y - 56
        n = text(s, x - 25, top, 180, 46, v, 34, TEXT, True, HEAD)
        text(s, x - 30, base + 14, 190, 56, lab, 20, SUB, spacing=1.15)
        effects.append([fx(b, 'up', dur=500), fx(n)])
    rule(s, 120, limit_y, 1214, limit_y, TEXT, 3)
    text(s, 1064, limit_y + 8, 150, 28, '8.3 ms budget', 19, TEXT, True, align=PP_ALIGN.LEFT)
    fine(s, 'Raster p90 in ms at 8× on Impeller, median of 3 rounds.', 640)
    for e in effects:
        t.click(*e)
    note(s, "CLICK through each fix: raster from 30 milliseconds to six and a half.")

    s, t = new()
    panel = box(s, 40, 40, 560, 620, EVENT, 36, 'Frame rate')
    text(s, 84, 80, 480, 40, 'Frame rate', 28, WHITE, True, HEAD, PP_ALIGN.LEFT)
    set_title(s, '120', 216, 76, 270, 500, 230, WHITE)
    s.shapes.title.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT
    s.shapes._spTree.remove(panel._element)
    s.shapes._spTree.insert(2, panel._element)
    text(s, 84, 516, 480, 50, 'fps, from about 36', 36, WHITE, True, HEAD, PP_ALIGN.LEFT, track=-40)
    for x, y, w, h, lab, val, sub in ((618, 40, 300, 301, 'Raster', '6.5 ms', 'from 29.7 ms'), (936, 40, 304, 301, 'UI', '3.4 ms', 'from 15.9 ms'), (618, 359, 300, 301, 'Offscreen layers', '0', 'from 64'), (936, 359, 304, 301, 'Path points', '10,112', 'from 129,920')):
        box(s, x, y, w, h, CARD, 36, lab)
        text(s, x + 28, y + 26, w - 50, 34, lab, 24, SUB, True, HEAD, PP_ALIGN.LEFT)
        big(s, x + 28, y + h - 140, w - 40, 80, val, 62, TEXT, PP_ALIGN.LEFT)
        text(s, x + 28, y + h - 56, w - 40, 34, sub, 22, SUB, align=PP_ALIGN.LEFT)
    note(s, "Raster went from 30 milliseconds to six and a half. UI from 16 to three and a half. From about 36 frames a second to the full 120. Nothing here was clever. Fewer points, fewer draw calls, no offscreen layers, no pointless repainting. Impeller took shader compilation out of the frame. You still pay for every point, every draw and every layer you ask for.")

    # ------------------------------------------------------------ Your own shader
    s, t = new('Your own shader')
    set_title(s, 'Your own pre-compiled shader.', 60, 80, 44, 1120, 80)
    box(s, 170, 140, 940, 400, CARD, 32, 'Code')
    code = ["# pubspec.yaml", "flutter:", "  shaders: [depth_fill.frag]", "", "final program = await FragmentProgram.fromAsset(...);", "final shader = program.fragmentShader();", "", "// paint(): uniforms only, one draw", "canvas.drawPath(depth, Paint()..shader = shader);"]
    text(s, 212, 168, 860, 350, code, 22, TEXT, False, MONO, PP_ALIGN.LEFT, spacing=1.3)
    text(s, 120, 562, 1040, 44, 'One draw call. Any procedural effect. No layer.', 30, SUB)
    fine(s, 'Code condensed. Not timed on the phone.', 626)
    note(s, "One more pattern, for the pre-compiled part. Everything Impeller drew in both demos ran on shaders compiled when the engine was built. Your own effects can join that path: write a fragment shader, list it in pubspec, load it once, and only set uniforms in paint. Do not quote a speed: this custom shader was not timed.")
    number('503 B → 4,008 B', 'SPIR-V for Vulkan. GLSL ES for OpenGL ES. SkSL text for Skia.', 'depth_fill.frag in the Kiln profile APK. Skia still compiles the SkSL text on the device at first use.', "Here's what the build did with this 500-byte file: a 4-kilobyte bundle. SPIR-V for Vulkan. GLSL for Impeller's OpenGL backend. And SkSL for Skia, as source text, which Skia still compiles on the phone the first time it's drawn. Same file, two engines: the whole talk in one asset.", size=110, capsize=30)

    # ------------------------------------------------------------ Prove it with tools
    s, t = new('Prove it with tools')
    set_title(s, 'DevTools: which thread?', 60, 80, 44, 1120, 80)
    pic = s.shapes.add_picture(os.path.join(A, 'devtools-frames-crop.png'), px(60), px(140), px(1160), px(195))
    pic._element.find('.//' + qn('p:cNvPr')).set('descr', 'DevTools frames chart at 8×: every frame is red, and raster is taller than UI')
    g = pic._element.find('.//' + qn('a:prstGeom'))
    g.set('prst', 'roundRect')
    gd = etree.SubElement(g.find(qn('a:avLst')), qn('a:gd'))
    gd.set('name', 'adj')
    gd.set('fmla', 'val 9000')
    for i, (h, d) in enumerate((('One pair, one frame', 'UI left, raster right'), ('Red means late', 'Over the frame budget'), ('Taller bar first', 'Raster: leave the widgets alone'))):
        x = 80 + i * 390
        text(s, x, 368, 340, 44, h, 30, TEXT, True, HEAD, track=-40)
        text(s, x, 414, 340, 40, d, 23, SUB)
    text(s, 120, 490, 1040, 50, 'Then Timeline Events names the code.', 32, TEXT, True, HEAD, track=-40)
    text(s, 120, 540, 1040, 40, 'KILN::Thrash::grid  strip  lines  dots', 24, ACC, False, MONO)
    fine(s, 'Emulator in debug mode: read the shape, ignore the milliseconds.', 620)
    note(s, "This is DevTools on an emulator, in debug mode, so ignore the milliseconds. I'm showing you where to look; the real numbers are the phone traces. Each pair is one frame. Red is late. Raster is the taller one, so that's where I look first. The chart told me which thread. Timeline Events tells me which code, because I named my spans.")

    s, t = new()
    set_title(s, 'Perfetto: 100 ms on the phone.', 60, 80, 44, 1120, 80)
    text(s, 60, 146, 200, 44, 'Broken', 32, RED, True, HEAD, PP_ALIGN.LEFT)
    text(s, 60, 196, 110, 44, 'UI', 24, SUB, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.MIDDLE)
    trace_row(s, 170, 196, 1050, trace['broken']['ui'], TEXT, 'Broken: UI frames')
    text(s, 60, 250, 110, 44, 'Raster', 24, SUB, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.MIDDLE)
    trace_row(s, 170, 250, 1050, trace['broken']['raster'], RED, 'Broken: raster frames')
    h = text(s, 60, 324, 200, 44, 'Fixed', 32, ACC, True, HEAD, PP_ALIGN.LEFT)
    l1 = text(s, 60, 374, 110, 44, 'UI', 24, SUB, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.MIDDLE)
    f1 = trace_row(s, 170, 374, 1050, trace['fixed']['ui'], TEXT, 'Fixed: UI frames')
    l2 = text(s, 60, 428, 110, 44, 'Raster', 24, SUB, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.MIDDLE)
    f2 = trace_row(s, 170, 428, 1050, trace['fixed']['raster'], ACC, 'Fixed: raster frames')
    text(s, 120, 498, 1040, 50, '4 frames became 12.', 40, TEXT, True, HEAD, track=-70)
    fine(s, 'Real frames from system traces. Each faint line is a 120 Hz deadline.', 590)
    t.click(fx(h), fx(l1), fx(f1, 'left', dur=800), fx(l2), fx(f2, 'left', dur=800))
    note(s, "This is the broken chart as the system sees it. Raster: long slices back to back. It never rests. Each raster frame is 28 milliseconds, and 27 of them are SurfaceFrame Encode: Impeller turning our DisplayList into triangles and command buffers on the CPU. 64 saveLayer per frame, and two queue submissions.\n\nCLICK: all four fixes. 4.8 milliseconds a frame, zero layers, one submission, 604 frames in five seconds.")

    say('Is it waiting on the GPU?', 'Hands up.', 'VOTE. Wait for hands, then advance.', size=76)
    number('24 of 28 ms', 'running on the CPU, not waiting', "These traces show the CPU side: encoding and submits. This phone's driver exposes no GPU render stages.", "Going in, I suspected it was waiting on the GPU. The trace said otherwise: the raster thread is running, not sleeping. On this phone the cost is the CPU preparing the frame. Only say 'I suspected' if it is true for you.", size=170, color=TEXT)
    number('1000 ÷ 27.9 = 36', 'fps. The slowest thread sets the frame rate.', 'From 5 s system traces. Measured: 35.5 fps broken, 70.4 at 13.8 ms raster, 119.8 with all fixes.', "Divide a thousand by 28: 36. That's the frame rate we measured. Halfway through the fixes, UI is inside four milliseconds on 94 percent of frames, and we're still at 70, because raster is at 14. A green UI bar proves nothing if raster is red.", size=120, color=TEXT)
    say('The threads overlap.', 'UI + raster passed 8.3 ms on about 28% of fixed frames. It still averaged 120 fps.', "That's pipelining. Four and four is the target for latency. 8.3 per thread is the limit for frame rate. Fixed raster is over the 4 millisecond target on 81 percent of frames, and it holds 120.")

    # ------------------------------------------------------------ Finish
    s, t = new('Finish')
    set_title(s, 'Three honest limits.', 64, 80, 90, 1120, 80)
    for i, (h, d) in enumerate((('Order matters', 'Isolate repaints did nothing until the big cost was gone.'), ('CPU side only', "The GPU's render passes here are the model, not my trace."), ('Skia copes worse', '188 ms a frame broken. 58 ms with every fix.'))):
        x = 80 + i * 390
        text(s, x, 240, 340, 60, h, 36, TEXT, True, HEAD, track=-60)
        text(s, x, 306, 340, 170, d, 28, SUB, spacing=1.25)
    note(s, "Not every fix helped on its own. I can show you the CPU side of the GPU, but what the Mali GPU did with those buffers, this phone's driver doesn't expose to Perfetto. And Skia: same phone, same chart, 188 milliseconds broken, 58 with every fix. Impeller made this workload possible. It didn't make it free.")

    s, t = new()
    set_title(s, 'Take this home.', 64, 80, 70, 1120, 80)
    for i, (n, h, d) in enumerate((('1', 'Demystify the engine.', 'Impeller compiles ahead, tessellates on the CPU, records command buffers.'), ('2', 'Profile low-level.', 'About 4 ms UI, 4 ms raster. The slowest thread sets your frame rate.'), ('3', 'Tame your painters.', "Fewer points, fewer draws, no saveLayer you don't need. Prove every fix."))):
        x = 80 + i * 390
        big(s, x, 196, 340, 100, n, 80, ACC)
        text(s, x, 296, 340, 50, h, 30, TEXT, True, HEAD, track=-40)
        text(s, x, 348, 340, 170, d, 26, SUB, spacing=1.25)
    note(s, "One: demystify the engine. Skia compiles in the frame; Impeller compiles ahead. Two: profile low-level. DevTools for the frame, Perfetto for the system. Three: tame your custom painters, and your own effects as build-time shaders. Prove every fix with numbers.")

    s, t = new(layout=blue)
    set_title(s, "Impeller made performance predictable.\nIt didn't make expensive work free.", 50, 72, 120, 720, 280, WHITE)
    s.shapes.title.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT
    text(s, 72, 420, 720, 44, 'Thread, event, code, fix, measure.', 30, WHITE, align=PP_ALIGN.LEFT)
    text(s, 72, 520, 720, 36, 'Collins Munene, Shipht', 24, WHITE, True, HEAD, PP_ALIGN.LEFT)
    text(s, 72, 556, 720, 32, 'FlutterCon Kenya, Nairobi, 5–6 Nov 2026', 22, WHITE, align=PP_ALIGN.LEFT)
    box(s, 836, 96, 372, 500, WHITE, 28, 'QR card')
    qr = s.shapes.add_picture(os.path.join(A, 'qr-repo.png'), px(866), px(118), px(312), px(312))
    qr._element.find('.//' + qn('p:cNvPr')).set('descr', f'QR code linking to {REPO}')
    qr.click_action.hyperlink.address = REPO
    text(s, 866, 442, 312, 40, 'Scan to run it yourself', 26, INK, True, HEAD)
    link = text(s, 850, 490, 344, 80, ['github.com/cm-collins/', 'fluttercon-demo-app'], 20, RGBColor(0x42, 0x42, 0x45))
    for par in link.text_frame.paragraphs:
        par.runs[0].hyperlink.address = REPO
    note(s, "Impeller made performance predictable. It didn't make expensive work free. Thread, event, code, fix, measure: that's the method you can take into production. The repo has the app and every script behind these numbers, so run it on your own phone. Thank you.\n\nLeave this slide up during Q&A so people can scan the code.")

    # ------------------------------------------------------------ Backups
    def table_slide(heading, rows, widths, foot, section=None):
        s, t = new(section)
        set_title(s, heading, 48, 80, 44, 1120, 70)
        frame = s.shapes.add_table(len(rows), len(rows[0]), px(60), px(130), px(1160), px(64 * len(rows)))
        frame.name = heading
        tbl = frame.table
        tp = tbl._tbl.tblPr
        tp.set('firstRow', '0')
        tp.set('bandRow', '0')
        sid = tp.find(qn('a:tableStyleId'))
        if sid is not None:
            sid.text = '{2D5ABB26-0587-4C30-8999-92F81FD0307C}'
        for j, w in enumerate(widths):
            tbl.columns[j].width = px(w)
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                cell = tbl.cell(i, j)
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                run = cell.text_frame.paragraphs[0].add_run()
                run.text = val
                run.font.size = fs(20 if i == 0 else 26)
                run.font.bold = i > 0 and j == 0
                paint(run.font.color, SUB if i == 0 else TEXT)
        fine(s, foot)
        note(s, 'Backup for Q&A: press Next past the closing slide, or type the slide number and press Enter.')

    table_slide('Shader Storm medians', [('Effects', 'Skia cold', 'Impeller cold', 'Skia repeat', 'Impeller repeat', 'Skia relaunch', 'Impeller relaunch'),
                                         ('48', '687', '127', '18', '45', '58', '66'), ('96', '1,310', '145', '19', '43', '81', '73'), ('144', '1,863', '145', '23', '48', '102', '73')],
                (120, 150, 180, 150, 190, 170, 200), 'Worst frame in ms, median of 3 rounds, 120 Hz, tracing off. Infinix X6873, Flutter 3.47.8 profile builds.', 'Backup for Q&A')
    table_slide('Canvas Thrash medians at 8×', [('Fixes on', 'Impeller UI', 'Impeller raster', 'Skia UI', 'Skia raster'),
                                                ('None', '15.9', '29.7', '21.8', '188.4'), ('Simplify', '6.3', '18.6', '23.7', '187.7'), ('Simplify + Batch', '4.9', '13.7', '23.5', '202.3'),
                                                ('+ Glow', '4.4', '6.6', '3.9', '61.5'), ('+ Isolate', '3.4', '6.5', '3.9', '57.7')],
                (360, 200, 220, 170, 210), 'Frame p90 in ms, median of 3 rounds. Skia trace with all fixes: 47 of 53 ms inside 32 line draws.')

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
