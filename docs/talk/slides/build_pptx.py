#!/usr/bin/env python3
"""Builds the talk's PowerPoint decks next to this script: beyond-skia.pptx (light) and beyond-skia-dark.pptx.

usage: python3 build_pptx.py        (needs python-pptx, Pillow, and the files in local/)

The slides stay out of the speaker's way: one idea, few words, real data and real screens from the
demo app. The explanation lives in the speaker's voice, so speaker notes come from speaker_notes.json.
The fonts are embedded in each file. Sizes are in pixels on a 1280 x 720 slide.
"""
import json
import math
import os
import re
import struct

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_MARKER_STYLE
from pptx.enum.dml import MSO_THEME_COLOR as TC
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.opc.package import Part
from pptx.opc.packuri import PackURI
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(HERE, 'local')
A = os.path.join(L, 'pptx')
REPO = 'https://github.com/cm-collins/fluttercon-demo-app'

# One ink, one paper, one grey, and one accent. The accent marks the one thing to look at.
TEXT, BG, SUB, CARD, ACC, HAIR = TC.TEXT_1, TC.BACKGROUND_1, TC.TEXT_2, TC.BACKGROUND_2, TC.ACCENT_1, TC.ACCENT_2
THEMES = {
    'light': dict(dk1='141414', lt1='F7F6F2', dk2='6B6A66', lt2='E9E7E0', accent1='D63C0A', accent2='D5D3CB',
                  accent3='141414', accent4='6B6A66', accent5='D63C0A', accent6='D5D3CB', hlink='141414', folHlink='6B6A66'),
    'dark': dict(dk1='F4F3EF', lt1='0B0B0C', dk2='8E8D89', lt2='1D1D1F', accent1='FF5C28', accent2='2C2C2E',
                 accent3='F4F3EF', accent4='8E8D89', accent5='FF5C28', accent6='2C2C2E', hlink='F4F3EF', folHlink='8E8D89'),
}
INK = RGBColor(0x0B, 0x0B, 0x0C)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
PAPER = RGBColor(0xF4, 0xF3, 0xEF)
ASH = RGBColor(0x9A, 0x99, 0x95)
EMBER = RGBColor(0xFF, 0x5C, 0x28)
GREY = RGBColor(0x55, 0x55, 0x52)

HEAD, BODY, MID, MONO = 'Inter Tight SemiBold', 'Inter', 'Inter Medium', 'JetBrains Mono'
FONTS = ((HEAD, 'regular', 'InterTight-600.ttf'), (BODY, 'regular', 'Inter-400.ttf'), (MID, 'regular', 'Inter-500.ttf'),
         (MONO, 'regular', 'JetBrainsMono-400.ttf'))
NS = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
FONT_REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/font'

# The grid: side margins, the title line, and the line shared by the source and the logo.
M, W, RIGHT_EDGE, TITLE_Y, TITLE_SIZE, FOOT_Y = 72, 1136, 1208, 44, 52, 664
SUB_Y, CT, CT_SUB, CB = 108, 132, 164, 640  # subtitle line, content top without and with a subtitle, content bottom
GUT = 32  # a 12-column grid with 32 px gutters: gx(k) is the left edge of column k, gw(n) the width of n columns

# The only font sizes in the deck, by job.
T_SOURCE, T_LABEL, T_CODE, T_SMALL, T_BODY, T_H3, T_H1, T_NUM, T_HERO, T_MEGA = 16, 20, 22, 24, 28, 36, 52, 72, 112, 160
LEFT, RIGHT, CENTER = PP_ALIGN.LEFT, PP_ALIGN.RIGHT, PP_ALIGN.CENTER


def gx(k):
    return M + k * (W + GUT) / 12


def gw(n):
    return n * (W + GUT) / 12 - GUT


def px(v):
    return Emu(int(round(v * 9525)))


def fs(v):
    return Pt(v * 0.75)


def paint(color_format, c):
    if isinstance(c, RGBColor):
        color_format.rgb = c
    else:
        color_format.theme_color = c


# --- Fonts --------------------------------------------------------------------------------
def eot(path):
    """Wraps a TrueType font as an uncompressed EOT, the format PowerPoint embeds as .fntdata."""
    data = open(path, 'rb').read()
    tables = {}
    for i in range(struct.unpack('>H', data[4:6])[0]):
        tag, _, off, size = struct.unpack('>4sLLL', data[12 + i * 16:28 + i * 16])
        tables[tag.decode()] = (off, size)
    os2 = tables['OS/2'][0]
    weight, fstype = struct.unpack('>H', data[os2 + 4:os2 + 6])[0], struct.unpack('>H', data[os2 + 8:os2 + 10])[0]
    panose = data[os2 + 32:os2 + 42]
    ranges = struct.unpack('>4L', data[os2 + 42:os2 + 58])
    pages = struct.unpack('>2L', data[os2 + 78:os2 + 86])
    italic = 1 if struct.unpack('>H', data[os2 + 62:os2 + 64])[0] & 1 else 0
    adjust = struct.unpack('>L', data[tables['head'][0] + 8:tables['head'][0] + 12])[0]
    base = tables['name'][0]
    count, strings = struct.unpack('>HH', data[base + 2:base + 6])
    names = {}
    for i in range(count):
        plat, _, lang, nid, size, off = struct.unpack('>6H', data[base + 6 + i * 12:base + 18 + i * 12])
        if plat == 3 and lang == 0x409:
            names[nid] = data[base + strings + off:base + strings + off + size].decode('utf-16-be').encode('utf-16-le')
    head = struct.pack('<LLL', len(data), 0x00020001, 0) + panose + struct.pack('<BBLHH', 1, italic, weight, fstype, 0x504C)
    head += struct.pack('<4L', *ranges) + struct.pack('<2L', *pages) + struct.pack('<L', adjust) + b'\0' * 16 + b'\0\0'
    for nid in (1, 2, 5, 4):
        head += struct.pack('<H', len(names.get(nid, b''))) + names.get(nid, b'') + b'\0\0'
    head += struct.pack('<H', 0)
    return struct.pack('<L', len(head) + 4 + len(data)) + head + data, panose.hex().upper()


def embed_fonts(prs):
    """So the deck looks the same on a machine that does not have the fonts installed."""
    root = prs.part._element
    root.set('embedTrueTypeFonts', '1')
    root.set('saveSubsetFonts', '0')
    lst = etree.Element(qn('p:embeddedFontLst'))
    for i, (family, style, name) in enumerate(FONTS):
        blob, panose = eot(os.path.join(A, 'fonts', name))
        part = Part(PackURI(f'/ppt/fonts/font{i + 1}.fntdata'), 'application/x-fontdata', prs.part.package, blob)
        rid = prs.part.relate_to(part, FONT_REL)
        node = etree.SubElement(lst, qn('p:embeddedFont'))
        font = etree.SubElement(node, qn('p:font'))
        font.set('typeface', family)
        font.set('panose', panose) if set(panose) != {'0'} else None
        etree.SubElement(node, qn(f'p:{style}')).set(qn('r:id'), rid)
    root.find(qn('p:notesSz')).addnext(lst)


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
    fonts.find('a:minorFont/a:latin', NS).set('typeface', BODY)
    part._blob = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
    title = master.element.find('.//p:txStyles/p:titleStyle/a:lvl1pPr', NS)
    title.set('algn', 'l')
    rpr = title.find('a:defRPr', NS)
    rpr.set('sz', str(int(TITLE_SIZE * 75)))
    rpr.set('b', '0')
    rpr.set('spc', str(int(-TITLE_SIZE * 1.1)))
    for shape in master.placeholders:
        idx = shape.placeholder_format.idx
        if idx == 0:
            shape.left, shape.top, shape.width, shape.height = px(M), px(TITLE_Y), px(W), px(64)
        elif idx == 1:
            shape.left, shape.top, shape.width, shape.height = px(M), px(150), px(W), px(480)
        else:
            shape.left, shape.top, shape.width, shape.height = px(M), px(FOOT_Y), px(200), px(24)


def layout_title(layout):
    for shape in list(layout.placeholders):
        if shape.placeholder_format.idx == 0:
            shape.left, shape.top, shape.width, shape.height = px(M), px(TITLE_Y), px(W), px(64)
            body = shape._element.find(qn('p:txBody')).find(qn('a:bodyPr'))
            for k in ('lIns', 'rIns', 'tIns', 'bIns'):
                body.set(k, '0')
            body.set('anchor', 't')
            for child in list(body):
                body.remove(child)
            etree.SubElement(body, qn('a:noAutofit'))
        else:
            shape._element.getparent().remove(shape._element)


def brand(layout, logo):
    """The FlutterCon wordmark, at the very bottom right."""
    _, rid = layout.part.get_or_add_image_part(os.path.join(L, f'fluttercon-{logo}.png'))
    layout.shapes._spTree.append(etree.fromstring(f'''<p:pic xmlns:p="{NS['p']}" xmlns:a="{NS['a']}" xmlns:r="{NS['r']}">
      <p:nvPicPr><p:cNvPr id="901" name="FlutterCon logo" descr="FlutterCon logo"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr userDrawn="1"/></p:nvPicPr>
      <p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
      <p:spPr><a:xfrm><a:off x="{px(RIGHT_EDGE - 116)}" y="{px(FOOT_Y + 2)}"/><a:ext cx="{px(116)}" cy="{px(20)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>'''))


def make_layouts(prs, dark):
    by_name = {x.name: x for x in prs.slide_layouts}
    content, ink = by_name['Title Only'], by_name['Section Header']
    content.name, ink.name = 'Slide', 'Ink'
    layout_title(content)
    layout_title(ink)
    fill = ink.background.fill
    fill.solid()
    fill.fore_color.rgb = INK
    for shape in ink.placeholders:
        lst = shape._element.find(qn('p:txBody')).find(qn('a:lstStyle'))
        for child in list(lst):
            lst.remove(child)
        rpr = etree.SubElement(etree.SubElement(lst, qn('a:lvl1pPr')), qn('a:defRPr'))
        etree.SubElement(etree.SubElement(rpr, qn('a:solidFill')), qn('a:srgbClr')).set('val', 'F4F3EF')
    brand(content, 'dark' if dark else 'light')
    brand(ink, 'dark')
    for layout in list(prs.slide_layouts):
        if layout.name not in ('Slide', 'Ink'):
            prs.slide_layouts.remove(layout)
    return content, ink


# --- Drawing helpers ----------------------------------------------------------------------
def text(slide, x, y, w, h, lines, size=26, color=TEXT, font=None, align=LEFT, anchor=MSO_ANCHOR.TOP,
         spacing=1.12, track=None, name=None, gap=0, wrap=True):
    """Zero insets, so text lines up exactly with rules and bars. `lines` is a string, or a list of paragraphs."""
    box_ = slide.shapes.add_textbox(px(x), px(y), px(w), px(h))
    tf = box_.text_frame
    tf.word_wrap = wrap
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
        for value, opt in ([(line, {})] if isinstance(line, str) else line):
            run = par.add_run()
            run.text = value
            f = run.font
            f.size = fs(opt.get('size', size))
            f.bold = False
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


def display(slide, x, y, w, h, value, size, color=TEXT, align=LEFT, name=None):
    """Headline type: the display cut, set tight."""
    return text(slide, x, y, w, h, value, size, color, HEAD, align, spacing=0.98, track=-size * 1.1, name=name)


def box(slide, x, y, w, h, fill=CARD, name=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(x), px(y), px(w), px(h))
    shape.fill.solid()
    paint(shape.fill.fore_color, fill)
    shape.line.fill.background()
    if name:
        shape.name = name
    return shape


def label_box(slide, x, y, w, h, value, fill, color, size=T_SMALL, font=MID, name=None):
    """A flat block of a diagram with words inside it."""
    b = box(slide, x, y, w, h, fill, name or value.replace('\n', ' '))
    tf = b.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = px(10)
    tf.margin_top = tf.margin_bottom = 0
    for j, part in enumerate(value.split('\n')):
        p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
        p.alignment = LEFT
        p.line_spacing = 1.04
        r = p.add_run()
        r.text = part
        r.font.size, r.font.bold, r.font.name = fs(size), False, font
        paint(r.font.color, color)
    return b


def rule(slide, x1, y1, x2, y2, color=HAIR, width=1.0, dash=None):
    ln = slide.shapes.add_connector(1, px(x1), px(y1), px(x2), px(y2))
    paint(ln.line.color, color)
    ln.line.width = fs(width)
    if dash:
        etree.SubElement(ln.line._get_or_add_ln(), qn('a:prstDash')).set('val', dash)
    return ln


def set_title(slide, value, size=TITLE_SIZE, x=M, y=TITLE_Y, w=W, h=64, color=None):
    shape = slide.shapes.title
    shape.left, shape.top, shape.width, shape.height = px(x), px(y), px(w), px(h)
    tf = shape.text_frame
    tf.word_wrap = True
    par = tf.paragraphs[0]
    par.line_spacing = 0.98
    for i, part in enumerate(value.split('\n')):
        if i:
            par.add_line_break()
        run = par.add_run()
        run.text = part
        run.font.size = fs(size)
        run.font.bold = False
        run._r.get_or_add_rPr().set('spc', str(int(-size * 1.1)))
        if color is not None:
            paint(run.font.color, color)
    return shape


def shot(slide, path, x, y, w, crop=(0, 0, 0, 0), size=None, radius=None, alt=''):
    """A real screen from the app or the tools. Crop is left, top, right, bottom, as fractions."""
    pic = slide.shapes.add_picture(path, px(x), px(y), width=px(w))
    pic.crop_left, pic.crop_top, pic.crop_right, pic.crop_bottom = crop
    natural_w, natural_h = pic.image.size
    h = w * (natural_h * (1 - crop[1] - crop[3])) / (natural_w * (1 - crop[0] - crop[2]))
    pic.height = px(h)
    pic._element.find('.//' + qn('p:cNvPr')).set('descr', alt)
    if radius:
        geom = pic._element.find('.//' + qn('a:prstGeom'))
        geom.set('prst', 'roundRect')
        gd = etree.SubElement(geom.find(qn('a:avLst')), qn('a:gd'))
        gd.set('name', 'adj')
        gd.set('fmla', f'val {int(radius / min(w, h) * 100000)}')
    return pic


def polyline(slide, pts, color, width, name):
    fb = slide.shapes.build_freeform(px(pts[0][0]), px(pts[0][1]), scale=1.0)
    fb.add_line_segments([(px(a), px(b)) for a, b in pts[1:]], close=False)
    shape = fb.convert_to_shape()
    shape.fill.background()
    paint(shape.line.color, color)
    shape.line.width = fs(width)
    shape.name = name
    return shape


def dots(slide, points, color, size=6, name='Points'):
    group = slide.shapes.add_group_shape()
    for a, b in points:
        o = group.shapes.add_shape(MSO_SHAPE.OVAL, px(a - size / 2), px(b - size / 2), px(size), px(size))
        o.fill.solid()
        paint(o.fill.fore_color, color)
        o.line.fill.background()
    group.name = name
    return group


def blocks(slide, spans, y, h, color, x0, k, x_max, name):
    """A lane of a timing diagram: each span is a start and a length, in ms."""
    group = slide.shapes.add_group_shape()
    for start, ms in spans:
        a = x0 + start * k
        b = min(a + ms * k, x_max)
        if a < x_max:
            r = group.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(a), px(y), px(max(b - a - 1, 1.5)), px(h))
            r.fill.solid()
            paint(r.fill.fore_color, color)
            r.line.fill.background()
    group.name = name
    return group


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


# --- The deck -----------------------------------------------------------------------------
def build(variant):
    dark = variant == 'dark'
    prs = Presentation()
    prs.slide_width, prs.slide_height = px(1280), px(720)
    set_theme(prs, THEMES[variant])
    plain, ink = make_layouts(prs, dark)
    prs.core_properties.title = 'Beyond Skia: GPU scheduling and profiling with Impeller on Android 10+'
    prs.core_properties.author = 'Collins Munene'
    prs.core_properties.subject = 'FlutterCon Kenya 2026'
    trace = json.loads(re.search(r'window\.TRACE=(\{.*\});', open(os.path.join(HERE, 'trace-data.js')).read()).group(1))
    speech = json.load(open(os.path.join(HERE, 'speaker_notes.json')))
    sections, timelines = [], []

    def new(section=None, layout=None):
        slide = prs.slides.add_slide(layout or plain)
        if section:
            sections.append((section, len(prs.slides)))
        tl = Timeline(slide)
        timelines.append(tl)
        slide.notes_slide.notes_text_frame.text = speech[len(prs.slides) - 1]
        return slide, tl

    def page(title, section=None, sub=None):
        s, t = new(section)
        set_title(s, title)
        if sub:
            text(s, M, SUB_Y, W, 40, sub, T_BODY, SUB, spacing=1.0, name='Subtitle')
        return s, t

    def source(s, value, w=980, color=SUB):
        """Where the numbers came from: one quiet line, level with the logo."""
        return text(s, M, FOOT_Y, w, 24, value, T_SOURCE, color, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0, name='Source')

    def code(s, x, y, w, h, lines):
        """Code on the page, with no panel around it. `!!` is the broken version and `++` the fixed one."""
        out = []
        for line in lines:
            c = TEXT
            if line.startswith('!!'):
                line, c = '// ' + line[2:].strip(), ACC
            elif line.startswith('++'):
                line, c = '// ' + line[2:].strip(), SUB
            elif line.startswith(('//', '#')):
                c = SUB
            out.append([(line, {'color': c})])
        return text(s, x, y, w, h, out, T_CODE, TEXT, MONO, spacing=1.2, name='Code')

    def change(s, x, y, w, label, a, b, size=T_H1, unit=None, color=TEXT):
        """A measured change: a quiet label, the old value in grey, the new value in full ink."""
        one = text(s, x, y, w, 26, label, T_LABEL, SUB, spacing=1.0)
        runs = [(a, {'color': SUB}), (' → ', {'color': SUB}), (b, {'color': color})]
        if unit:
            runs.append((' ' + unit, {'color': SUB, 'size': T_SMALL, 'track': 0}))
        two = text(s, x, y + 28, w, size * 1.25, [runs], size, TEXT, HEAD, spacing=1.0, track=-size * 0.9)
        return one, two

    def tall(s, path, crop, alt, top=CT, bottom=CB):
        """A phone screen on the right: top and bottom on the content lines, right edge on the margin."""
        from PIL import Image
        nw, nh = Image.open(path).size
        w_ = (bottom - top) * (nw * (1 - crop[0] - crop[2])) / (nh * (1 - crop[1] - crop[3]))
        return shot(s, path, RIGHT_EDGE - w_, top, w_, crop, radius=14, alt=alt)

    def mix(c1, c2, amount):
        """A step between two theme colours, for the overdraw heat picture."""
        slot = {BG: 'lt1', ACC: 'accent1', SUB: 'dk2', TEXT: 'dk1'}
        one, two = THEMES[variant][slot[c1]], THEMES[variant][slot[c2]]
        return RGBColor(*[int(int(one[i:i + 2], 16) * (1 - amount) + int(two[i:i + 2], 16) * amount) for i in (0, 2, 4)])

    def glow(s, cx, cy, r, value='4FC3F7'):
        """The demo's glowing marker: a soft radial fade with a bright core."""
        o = s.shapes.add_shape(MSO_SHAPE.OVAL, px(cx - r), px(cy - r), px(2 * r), px(2 * r))
        o.line.fill.background()
        o.fill.background()
        sp = o._element.spPr
        sp.remove(sp.find(qn('a:noFill')))
        sp.find(qn('a:prstGeom')).addnext(etree.fromstring(f'''<a:gradFill xmlns:a="{NS['a']}" rotWithShape="1"><a:gsLst><a:gs pos="0"><a:srgbClr val="{value}"/></a:gs><a:gs pos="100000"><a:srgbClr val="0B0B0C"/></a:gs></a:gsLst><a:path path="circle"><a:fillToRect l="50000" t="50000" r="50000" b="50000"/></a:path></a:gradFill>'''))
        c = s.shapes.add_shape(MSO_SHAPE.OVAL, px(cx - 12), px(cy - 12), px(24), px(24))
        c.fill.solid()
        c.fill.fore_color.rgb = WHITE
        c.line.fill.background()
        return o, c

    def table(s, x, y, widths, heights, rows, style=None, name='Table'):
        """A native table with no boxes: a quiet header, and a hairline under each row."""
        frame = s.shapes.add_table(len(rows), len(widths), px(x), px(y), px(sum(widths)), px(sum(heights)))
        frame.name = name
        tbl = frame.table
        tp = tbl._tbl.tblPr
        for a in ('firstRow', 'bandRow'):
            tp.set(a, '0')
        sid = tp.find(qn('a:tableStyleId'))
        if sid is not None:
            sid.text = '{2D5ABB26-0587-4C30-8999-92F81FD0307C}'
        for j, w_ in enumerate(widths):
            tbl.columns[j].width = px(w_)
        for i, row_ in enumerate(rows):
            tbl.rows[i].height = px(heights[i])
            for j, val in enumerate(row_):
                cell = tbl.cell(i, j)
                st = dict(size=T_BODY, color=TEXT, font=BODY, align=LEFT)
                if i == 0:
                    st.update(size=T_LABEL, color=SUB, font=BODY)
                if style and i:
                    st.update(style(i, j, val) or {})
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                cell.margin_left, cell.margin_right = 0, px(8)
                cell.margin_top = cell.margin_bottom = 0
                par = cell.text_frame.paragraphs[0]
                par.alignment = st['align']
                par.line_spacing = 1.05
                run = par.add_run()
                run.text = val
                run.font.size, run.font.bold, run.font.name = fs(st['size']), False, st['font']
                paint(run.font.color, st['color'])
                cell.fill.background()
                ln = etree.Element(qn('a:lnB'))
                ln.set('w', str(int(fs(1.0))))
                sf = etree.SubElement(ln, qn('a:solidFill'))
                etree.SubElement(sf, qn('a:schemeClr')).set('val', 'tx2' if i == 0 else 'accent2')
                cell._tc.get_or_add_tcPr().insert(0, ln)
        return frame

    # ------------------------------------------------------------ 1. Cover
    s, t = new('Opening', ink)
    pill = box(s, -240, 96, 1040, 464, WHITE, 'Title pill')
    pill._element.spPr.find(qn('a:prstGeom')).set('prst', 'roundRect')
    gd = etree.SubElement(pill._element.spPr.find(qn('a:prstGeom')).find(qn('a:avLst')), qn('a:gd'))
    gd.set('name', 'adj')
    gd.set('fmla', 'val 50000')
    s.shapes._spTree.remove(pill._element)
    s.shapes._spTree.insert(2, pill._element)
    set_title(s, 'Beyond\nSkia', T_HERO, M, 124, gw(7), 270, INK)
    text(s, M, 412, gw(7) - 40, 90, 'GPU scheduling and profiling with Impeller on Android 10+', T_BODY, GREY, spacing=1.14)
    photo = s.shapes.add_picture(os.path.join(L, 'speaker.jpg'), px(gx(8)), px(96), px(gw(4)), px(gw(4) * 400 / 340))
    photo._element.find('.//' + qn('p:cNvPr')).set('descr', 'Collins Munene')
    geom = photo._element.find('.//' + qn('a:prstGeom'))
    geom.set('prst', 'round2SameRect')
    av = geom.find(qn('a:avLst'))
    for key, val in (('adj1', 50000), ('adj2', 0)):
        gd = etree.SubElement(av, qn('a:gd'))
        gd.set('name', key)
        gd.set('fmla', f'val {val}')
    display(s, gx(8), 530, gw(4), 44, 'Collins Munene', T_H3, PAPER)
    text(s, gx(8), 578, gw(4) + 40, 30, 'DevOps and Software Engineer, Shipht', T_LABEL, ASH, spacing=1.0, track=-20)

    # ------------------------------------------------------------ 2. The map
    s, t = new()
    set_title(s, 'Impeller tamed\none kind of jank.', T_HERO, M, 84, W, 280)
    rule(s, M, 396, RIGHT_EDGE, 396, TEXT, 1)
    text(s, gx(0), 420, gw(6), 32, 'Tamed', T_SMALL, SUB, spacing=1.0)
    display(s, gx(0), 456, gw(6), 66, 'Compilation jank', T_H1, SUB)
    text(s, gx(6), 420, gw(6), 32, 'Still yours to fix', T_SMALL, SUB, spacing=1.0)
    display(s, gx(6), 456, gw(6), 66, 'Drawing cost', T_H1, ACC)

    # ------------------------------------------------------------ 3. One frame, and who does what
    s, t = page('One frame, from vsync to pixels.', 'How Flutter draws', sub='Dart is your code. The engine is the C++ underneath it, inside your app.')
    text(s, M, CT_SUB + 16, W, 28, 'vsync: the screen’s tick, time for a new frame', T_LABEL, SUB, spacing=1.0)
    rule(s, M, 216, RIGHT_EDGE, 216, TEXT, 1)
    for i, (thread, verb, how, hot) in enumerate((('Dart, on the main thread', 'Records', 'paint() draws nothing. It writes a DisplayList.', False),
                                                  ('Engine, on 1.raster', 'Prepares', 'Pipelines, triangles, commands. This is CPU time.', True),
                                                  ('GPU hardware', 'Executes', 'Later, on its own schedule. Not a Flutter thread.', False))):
        x, w_ = gx(i * 4), gw(4)
        a = rule(s, x, 216, x, 230, TEXT, 1)
        b = text(s, x, 246, w_, 30, thread, T_SMALL, SUB, spacing=1.0)
        c = display(s, x, 290, w_, 92, verb, T_NUM, ACC if hot else TEXT)
        d = text(s, x, 394, w_, 180, how, T_BODY, SUB, spacing=1.18)
        t.click(fx(a), fx(b), fx(c), fx(d, delay=120))

    # ------------------------------------------------------------ 4. The budget
    s, t = page('Every frame gets 8.3 ms.', sub='A train leaves every 8.3 ms. Miss it, and the screen shows the old frame again.')
    X0, X1 = gx(3), RIGHT_EDGE
    K = (X1 - X0) / 33.32
    for i in range(5):
        x = X0 + i * 8.33 * K
        rule(s, x, 196, x, CB)
        if i:
            text(s, x - 78, CT_SUB, 72, 26, ('8.3', '16.7', '25', '33.3')[i - 1], T_LABEL, SUB, MONO, RIGHT, spacing=1.0)
    text(s, X0, CT_SUB, 90, 26, '0 ms', T_LABEL, SUB, MONO, spacing=1.0)
    rows = ((208, 'Target', ['4 + 4 ms', '120 fps'], [(i * 8.33, 4) for i in range(4)], [(i * 8.33 + 4, 4) for i in range(4)], SUB, TEXT, TEXT),
            (352, 'Limit', ['8.3 ms each', '120 fps'], [(i * 8.33, 8.33) for i in range(4)], [((i + 1) * 8.33, 8.33) for i in range(3)], SUB, TEXT, TEXT),
            (496, 'Measured', ['28 ms raster', '36 fps'], trace['broken']['ui'], trace['broken']['raster'], SUB, ACC, ACC))
    for y, name, how, ui, raster, c1, c2, c3 in rows:
        a = display(s, M, y, gw(2) + 20, 46, name, T_H3, c3)
        b = text(s, M, y + 50, gw(2) + 4, 56, how, T_LABEL, SUB, spacing=1.1)
        l1 = text(s, X0 - 92, y + 8, 80, 28, 'UI', T_LABEL, SUB, MONO, RIGHT, spacing=1.0)
        l2 = text(s, X0 - 92, y + 66, 80, 28, 'Raster', T_LABEL, SUB, MONO, RIGHT, spacing=1.0)
        g1 = blocks(s, ui, y, 48, c1, X0, K, X1, f'{name}: UI')
        g2 = blocks(s, raster, y + 58, 48, c2, X0, K, X1, f'{name}: raster')
        t.click(fx(a), fx(b), fx(l1), fx(l2), fx(g1, 'left', dur=600), fx(g2, 'left', dur=600, delay=150))
    source(s, 'Top rows drawn to scale. Bottom row: real frames from a system trace on the phone.')

    # ------------------------------------------------------------ 5. Compilation jank
    s, t = page('Compilation jank.', 'Before: Skia', sub='The first time a new effect appears, the app stops to compile it.')
    flow = text(s, M, CT_SUB + 2, W, 32, [[('new paint + blend + clip', {'color': TEXT}), ('  →  SkSL  →  GLSL  →  driver compile  →  ', {'color': SUB}), ('missed frame', {'color': ACC})]], T_CODE, TEXT, MONO, spacing=1.0)
    t.click(fx(flow))
    num = display(s, gx(0), 208, gw(6), 196, '1.8 s', T_MEGA, ACC, name='One frame')
    cap = text(s, gx(6), 244, gw(6), 110, ['118 shaders, compiled inside', 'one frame. About 14.5 ms each.'], T_H3, TEXT, HEAD, spacing=1.14, track=-30)
    PK = W / 1820
    prog = s.shapes.add_group_shape()
    for i in range(118):
        r = prog.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(M + i * 14.525 * PK), px(412), px(14.6 * PK - 1.6), px(112))
        r.fill.solid()
        paint(r.fill.fore_color, ACC)
        r.line.fill.background()
    prog.name = '118 Skia programs in one frame, drawn to scale'
    bud = box(s, M, 544, max(8.33 * PK, 5.2), 36, TEXT, 'One frame budget, 8.3 ms, to the same scale')
    budl = text(s, M + 20, 544, 800, 36, '8.3 ms: one frame’s budget, same scale', T_SMALL, TEXT, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0)
    t.click(fx(num), fx(cap, delay=150), fx(prog, 'left', dur=1100, delay=250), fx(bud, delay=1100), fx(budl, delay=1100))
    source(s, 'Real Skia trace on the Infinix, to scale: 1,714 ms of programs in a 1,820 ms frame. 144 new effects.')

    # ------------------------------------------------------------ 6. The engine, before and now
    s, t = page('The Android engine, before and now.', 'Now: Impeller')
    BX_, NX_, BW_, NW_ = gx(3), gx(7), gw(4), gw(5)
    display(s, BX_, CT, BW_, 46, 'Before: Skia', T_H3, SUB)
    now_head = display(s, NX_, CT, NW_, 46, 'Now: Impeller', T_H3, TEXT)
    rule(s, M, 184, RIGHT_EDGE, 184, TEXT)
    now_cells = [now_head]
    for i, (label, was, now, hot_was, hot_now) in enumerate((('Compiled ahead', 'Nothing', 'impellerc: SPIR-V, Metal, GLSL ES', False, False),
                                                             ('Dart runs on', '1.ui', 'The main thread, since 3.29', False, False),
                                                             ('1.raster', 'Writes and compiles shaders, then draws', 'Binds pipelines, tessellates, records commands', True, True),
                                                             ('Raster cache', 'Automatic', 'None', False, True),
                                                             ('GPU API', 'OpenGL ES: the driver decides', 'Vulkan: explicit commands', False, False))):
        y = 184 + i * 90
        text(s, gx(0), y, gw(3), 90, label, T_BODY, TEXT, HEAD, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0, track=-20)
        text(s, BX_, y, BW_, 90, was, T_BODY, ACC if hot_was else SUB, anchor=MSO_ANCHOR.MIDDLE, spacing=1.08)
        now_cells.append(text(s, NX_, y, NW_, 90, now, T_BODY, ACC if hot_now else TEXT, MID, anchor=MSO_ANCHOR.MIDDLE, spacing=1.08))
        rule(s, M, y + 90, RIGHT_EDGE, y + 90)
    t.click(*[fx(x, delay=i * 120) for i, x in enumerate(now_cells)])
    source(s, 'Android, simplified. iOS and macOS use Metal. Dart moved in 3.29, separately: my Skia build does it too.')

    # ------------------------------------------------------------ 7. Late and early
    s, t = page('Skia compiles late. Impeller compiles early.', sub='Skia writes the recipe after you order. Impeller preps the kitchen first.')
    stages = ('Engine build', 'App build', 'App start', 'First use', 'Every frame')
    col_x = [gx(2 + 2 * i) for i in range(5)]
    CWD = gw(2)
    for x, st in zip(col_x, stages):
        text(s, x, CT_SUB, CWD + 20, 26, st, T_LABEL, SUB, spacing=1.0)
    rule(s, M, 196, RIGHT_EDGE, 196, TEXT)
    rule(s, M, 412, RIGHT_EDGE, 412)
    display(s, gx(0), 212, gw(2) + 16, 46, 'Skia', T_H3, TEXT)
    text(s, gx(0), 260, gw(2), 28, 'JIT', T_CODE, SUB, MONO, spacing=1.0)
    display(s, gx(0), 428, gw(2) + 16, 46, 'Impeller', T_H3, TEXT)
    text(s, gx(0), 476, gw(2), 28, 'AOT', T_CODE, SUB, MONO, spacing=1.0)
    CH = 184
    skia = (text(s, col_x[0], 212, CWD, CH, 'Nothing yet', T_SMALL, SUB),
            text(s, col_x[1], 212, CWD, CH, 'Your .frag stays as SkSL text', T_SMALL, SUB, spacing=1.12),
            text(s, col_x[2], 212, CWD, CH, 'Warm-up, if you wrote one', T_SMALL, SUB, spacing=1.12),
            label_box(s, col_x[3], 212, CWD, CH, 'Write and compile, in the frame\n14.5 ms each', ACC, WHITE if not dark else INK, T_SMALL),
            text(s, col_x[4], 212, CWD, CH, 'Bind the cached program', T_SMALL, SUB, spacing=1.12))
    t.click(*[fx(x, delay=i * 70) for i, x in enumerate(skia)])
    imp = (label_box(s, col_x[0], 428, CWD, CH, 'impellerc: engine shaders', TEXT, BG, T_SMALL),
           label_box(s, col_x[1], 428, CWD, CH, 'impellerc: your .frag', TEXT, BG, T_SMALL),
           text(s, col_x[2], 428, CWD, CH, 'Most pipelines are built', T_SMALL, TEXT, spacing=1.12),
           text(s, col_x[3], 428, CWD, CH, 'A missing pipeline: 2.2 ms each, in the frame', T_SMALL, TEXT, spacing=1.12),
           text(s, col_x[4], 428, CWD, CH, 'Bind a built pipeline', T_SMALL, TEXT, spacing=1.12))
    t.click(*[fx(x, delay=i * 70) for i, x in enumerate(imp)])
    source(s, 'A pipeline is shader code plus fixed GPU state. On Vulkan, the driver finishes the compile when it is built. Infinix traces.')

    # ------------------------------------------------------------ 8. Which backend
    s, t = page('On Android, Vulkan isn’t guaranteed.', sub='The default since Flutter 3.27, on Android 10+ (API 29+). There’s a catch.')
    rule(s, M, CT_SUB, RIGHT_EDGE, CT_SUB, TEXT)
    for i, (when, what, c) in enumerate((('Android 9 or older', 'Skia on OpenGL ES', SUB),
                                         ('Android 10+, a device check fails', 'Impeller on OpenGL ES', ACC),
                                         ('Android 10+, every check passes', 'Impeller on Vulkan', TEXT))):
        y = CT_SUB + i * 80
        text(s, gx(0), y, gw(6), 80, when, T_BODY, SUB if i == 0 else TEXT, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0)
        text(s, gx(6), y, gw(6), 80, what, T_H3, c, HEAD, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0, track=-30)
        rule(s, M, y + 80, RIGHT_EDGE, y + 80)
    checks = text(s, M, 424, W, 28, 'The checks, in this engine', T_LABEL, SUB, spacing=1.0)
    what_ = text(s, M, 456, W, 76, ['Emulator. Huawei. MediaTek with a vendor API below 32. Adreno 650 or older.', 'Some Exynos chips. No working Vulkan 1.1 with the extensions Impeller needs.'], T_SMALL, TEXT, spacing=1.2)
    t.click(fx(checks), fx(what_))
    proof = text(s, M, 556, W, 32, 'adb logcat | grep "Impeller rendering backend"', T_CODE, ACC, MONO, spacing=1.0)
    t.click(fx(proof))
    source(s, 'From the Flutter 3.47.8 engine source. My Impeller numbers ran on Vulkan, per the log.')

    # ------------------------------------------------------------ 9. Scoreboard, and how it grows
    s, t = page('Same app. Same phone. Two renderers.', 'The proof')
    phone_ = tall(s, os.path.join(L, 'poster-impeller-cold.png'), (0, 0.035, 0, 0.012), 'Shader Storm in the demo app, on the phone, before a reveal')
    END = phone_.left / 9525 - GUT
    CX = (gx(2), gx(5))
    text(s, CX[0], CT, gw(3), 30, 'First reveal', T_SMALL, SUB, spacing=1.0)
    text(s, CX[1], CT, gw(3), 30, 'Second time', T_SMALL, SUB, spacing=1.0)

    def score(x, y, value, color=TEXT):
        return text(s, x, y, gw(3), 120, [[(value, {'color': color}), (' ms', {'size': T_SMALL, 'color': SUB, 'track': 0})]], T_NUM, TEXT, HEAD, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0, track=-80)
    rule(s, M, 172, END, 172, TEXT)
    rule(s, M, 300, END, 300)
    rule(s, M, 428, END, 428)
    text(s, gx(0), 172, gw(2), 128, 'Skia', T_H3, SUB, HEAD, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0, track=-30)
    text(s, gx(0), 300, gw(2) + 16, 128, 'Impeller', T_H3, TEXT, HEAD, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0, track=-30)
    a = score(CX[0], 176, '1,863', ACC)
    t.click(fx(a))
    b_ = score(CX[1], 176, '23', SUB)
    t.click(fx(b_))
    c = score(CX[0], 304, '145')
    d = score(CX[1], 304, '48')
    t.click(fx(c), fx(d, delay=250))
    e = display(s, M, 452, END - M, 66, '13× shorter', T_H1, TEXT)
    f = text(s, M, 530, END - M, 90, ['It barely grows. From 48 to 144 new effects:', 'Skia 687 → 1,863 ms. Impeller 127 → 145 ms.'], T_SMALL, SUB, spacing=1.2)
    t.click(fx(e), fx(f, delay=200))
    source(s, 'Worst frame, median of 3 rounds. Infinix X6873, Mali-G615, 120 Hz. Skia on OpenGL ES, Impeller on Vulkan.')

    # ------------------------------------------------------------ 10. The cost moved
    s, t = page('The cost shrank and moved. It didn’t vanish.')
    TK = W / 1714
    a1 = display(s, M, CT + 8, gw(8), 46, 'Skia: 118 shaders', T_H3, TEXT)
    a2 = display(s, gx(8), CT + 8, gw(4), 46, '1,714 ms', T_H3, ACC, RIGHT)
    g = s.shapes.add_group_shape()
    for i in range(118):
        r = g.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(M + i * 14.53 * TK), px(190), px(14.53 * TK - 1.6), px(88))
        r.fill.solid()
        paint(r.fill.fore_color, ACC)
        r.line.fill.background()
    g.name = '118 Skia programs, to scale'
    b1 = display(s, M, 316, gw(8), 46, 'Impeller: 40 pipelines', T_H3, TEXT)
    b2 = display(s, gx(8), 316, gw(4), 46, '87 ms', T_H3, TEXT, RIGHT)
    b3 = box(s, M, 368, 87 * TK, 88, TEXT, '40 Impeller pipelines, to scale')
    c1 = text(s, M, 504, W, 84, 'Both on the raster thread, both in the frame. Impeller only builds from shaders it already compiled.', T_BODY, SUB, spacing=1.18)
    t.click(fx(a1), fx(a2), fx(g, 'left', dur=900), fx(b1, delay=500), fx(b2, delay=500), fx(b3, 'left', dur=400, delay=500), fx(c1, delay=900))
    source(s, 'System traces of one cold reveal on the Infinix, tracing on, drawn to scale.')

    # ------------------------------------------------------------ 11. Tessellation
    s, t = page('Tessellation: how a path becomes triangles.', 'Inside a frame', sub='The GPU only fills triangles, so the CPU cuts every path into them.')
    WX = lambda v: gx(0) + 12 + (v - 10) * (gw(8) - 24) / 450
    WY = lambda v: 292 + (v - 30) * 1.25
    steps = (('Path', 'What you ask for'), ('Points', 'Curves flatten'), ('Vertices', 'Two per point'), ('Triangles', 'v − 2 of them'))
    pts, edges = strip_edges(16)
    head_ = []
    for i, (h_, d) in enumerate(steps):
        x = gx(i * 2)
        h1 = text(s, x, CT_SUB, gw(2) + 24, 36, h_, T_BODY, TEXT, HEAD, spacing=1.0, track=-20)
        h2 = text(s, x, CT_SUB + 38, gw(2) + 24, 28, d, T_LABEL, SUB, spacing=1.0)
        head_.append((h1, h2))
    path = polyline(s, [(WX(a), WY(b)) for a, b in bezier()], TEXT, 3, 'The path')
    points = dots(s, [(WX(a), WY(b)) for a, b in pts], TEXT, 9, 'Flattened points')
    verts = dots(s, [(WX(a), WY(b)) for e in edges for a, b in e], ACC, 8, 'Vertices')
    tris = s.shapes.add_group_shape()
    zig = [(WX(a), WY(b)) for e in edges for a, b in e]
    for i in range(len(zig) - 1):
        ln = tris.shapes.add_connector(1, px(zig[i][0]), px(zig[i][1]), px(zig[i + 1][0]), px(zig[i + 1][1]))
        paint(ln.line.color, TEXT)
        ln.line.width = fs(1)
    for i in range(len(edges) - 1):
        for side in (0, 1):
            ln = tris.shapes.add_connector(1, px(WX(edges[i][side][0])), px(WY(edges[i][side][1])), px(WX(edges[i + 1][side][0])), px(WY(edges[i + 1][side][1])))
            paint(ln.line.color, TEXT)
            ln.line.width = fs(1)
    tris.name = 'Triangle strip'
    t.click(fx(head_[0][0]), fx(head_[0][1]), fx(path, 'left', dur=900))
    t.click(fx(head_[1][0]), fx(head_[1][1]), fx(points, 'left', dur=700))
    t.click(fx(head_[2][0]), fx(head_[2][1]), fx(verts, 'left', dur=700))
    t.click(fx(head_[3][0]), fx(head_[3][1]), fx(tris, 'left', dur=900))
    lens = shot(s, os.path.join(A, 'clips', 'xray.png'), gx(8), CT_SUB, gw(4), (0.174, 0.134, 0.424, 0.744), alt='The X-ray lens in the demo app: a price line cut into triangles')
    lens_cap = text(s, gx(8), 416, gw(4), 84, 'The app’s X-ray lens: a model of these steps, on the real path.', T_LABEL, SUB, spacing=1.14)
    bottom = text(s, M, 552, W, 54, [[('The demo at 8×: 16 lines × 8,000 points × 2 = ', {'color': SUB}), ('256,000+', {'color': ACC}), (' vertices.', {'color': SUB})]], T_H3, TEXT, HEAD, spacing=1.0, track=-30)
    t.click(fx(lens), fx(lens_cap), fx(bottom, delay=200))
    source(s, 'Illustration. On the CPU, every frame. Vertex count worked out from stroke_path_geometry.cc, not measured.')

    # ------------------------------------------------------------ 12. Command buffers
    s, t = page('The CPU records. The GPU executes.', sub='The waiter writes the order. The kitchen cooks later. That’s GPU scheduling.')
    code(s, gx(0), CT_SUB, gw(5), 400, ['// You write', 'canvas.drawCircle(c, r, paint);', '', '// Impeller records', 'begin render pass', '  bind pipeline', '  bind vertex buffer', '  bind uniforms', '  draw', 'end render pass', 'submit to queue, fence'])
    LX, BX = gx(5), gx(6) + GUT
    BW = RIGHT_EDGE - BX
    rule(s, LX, CT_SUB, RIGHT_EDGE, CT_SUB, TEXT)
    for name, y in (('1.raster', 180), ('queue', 300), ('GPU', 420)):
        text(s, LX, y, BX - LX - 8, 84, name, T_CODE, SUB, MONO, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0)
        rule(s, LX, y + 102, RIGHT_EDGE, y + 102)
    fxs = []
    for i, (off, c) in enumerate(((0, TEXT), (250, SUB))):
        d0 = i * 900
        r1 = box(s, BX + off, 180, 200, 84, c, f'Frame {i + 1}: recorded')
        r2 = box(s, BX + off + 202, 300, 12, 84, c, f'Frame {i + 1}: submitted')
        r3 = box(s, BX + off + 220, 420, 190 if i == 0 else BW - off - 220, 84, c, f'Frame {i + 1}: executed')
        fxs += [fx(r1, 'left', dur=500, delay=d0), fx(r2, delay=d0 + 450), fx(r3, 'left', dur=500, delay=d0 + 550)]
    fence = rule(s, BX + 410, 420, BX + 410, 560, TEXT, 1, 'dash')
    fword = text(s, BX + 420, 530, 120, 28, 'fence', T_CODE, TEXT, MONO, spacing=1.0)
    t.click(*fxs, fx(fence, delay=1500), fx(fword, delay=1500))
    source(s, 'Illustration of the order of work, not a measured trace.')

    # ------------------------------------------------------------ 13. Overdraw
    s, t = page('Overdraw: painting the same pixel again.', sub='Like painting a wall three times. Only the last coat shows.')

    def screen(x, heat):
        y0, w0, h0 = 198, gw(3), 430
        ON = WHITE if not dark else INK
        fills = (mix(BG, ACC, 0.22), mix(BG, ACC, 0.55), ACC) if heat else (mix(BG, SUB, 0.45), BG if dark else WHITE, TEXT)
        shapes = [box(s, x, y0, w0, h0, fills[0], 'Background image')]
        shapes.append(box(s, x + 24, y0 + 180, w0 - 48, 170, fills[1], 'Card'))
        shapes.append(box(s, x + 48, y0 + 250, w0 - 96, 48, fills[2], 'Text'))
        if heat:
            shapes.append(text(s, x + 14, y0 + 12, 80, 36, '1×', T_BODY, TEXT, HEAD, spacing=1.0))
            shapes.append(text(s, x + 38, y0 + 192, 80, 36, '2×', T_BODY, TEXT, HEAD, spacing=1.0))
            shapes.append(text(s, x + 48, y0 + 250, w0 - 96, 48, '3×', T_BODY, ON, HEAD, CENTER, MSO_ANCHOR.MIDDLE, spacing=1.0))
        return shapes
    text(s, gx(0), CT_SUB, gw(3), 26, 'What you see', T_LABEL, SUB, spacing=1.0)
    screen(gx(0), False)
    cap = text(s, gx(3), CT_SUB, gw(3), 26, 'How often it’s drawn', T_LABEL, SUB, spacing=1.0)
    t.click(fx(cap), *[fx(x) for x in screen(gx(3), True)])
    code(s, gx(6), 198, gw(6), 260, ['Stack(', '  children: [', '    Image.asset(\'bg.png\'),      // 1×', '    Card(                       // 2×', '      child: Text(\'KSh 1,200\'), // 3×', '    ),', '  ],', ')'])
    text(s, gx(6), 476, gw(6), 156, 'The image behind the card still costs work. The engine and GPU skip some of it, so measure before you fix.', T_BODY, TEXT, spacing=1.16)
    source(s, 'Illustration. Impeller merges full-screen solid colours into the clear; Mali can kill hidden pixels. Not measured in my demo.')

    # ------------------------------------------------------------ 14. The layer
    s, t = page('Why a layer costs more than a draw.', sub='The GPU wants to run like a firehose. A layer makes it change direction.')
    FG = WHITE if not dark else INK
    display(s, M, CT_SUB, W, 44, 'One render pass', T_H3, TEXT)
    x = M
    for w_, words, hot in ((110, 'Clear', False), (746, 'All draws, in fast tile memory', False), (130, 'Resolve', False), (150, 'Store once', True)):
        label_box(s, x, 212, w_ - 3, 76, words, ACC if hot else CARD, FG if hot else TEXT)
        x += w_
    head2 = display(s, M, 312, W, 44, 'With one saveLayer', T_H3, TEXT)
    second = []
    x = M
    for w_, words, hot in ((150, 'Draws so far', False), (116, 'Store', True), (316, 'Offscreen pass: draw and blur', False), (116, 'Store', True), (116, 'Load', True), (176, 'Composite', False), (146, 'Store', True)):
        second.append(label_box(s, x, 360, w_ - 3, 76, words, ACC if hot else CARD, FG if hot else TEXT))
        x += w_
    t.click(fx(head2), *[fx(b_, 'left', dur=250, delay=i * 130) for i, b_ in enumerate(second)])
    text(s, M, 468, W, 40, 'Measured: 64 saveLayer a frame. Removing them cut raster from 13.7 to 6.6 ms.', T_BODY, TEXT, MID, spacing=1.0)
    text(s, M, 516, W, 40, 'The GPU side is the model. This phone’s driver doesn’t expose it.', T_BODY, SUB, spacing=1.0)
    source(s, 'Illustration, not to scale. The accent marks a trip to main memory.')

    # ------------------------------------------------------------ 15. What it didn't fix, and the bill
    s, t = new('What Impeller didn’t fix', ink)
    set_title(s, 'What Impeller\ndidn’t fix.', T_NUM, M, 44, gw(8), 170, PAPER)
    text(s, M, 216, gw(8), 40, 'If compiling shaders isn’t the problem, what is?', T_BODY, ASH, spacing=1.0)
    bill = []
    for x, w_, val, name, c in ((gx(0), gw(3), '129,920', 'path points', EMBER), (gx(3), gw(2), '624', 'draw calls', PAPER), (gx(5), gw(3), '64', 'offscreen layers', PAPER)):
        bill.append(display(s, x, 286, w_ + 20, 90, val, T_NUM, c))
        bill.append(text(s, x, 378, w_ + 20, 32, name, T_SMALL, ASH, spacing=1.0))
    bill.append(text(s, M, 446, gw(8), 40, [[('UI 15.9 ms.  ', {'color': PAPER}), ('Raster 29.7 ms.  ', {'color': EMBER}), ('Budget 8.3 ms.', {'color': ASH})]], T_BODY, PAPER, MID, spacing=1.0))
    bill.append(text(s, M, 506, gw(8) + 20, 100, 'Nothing is compiling. This is pure drawing cost.', T_H3, PAPER, HEAD, spacing=1.08, track=-30))
    t.click(*[fx(x, delay=i * 60) for i, x in enumerate(bill)])
    source(s, 'My demo’s dial, not a Flutter limit: 8× is 16 lines of 8,000 points. Canvas Thrash, p90, median of 3 rounds.', color=ASH)
    shot(s, os.path.join(L, 'poster-thrash-broken.png'), RIGHT_EDGE - 300, 0, 300, (0, 0.045, 0, 0.02), alt='Canvas Thrash in the demo app at 8×: both lanes red')

    # ------------------------------------------------------------ 16. The vote
    s, t = page('Which fix helps most, on its own?')
    BX2, BASE = gx(4), gx(10) + 40
    BK2 = (BASE - BX2) / 29.7
    text(s, BASE - 300, CT + 2, 294, 26, 'No fixes: 29.7 ms', T_LABEL, TEXT, align=RIGHT, spacing=1.0)
    rule(s, M, 164, RIGHT_EDGE, 164, TEXT)
    fxs = []
    for i, (name, why, v) in enumerate((('Simplify paths', 'Fewer points', 18.6), ('Batch draws', 'Fewer draw calls', 28.6), ('Glow without layers', 'No offscreen passes', 21.2), ('Isolate repaints', 'Less Dart re-recording', 25.2))):
        y = 180 + i * 114
        display(s, gx(0), y, gw(4) + 20, 46, name, T_H3, TEXT)
        text(s, gx(0), y + 50, gw(4), 30, why, T_SMALL, SUB, spacing=1.0)
        hot = i == 0
        b = box(s, BX2, y + 4, v * BK2, 74, ACC if hot else CARD, f'{name}: {v} ms')
        n = text(s, BASE + 16, y + 4, RIGHT_EDGE - BASE - 16, 74, str(v), T_H3, ACC if hot else TEXT, HEAD, RIGHT, MSO_ANCHOR.MIDDLE, spacing=1.0, track=-30)
        fxs += [fx(b, 'left', dur=700, delay=i * 120), fx(n, delay=500 + i * 120)]
    t.click(*fxs)
    rule(s, BASE, 164, BASE, CB, TEXT, 1.5)
    source(s, 'Raster p90 at 8×, each fix alone, median of 3 rounds. Batch and Isolate are within noise. None reaches 8.3 ms.')

    # ------------------------------------------------------------ 17. Fix 1
    s, t = page('Fix 1: Simplify paths.', sub='Same chart. Can you see the difference?')
    CROP = (0.03, 0.112, 0.03, 0.525)
    shot(s, os.path.join(L, 'poster-thrash-broken.png'), gx(0), CT_SUB, gw(3), CROP, radius=8, alt='The chart at 8× with 129,920 path points')
    text(s, gx(0), 396, gw(3), 30, '129,920 path points', T_SMALL, ACC, MID, spacing=1.0)
    a_ = shot(s, os.path.join(L, 'poster-thrash-simplify.png'), gx(3), CT_SUB, gw(3), CROP, radius=8, alt='The same chart with 12,032 path points')
    b_ = text(s, gx(3), 396, gw(3), 30, '12,032 path points', T_SMALL, TEXT, MID, spacing=1.0)
    ch = [change(s, gx(6), CT_SUB + i * 94, gw(6), lab, a, b, T_H1, u) for i, (lab, a, b, u) in enumerate((('Points a line, at the demo’s 8× setting', '8,000', '632', None), ('Raster p90', '29.7', '18.6', 'ms'), ('UI p90', '15.9', '6.3', 'ms')))]
    t.click(fx(a_), fx(b_), *[fx(x, delay=400) for pair in ch for x in pair])
    code(s, gx(0), 456, gw(6), 170, ['!!A new path, every frame', 'final path = Path();', 'for (var k = 0; k < n; k++) // n = 8,000', '  path.lineTo(x(k), y(k));'])
    code(s, gx(6), 456, gw(6), 170, ['++Simplify once, then only move it', 'final xy = decimate(series, plot.width);', 'canvas..translate(shift, 0)', '      ..drawPath(cached, stroke);'])
    source(s, 'Real screens from the app at 8×. Code condensed from thrash_canvas.dart. p90, median of 3 rounds.')

    # ------------------------------------------------------------ 18. Fix 2
    s, t = page('Fix 2: Batch draws.', sub='480 trips to the shop, or one trip with a list.')
    BARS = 30
    SW_, BH = gw(6) / BARS, 72
    heights = [0.5 + 0.25 * math.sin(k / BARS * 6 * math.pi) + 0.15 * math.sin(k / BARS * 40 * math.pi) for k in range(BARS)]
    text(s, gx(0), CT_SUB, gw(6), 30, 'Before: 480 draws', T_SMALL, ACC, MID, spacing=1.0)
    before_ = s.shapes.add_group_shape()
    for k, v in enumerate(heights):
        r = before_.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(gx(0) + k * SW_), px(198 + BH * (1 - v)), px(SW_ - 5), px(BH * v))
        r.fill.solid()
        paint(r.fill.fore_color, ACC)
        r.line.fill.background()
    before_.name = 'Heat strip: each segment is its own draw'
    a_ = text(s, gx(0), 288, gw(6), 30, 'After: 1 draw', T_SMALL, TEXT, MID, spacing=1.0)
    after_ = s.shapes.add_group_shape()
    for k, v in enumerate(heights):
        r = after_.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(gx(0) + k * SW_), px(322 + BH * (1 - v)), px(SW_ + 0.5), px(BH * v))
        r.fill.solid()
        paint(r.fill.fore_color, TEXT)
        r.line.fill.background()
    after_.name = 'Heat strip: all segments in one draw'
    ch = [change(s, gx(6), CT_SUB + i * 118, gw(6), lab, a, b, T_H1, u) for i, (lab, a, b, u) in enumerate((('Draw calls', '640', '161', None), ('Raster p90', '18.6', '13.7', 'ms')))]
    t.click(fx(a_), fx(after_, 'left', dur=700), *[fx(x, delay=400) for pair in ch for x in pair])
    code(s, gx(0), 430, gw(6), 180, ['!!Before: one draw per segment', 'for (final segment in segments) {', '  canvas.drawPath(segment, paint);', '}'])
    code(s, gx(6), 430, gw(6), 180, ['++After: two triangles each, one draw', 'canvas.drawVertices(', '  Vertices.raw(triangles, positions,', '    colors: colors),', '  BlendMode.dst, p);'])
    source(s, 'Illustration of the heat strip. Code condensed from thrash_canvas.dart. Starts at 640 because Fix 1 draws each line twice.')

    # ------------------------------------------------------------ 19. Fix 3
    s, t = page('Fix 3: Glow without saveLayer.', sub='The same glow, without the detour.')
    box(s, gx(0), CT_SUB, gw(6), 216, INK, 'The glow, before and after')
    cx1, cx2 = gx(0) + gw(6) * 0.25, gx(0) + gw(6) * 0.75
    glow(s, cx1, CT_SUB + 92, 68)
    glow(s, cx2, CT_SUB + 92, 68)
    text(s, cx1 - 130, CT_SUB + 174, 260, 28, 'saveLayer + blur', T_LABEL, ASH, MONO, CENTER, spacing=1.0)
    text(s, cx2 - 130, CT_SUB + 174, 260, 28, 'radial gradient', T_LABEL, PAPER, MONO, CENTER, spacing=1.0)
    ch = [change(s, gx(6), CT_SUB + i * 74, gw(6), lab, a, b, T_H3, u) for i, (lab, a, b, u) in enumerate((('saveLayer a frame', '64', '0', None), ('Raster p90', '13.7', '6.6', 'ms'), ('QueueSubmit a frame', '2', '1', None)))]
    code(s, gx(0), 402, gw(6), 70, ['!!Before, per dot: a pass and a blur', 'canvas.saveLayer(bounds, blurPaint);'])
    code(s, gx(6), 402, gw(6), 70, ['++After: same soft edge, main pass', 'canvas.drawCircle(c, r, radialPaint);'])
    rule(s, M, 486, RIGHT_EDGE, 486)
    text(s, M, 504, W, 32, 'You may have this in your app. These can trigger a saveLayer:', T_SMALL, SUB, spacing=1.0)
    text(s, M, 544, W, 32, [[('Opacity', {}), (' · ', {'color': SUB}), ('ShaderMask', {}), (' · ', {'color': SUB}), ('ColorFilter', {}), (' · ', {'color': SUB}), ('Clip.antiAliasWithSaveLayer', {})]], T_CODE, TEXT, MONO, spacing=1.0)
    source(s, 'Illustration of the marker. Code condensed from thrash_canvas.dart. Widget list from Flutter’s performance best practices.')

    # ------------------------------------------------------------ 20. Fix 4
    s, t = page('Fix 4: A RepaintBoundary, on its own?')
    code(s, M, SUB_Y + 4, W, 32, ['RepaintBoundary(child: CustomPaint(painter: ThrashGridPainter(ledger)))'])
    a = display(s, M, 156, W, 92, 'Alone at 8×: almost nothing.', T_NUM, TEXT)
    t.click(fx(a))
    r_ = rule(s, M, 264, RIGHT_EDGE, 264)
    h_ = text(s, M, 280, W, 32, 'After the other fixes', T_SMALL, SUB, spacing=1.0)
    trio = [change(s, gx(i * 4), 324, gw(4), lab, a_, b_, T_H1, u) for i, (lab, a_, b_, u) in enumerate((('UI', '4.4', '3.4', 'ms'), ('Raster', '6.6', '6.5', 'ms'), ('Grid repaints', '120', '0', 'a second')))]
    t.click(fx(r_), fx(h_), *[fx(x, delay=150) for pair in trio for x in pair])
    ans = display(s, M, 460, W, 130, ['On Impeller, a RepaintBoundary', 'saves Dart work, not GPU work.'], T_H1, ACC)
    t.click(fx(ans))

    # ------------------------------------------------------------ 21. The result
    s, t = page('Four fixes. From 36 fps to 120.')
    phone_ = tall(s, os.path.join(L, 'poster-thrash-fixed.png'), (0, 0.045, 0, 0.012), 'Canvas Thrash at 8× with all four fixes on')
    END = phone_.left / 9525 - GUT
    BWD = (END - M - 4 * 16) / 5
    base, unit_ = 548, 11.8
    limit_y = base - 8.33 * unit_
    for i, (v, lab) in enumerate((('29.7', 'No fixes'), ('18.6', '+ Simplify'), ('13.7', '+ Batch'), ('6.6', '+ Glow'), ('6.5', '+ Isolate'))):
        x = M + i * (BWD + 16)
        h = float(v) * unit_
        over = float(v) > 8.33
        b = box(s, x, base - h, BWD, h, ACC if over else TEXT, f'{lab}: {v} ms')
        n = display(s, x, (base - h - 48) if over else (limit_y - 48), BWD, 46, v, T_H3, TEXT)
        text(s, x, base + 8, BWD + 12, 28, lab, T_LABEL, SUB, spacing=1.0)
        t.click(fx(b, 'up', dur=500), fx(n))
    rule(s, M, limit_y, END, limit_y, TEXT, 1.5, 'dash')
    text(s, M, 604, END - M, 30, 'UI 3.4 ms from 15.9. Layers 0 from 64. Path points 10,112 from 129,920.', T_LABEL, SUB, spacing=1.0)
    source(s, 'Raster p90 in ms at 8×. The line is 8.3 ms. Frame rates from 5 s system traces: 35.5 and 119.8 fps.')

    # ------------------------------------------------------------ 22. Your own shader
    s, t = page('Your effects can be pre-compiled too.', 'Your own shader')
    code(s, gx(0), CT, gw(7), 470, ['# pubspec.yaml', 'flutter:', '  shaders: [shaders/depth_fill.frag]', '', '// Once, before it is needed', 'final program = await', '    FragmentProgram.fromAsset(path);', 'final shader = program.fragmentShader();', '', '// paint(): uniforms only, one draw', 'canvas.drawPath(depth,', '    Paint()..shader = shader);'])
    RX, RW = gx(7), gw(5)
    rule(s, RX, CT, RIGHT_EDGE, CT, TEXT)
    text(s, RX, CT + 16, RW, 26, 'depth_fill.frag, in the APK', T_LABEL, SUB, spacing=1.0)
    text(s, RX, CT + 46, RW, 70, [[('503 B', {'color': SUB}), (' → ', {'color': SUB}), ('4,008 B', {})]], T_H1, TEXT, HEAD, spacing=1.0, track=-50)
    for i, (a, b, hot) in enumerate((('SPIR-V', 'For Vulkan. Already compiled.', False), ('GLSL ES', 'For Impeller’s OpenGL backend.', False), ('SkSL', 'For Skia. Compiled on the phone, at first use.', True))):
        y = 266 + i * 118
        rule(s, RX, y, RIGHT_EDGE, y)
        text(s, RX, y + 14, RW, 32, a, T_CODE, ACC if hot else TEXT, MONO, spacing=1.0)
        text(s, RX, y + 48, RW, 66, b, T_SMALL, SUB, spacing=1.1)
    source(s, 'Code condensed. This custom shader was not timed on the phone.')

    # ------------------------------------------------------------ 23. DevTools
    s, t = page('DevTools: which thread, then which code.', 'Prove it')
    shot(s, os.path.join(L, 'devtools-frames-8x.png'), 0, CT, 1280, (0, 0.03, 0, 0.75), alt='Flutter DevTools frames chart at 8×: every frame is red, and raster is taller than UI')
    STEP5 = (W + GUT) / 5
    for i, (n, w_) in enumerate((('1', 'Which thread?'), ('2', 'Which event?'), ('3', 'Which code?'), ('4', 'One fix.'), ('5', 'Measure again.'))):
        x = M + i * STEP5
        rule(s, x, 336, x + STEP5 - GUT, 336, TEXT)
        text(s, x, 350, 200, 28, n, T_LABEL, SUB, MONO, spacing=1.0)
        display(s, x, 382, STEP5 - GUT + 8, 100, w_.split(' '), T_H3, ACC if i == 4 else TEXT)
    code(s, M, 524, W, 32, ["Timeline.timeSync('KILN::Thrash::grid', () { ... })"])
    source(s, 'Emulator in debug mode: read the shape, ignore the milliseconds.')

    # ------------------------------------------------------------ 24. Perfetto and the budget
    s, t = page('Systrace, now Perfetto: read the budget.', sub='Target about 4 ms UI, 4 ms raster. Limit 8.3 ms a thread.')
    TX = gx(2)
    TK2 = (RIGHT_EDGE - TX) / 100
    t_ = 0.0
    while t_ <= 100:
        rule(s, TX + t_ * TK2, 160, TX + t_ * TK2, 318)
        t_ += 8.33

    def lanes_(y, name, ui, raster, c):
        a = text(s, M, y, 110, 34, name, T_SMALL, c, MID, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0)
        l1 = text(s, TX - 90, y, 80, 34, 'main', T_LABEL, SUB, MONO, RIGHT, MSO_ANCHOR.MIDDLE, spacing=1.0)
        l2 = text(s, TX - 90, y + 38, 80, 34, 'raster', T_LABEL, SUB, MONO, RIGHT, MSO_ANCHOR.MIDDLE, spacing=1.0)
        g1 = blocks(s, ui, y, 34, SUB, TX, TK2, RIGHT_EDGE, f'{name}: main thread')
        g2 = blocks(s, raster, y + 38, 34, c, TX, TK2, RIGHT_EDGE, f'{name}: raster thread')
        return a, l1, l2, g1, g2
    lanes_(164, 'Broken', trace['broken']['ui'], trace['broken']['raster'], ACC)
    a, l1, l2, g1, g2 = lanes_(244, 'Fixed', trace['fixed']['ui'], trace['fixed']['raster'], TEXT)
    t.click(fx(a), fx(l1), fx(l2), fx(g1, 'left', dur=800), fx(g2, 'left', dur=800))

    def bt_style(i, j, val):
        if j == 0:
            return dict(size=T_SMALL, font=HEAD, color=ACC if i == 1 else TEXT)
        if j == 2:
            return dict(size=T_SMALL, font=HEAD, color=ACC if i < 3 else TEXT)
        if j == 6:
            return dict(size=T_SMALL, font=HEAD)
        return dict(size=T_SMALL, color=TEXT)
    first = TX - M
    rest = (RIGHT_EDGE - TX) / 6
    bt = table(s, M, 326, (first, rest, rest, rest, rest, rest, rest), (30, 40, 40, 40),
               [('', 'UI', 'Raster', 'Encode', 'saveLayer', 'QueueSubmit', 'Frame rate'),
                ('Broken', '13.5 ms', '27.9 ms', '27.1 ms', '64', '2', '35.5 fps'),
                ('Halfway', '2.7 ms', '13.8 ms', '12.9 ms', '64', '2', '70.4 fps'),
                ('All fixes', '2.3 ms', '4.8 ms', '3.7 ms', '0', '1', '119.8 fps')], bt_style, 'Budget from the traces')
    t.click(fx(bt))
    ans = display(s, M, 498, W, 50, 'Waiting on the GPU? No. Running for 24 of its 28 ms.', T_H3, TEXT)
    t.click(fx(ans))
    lesson = display(s, M, 552, W, 50, 'The slowest thread sets the rate.', T_H3, ACC)
    t.click(fx(lesson))
    source(s, '100 ms with atrace, tracing on, p50 at 8×. Halfway is Simplify plus Batch. No GPU render stages on this phone.')

    # ------------------------------------------------------------ 25. Take home
    s, t = page('Take this home.', 'Finish')
    for i, (h_, d) in enumerate((('Demystifying\nthe engine', ['Skia: JIT, in the frame.', 'Impeller: AOT, on Vulkan. It tessellates on the CPU and records command buffers.']),
                                 ('Low-level\nprofiling', ['About 4 ms UI, 4 ms raster.', 'DevTools for the frame, Perfetto for the system. The slowest thread sets the rate.']),
                                 ('Taming custom\npainters', ['Fewer points, fewer draws, no saveLayer you don’t need.', 'Pre-compile your own effects. Prove every fix.']))):
        x, w_ = gx(i * 4), gw(4)
        rule(s, x, CT, x + w_, CT, TEXT)
        display(s, x, CT + 16, w_ + 12, 124, h_.split('\n'), T_H1, TEXT)
        text(s, x, 280, w_, 300, d, T_BODY, SUB, spacing=1.12, gap=10)
    rule(s, M, 590, RIGHT_EDGE, 590)
    text(s, M, 604, W, 28, 'Honest limits: fix order matters. GPU passes here are a model, not my trace. Skia: 188 → 58 ms with every fix.', T_LABEL, SUB, spacing=1.0)

    # ------------------------------------------------------------ 26. Close
    s, t = new(layout=ink)
    set_title(s, 'Impeller made\nperformance predictable.\nIt didn’t make\nexpensive work free.', T_NUM, M, 64, gw(9), 370, PAPER)
    text(s, M, 450, gw(8), 40, 'Thread, event, code, fix, measure.', T_BODY, ASH, spacing=1.0)
    display(s, M, 544, gw(8), 40, 'Collins Munene, Shipht', T_BODY, PAPER)
    text(s, M, 584, gw(8), 28, 'FlutterCon Kenya, Nairobi, 5–6 Nov 2026', T_LABEL, ASH, spacing=1.0)
    box(s, gx(9), 84, gw(3), gw(3), WHITE, 'QR background')
    qr = s.shapes.add_picture(os.path.join(A, 'qr-repo.png'), px(gx(9) + 10), px(94), px(gw(3) - 20), px(gw(3) - 20))
    qr._element.find('.//' + qn('p:cNvPr')).set('descr', f'QR code linking to {REPO}')
    qr.click_action.hyperlink.address = REPO
    text(s, gx(9), 362, gw(3), 72, 'Scan it. Run it on your phone.', T_SMALL, PAPER, MID, spacing=1.14)
    link = text(s, gx(9), 446, gw(3), 92, ['github.com/', 'cm-collins/', 'fluttercon-demo-app'], T_LABEL, ASH, MONO, spacing=1.14)
    link.click_action.hyperlink.address = REPO

    # ------------------------------------------------------------ Backups
    def backup(heading, rows, widths, heights, foot, style, section=None):
        s, t = new(section)
        set_title(s, heading)
        table(s, M, CT, widths, heights, rows, style, heading)
        source(s, foot)

    def storm_style(i, j, val):
        if j == 0:
            return dict(font=HEAD)
        if j == 1:
            return dict(font=HEAD, color=ACC)
        if j == 2:
            return dict(font=HEAD)
        return dict(color=SUB)
    backup('Backup: Shader Storm medians', [('Effects', 'Skia cold', 'Impeller cold', 'Skia repeat', 'Impeller repeat', 'Skia relaunch', 'Impeller relaunch'),
                                            ('48', '687', '127', '18', '45', '58', '66'), ('96', '1,310', '145', '19', '43', '81', '73'), ('144', '1,863', '145', '23', '48', '102', '73')],
           (110, 150, 166, 160, 186, 170, 194), (54, 110, 110, 110), 'Worst frame in ms, median of 3 rounds, 120 Hz, tracing off. Infinix X6873, Flutter 3.47.8 profile builds.', storm_style, 'Backup for Q&A')

    def thrash_style(i, j, val):
        if j == 0:
            return dict(font=HEAD)
        if j == 2:
            return dict(font=HEAD)
        if j == 4:
            return dict(font=HEAD, color=ACC)
        return dict(color=SUB)
    backup('Backup: Canvas Thrash medians at 8×', [('Fixes on', 'Impeller UI', 'Impeller raster', 'Skia UI', 'Skia raster'),
                                                   ('None', '15.9', '29.7', '21.8', '188.4'), ('Simplify', '6.3', '18.6', '23.7', '187.7'), ('Simplify + Batch', '4.9', '13.7', '23.5', '202.3'),
                                                   ('+ Glow', '4.4', '6.6', '3.9', '61.5'), ('+ Isolate', '3.4', '6.5', '3.9', '57.7')],
           (gw(4) + GUT, gw(2) + GUT, gw(2) + GUT, gw(2) + GUT, gw(2)), (54, 86, 86, 86, 86, 86), 'Frame p90 in ms, median of 3 rounds. Skia trace with all fixes: 47 of 53 ms inside 32 line draws.', thrash_style)

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
    embed_fonts(prs)
    out = os.path.join(HERE, 'beyond-skia-dark.pptx' if dark else 'beyond-skia.pptx')
    prs.save(out)
    print(variant, os.path.getsize(out) // 1024, 'KB,', len(prs.slides), 'slides')


if __name__ == '__main__':
    build('light')
    build('dark')
