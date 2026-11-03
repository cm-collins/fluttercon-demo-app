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
M, W, RIGHT_EDGE, TITLE_Y, TITLE_SIZE, FOOT_Y = 72, 1136, 1208, 50, 48, 664
LEFT, RIGHT, CENTER = PP_ALIGN.LEFT, PP_ALIGN.RIGHT, PP_ALIGN.CENTER


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
    return text(slide, x, y, w, h, value, size, color, HEAD, align, spacing=0.98, track=-size * 1.2, name=name)


def box(slide, x, y, w, h, fill=CARD, name=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(x), px(y), px(w), px(h))
    shape.fill.solid()
    paint(shape.fill.fore_color, fill)
    shape.line.fill.background()
    if name:
        shape.name = name
    return shape


def label_box(slide, x, y, w, h, value, fill, color, size=21, font=MID, name=None):
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
            text(s, M, 110, W, 36, sub, 26, SUB, spacing=1.0)
        return s, t

    def source(s, value, w=980):
        """Where the numbers came from: one quiet line, level with the logo."""
        return text(s, M, FOOT_Y, w, 24, value, 16, SUB, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0, name='Source')

    def code(s, x, y, w, h, lines, size=21):
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
        return text(s, x, y, w, h, out, size, TEXT, MONO, spacing=1.22, name='Code')

    def change(s, x, y, w, label, a, b, size=52, unit=None, color=TEXT, lsize=20):
        """A measured change: a quiet label, the old value in grey, the new value in full ink."""
        one = text(s, x, y, w, 26, label, lsize, SUB, spacing=1.0)
        runs = [(a, {'color': SUB}), (' → ', {'color': SUB}), (b, {'color': color})]
        if unit:
            runs.append((' ' + unit, {'color': SUB, 'size': size * 0.5}))
        two = text(s, x, y + lsize + 8, w, size * 1.2, [runs], size, TEXT, HEAD, spacing=1.0, track=-size * 0.9)
        return one, two

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
        for j, w in enumerate(widths):
            tbl.columns[j].width = px(w)
        for i, row_ in enumerate(rows):
            tbl.rows[i].height = px(heights[i])
            for j, val in enumerate(row_):
                cell = tbl.cell(i, j)
                st = dict(size=25, color=TEXT, font=BODY, align=LEFT)
                if i == 0:
                    st.update(size=19, color=SUB, font=BODY)
                if style:
                    st.update(style(i, j, val) or {})
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                cell.margin_left, cell.margin_right = 0, px(16)
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
    set_title(s, 'Beyond\nSkia', 112, 72, 132, 640, 240, INK)
    text(s, 72, 400, 610, 90, 'GPU scheduling and profiling with Impeller on Android 10+', 28, GREY, spacing=1.14)
    photo = s.shapes.add_picture(os.path.join(L, 'speaker.jpg'), px(868), px(96), px(340), px(400))
    photo._element.find('.//' + qn('p:cNvPr')).set('descr', 'Collins Munene')
    geom = photo._element.find('.//' + qn('a:prstGeom'))
    geom.set('prst', 'round2SameRect')
    av = geom.find(qn('a:avLst'))
    for key, val in (('adj1', 50000), ('adj2', 0)):
        gd = etree.SubElement(av, qn('a:gd'))
        gd.set('name', key)
        gd.set('fmla', f'val {val}')
    display(s, 868, 512, 340, 40, 'Collins Munene', 30, PAPER)
    text(s, 868, 552, 360, 30, 'DevOps and Software Engineer, Shipht', 19, ASH, spacing=1.0)

    # ------------------------------------------------------------ 2. The map
    s, t = new()
    set_title(s, 'Impeller tamed\none kind of jank.', 104, M, 96, W, 230)
    rule(s, M, 400, RIGHT_EDGE, 400, TEXT, 1)
    text(s, M, 424, 540, 30, 'Tamed', 24, SUB, spacing=1.0)
    display(s, M, 460, 540, 66, 'Compilation jank', 54, SUB)
    text(s, 660, 424, 540, 30, 'Still yours to fix', 24, SUB, spacing=1.0)
    display(s, 660, 460, 548, 66, 'Drawing cost', 54, ACC)

    # ------------------------------------------------------------ 3. The layers
    s, t = page('Dart and the engine are different things.', 'How Flutter draws')
    for i, (name, lang, what, hot) in enumerate((('Framework', 'Dart', 'Widgets, layout, your paint()', False),
                                                 ('Engine', 'C++', 'Runs your Dart. Renders your frames.', True),
                                                 ('Embedder', 'Java, C++', 'Android surface, input, threads', False))):
        y = 170 + i * 150
        rule(s, M, y, RIGHT_EDGE, y, TEXT if i == 0 else HAIR)
        display(s, M, y + 40, 430, 70, name, 60, TEXT if hot else SUB)
        text(s, 520, y + 58, 180, 36, lang, 24, SUB, MONO, spacing=1.0)
        text(s, 700, y + 54, 508, 44, what, 28, TEXT if hot else SUB, spacing=1.0)
    rule(s, M, 620, RIGHT_EDGE, 620)
    text(s, 520, 306, 200, 24, 'dart:ui', 18, SUB, MONO, spacing=1.0)

    # ------------------------------------------------------------ 4. One frame
    s, t = page('One frame, from vsync to pixels.')
    tick = rule(s, M, 200, RIGHT_EDGE, 200, TEXT, 1)
    text(s, M, 162, 200, 28, 'vsync', 22, SUB, MONO, spacing=1.0)
    for i, (thread, verb, how, hot) in enumerate((('main thread', 'Records', 'paint() draws nothing. It writes a DisplayList.', False),
                                                  ('1.raster', 'Prepares', 'Pipelines, triangles, commands. This is CPU time.', True),
                                                  ('GPU', 'Executes', 'Later, on its own schedule. Not a Flutter thread.', False))):
        x = M + i * 389
        w_ = 358
        a = rule(s, x, 200, x, 214, TEXT, 1)
        b = text(s, x, 232, w_, 30, thread, 22, SUB, MONO, spacing=1.0)
        c = display(s, x, 286, w_, 100, verb, 80, ACC if hot else TEXT)
        d = text(s, x, 410, w_, 200, how, 32, SUB, spacing=1.16)
        t.click(fx(a), fx(b), fx(c), fx(d, delay=120))

    # ------------------------------------------------------------ 5. The budget
    s, t = page('Every frame gets 8.3 ms.')
    X0, X1 = 346, RIGHT_EDGE
    K = (X1 - X0) / 33.32
    for i in range(5):
        x = X0 + i * 8.33 * K
        rule(s, x, 158, x, 640)
        if i:
            text(s, x - 70, 128, 66, 24, ('8.3', '16.7', '25', '33.3')[i - 1], 18, SUB, MONO, RIGHT, spacing=1.0)
    text(s, X0, 128, 90, 24, '0 ms', 18, SUB, MONO, spacing=1.0)
    rows = ((172, 'Target', '4 + 4 ms', '120 fps', [(i * 8.33, 4) for i in range(4)], [(i * 8.33 + 4, 4) for i in range(4)], SUB, TEXT, TEXT),
            (332, 'Limit', '8.3 ms each', '120 fps', [(i * 8.33, 8.33) for i in range(4)], [((i + 1) * 8.33, 8.33) for i in range(3)], SUB, TEXT, TEXT),
            (492, 'Measured', '28 ms raster', '36 fps', trace['broken']['ui'], trace['broken']['raster'], SUB, ACC, ACC))
    for y, name, how, rate, ui, raster, c1, c2, c3 in rows:
        a = display(s, M, y + 4, 240, 46, name, 38, c3)
        b = text(s, M, y + 52, 190, 50, [how, rate], 20, SUB, spacing=1.06)
        l1 = text(s, 262, y + 8, 72, 24, 'UI', 16, SUB, MONO, RIGHT, spacing=1.0)
        l2 = text(s, 262, y + 58, 72, 24, 'Raster', 16, SUB, MONO, RIGHT, spacing=1.0)
        g1 = blocks(s, ui, y, 40, c1, X0, K, X1, f'{name}: UI')
        g2 = blocks(s, raster, y + 50, 40, c2, X0, K, X1, f'{name}: raster')
        t.click(fx(a), fx(b), fx(l1), fx(l2), fx(g1, 'left', dur=600), fx(g2, 'left', dur=600, delay=150))
    source(s, 'Top rows drawn to scale. Bottom row: real frames from a system trace on the phone.')

    # ------------------------------------------------------------ 6 and 9. The engine, before and now
    def engine(title, section, left, rows):
        s, t = page(title, section)
        text(s, M, 138, 260, 28, 'When Flutter is built', 21, SUB, spacing=1.0)
        text(s, 392, 138, 400, 28, 'When the app runs', 21, SUB, spacing=1.0)
        rule(s, 360, 138, 360, 640)
        marks = {}
        for i, (thread, cells) in enumerate(rows):
            y = 176 + i * 92
            rule(s, 392, y, RIGHT_EDGE, y, TEXT if i == 0 else HAIR)
            text(s, 392, y, 150, 92, thread, 20, SUB, MONO, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0)
            if isinstance(cells, str):
                text(s, 552, y, 656, 92, cells, 24, TEXT, anchor=MSO_ANCHOR.MIDDLE, spacing=1.08)
            else:
                for j, cell in enumerate(cells):
                    if not cell:
                        continue
                    hot = cell.startswith('!')
                    word = cell.lstrip('!')
                    marks[word] = text(s, 552 + j * 165, y, 155, 92, word, 24, ACC if hot else TEXT, MID if hot else BODY, anchor=MSO_ANCHOR.MIDDLE, spacing=1.04)
        rule(s, 392, 176 + len(rows) * 92, RIGHT_EDGE, 176 + len(rows) * 92)
        return s, t, marks

    s, t, m = engine('Android before: Skia on OpenGL ES.', 'Before: Skia', None, (
        ('platform', 'Android views, input, lifecycle'),
        ('1.ui', ('Animate', 'Build', 'Layout', 'Paint')),
        ('1.raster', ('Replay', '!Write the shader', '!Driver compiles it', 'Draw')),
        ('OpenGL ES', 'The driver hides the work'),
        ('GPU', 'Fills the pixels')))
    display(s, M, 262, 260, 70, 'Nothing.', 56, SUB)
    text(s, M, 340, 260, 120, 'No shader for your screen exists yet.', 25, SUB, spacing=1.14)
    t.click(fx(m['Write the shader']), fx(m['Driver compiles it'], delay=300))
    source(s, 'Android, simplified. iOS used Metal under Skia. Dart ran on 1.ui until Flutter 3.29.')

    # ------------------------------------------------------------ 7. Compilation jank
    s, t = page('Compilation jank.', sub='A shader is a small GPU program. On Android, the driver compiles it for that exact chip.')
    flow = text(s, M, 176, W, 34, [[('new paint + blend + clip', {'color': TEXT}), ('  →  SkSL  →  GLSL  →  driver compile  →  ', {'color': SUB}), ('missed frame', {'color': ACC})]], 21, TEXT, MONO, spacing=1.0)
    t.click(fx(flow))
    num = display(s, M, 246, 520, 170, '1.8 s', 160, ACC, name='One frame')
    cap = text(s, 590, 300, 618, 100, ['118 shaders, compiled inside', 'one frame. About 14.5 ms each.'], 34, TEXT, HEAD, spacing=1.1, track=-30)
    PK = W / 1820
    prog = s.shapes.add_group_shape()
    for i in range(118):
        r = prog.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(M + i * 14.525 * PK), px(446), px(14.6 * PK - 1.6), px(78))
        r.fill.solid()
        paint(r.fill.fore_color, ACC)
        r.line.fill.background()
    prog.name = '118 Skia programs in one frame, drawn to scale'
    bud = box(s, M, 546, max(8.33 * PK, 5.2), 30, TEXT, 'One frame budget, 8.3 ms, to the same scale')
    budl = text(s, M + 18, 546, 700, 30, '8.3 ms: one frame’s budget, same scale', 22, TEXT, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0)
    t.click(fx(num), fx(cap, delay=150), fx(prog, 'left', dur=1100, delay=250), fx(bud, delay=1100), fx(budl, delay=1100))
    source(s, 'Real Skia trace on the Infinix, to scale: 1,714 ms of programs in a 1,820 ms frame. 144 new effects.')

    # ------------------------------------------------------------ 9. The engine now
    s, t, m = engine('Android now: Impeller on Vulkan.', 'Now: Impeller', None, (
        ('main', 'Android and Dart, one thread since 3.29'),
        ('main', ('Animate', 'Build', 'Layout', 'Paint')),
        ('1.raster', ('Replay', 'Bind or build a pipeline', '!Tessellate', 'Record commands')),
        ('Vulkan', 'Explicit commands, on phones that pass the checks'),
        ('GPU', 'Runs the commands, fills the pixels')))
    a = display(s, M, 262, 270, 56, 'impellerc', 42, TEXT)
    b = text(s, M, 322, 270, 90, 'A small, fixed set of shaders, compiled for:', 24, SUB, spacing=1.14)
    c = text(s, M, 412, 270, 120, ['Vulkan: SPIR-V', 'Metal: iOS, macOS', 'OpenGL ES: GLSL'], 22, TEXT, MONO, spacing=1.3)
    d = text(s, M, 540, 270, 60, 'Inside the engine binary', 24, SUB, spacing=1.14)
    t.click(fx(a), fx(b, delay=120), fx(c, delay=240), fx(d, delay=360))
    t.click(fx(m['Tessellate']))
    source(s, 'Android on Vulkan, simplified. iOS and macOS run Impeller on Metal.')

    # ------------------------------------------------------------ 10. Late and early
    s, t = page('Skia compiles late. Impeller compiles early.')
    stages = ('Engine build', 'App build', 'App start', 'First use', 'Every frame')
    SX, SW = 272, 187.2
    for i, st in enumerate(stages):
        text(s, SX + i * SW, 138, SW - 12, 26, st, 20, SUB, spacing=1.0)
    rule(s, M, 174, RIGHT_EDGE, 174, TEXT)
    rule(s, M, 390, RIGHT_EDGE, 390)
    display(s, M, 202, 190, 50, 'Skia', 42, TEXT)
    text(s, M, 256, 190, 30, 'JIT', 22, SUB, MONO, spacing=1.0)
    display(s, M, 418, 190, 50, 'Impeller', 42, TEXT)
    text(s, M, 472, 190, 30, 'AOT', 22, SUB, MONO, spacing=1.0)
    CH = 128
    skia = (text(s, SX, 202, SW - 16, CH, 'Nothing yet', 22, SUB),
            text(s, SX + SW, 202, SW - 16, CH, 'Your .frag stays as SkSL text', 22, SUB, spacing=1.12),
            text(s, SX + 2 * SW, 202, SW - 16, CH, 'Warm-up, if you wrote one', 22, SUB, spacing=1.12),
            label_box(s, SX + 3 * SW, 196, SW - 12, CH, 'Write and compile, in the frame\n14.5 ms each', ACC, WHITE if not dark else INK, 21),
            text(s, SX + 4 * SW, 202, SW - 16, CH, 'Bind the cached program', 22, SUB, spacing=1.12))
    t.click(*[fx(x, delay=i * 70) for i, x in enumerate(skia)])
    imp = (label_box(s, SX, 412, SW - 12, CH, 'impellerc: engine shaders', TEXT, BG, 21),
           label_box(s, SX + SW, 412, SW - 12, CH, 'impellerc: your .frag', TEXT, BG, 21),
           text(s, SX + 2 * SW, 418, SW - 16, CH, 'Most pipelines are built', 22, TEXT, spacing=1.12),
           text(s, SX + 3 * SW, 418, SW - 16, CH, 'A missing pipeline: 2.2 ms each, in the frame', 22, TEXT, spacing=1.12),
           text(s, SX + 4 * SW, 418, SW - 16, CH, 'Bind a built pipeline', 22, TEXT, spacing=1.12))
    t.click(*[fx(x, delay=i * 70) for i, x in enumerate(imp)])
    source(s, 'A pipeline is shader code plus fixed GPU state. On Vulkan, the driver finishes the compile when it is built. Infinix traces.')

    # ------------------------------------------------------------ 10. Rollout
    s, t = page('Impeller arrived one platform at a time.')
    for i, (name, ver, when, extra, hot) in enumerate((('iOS', 'Default in 3.10', 'May 2023', 'On Metal. Skia removed in 3.29', False),
                                                       ('Android', 'Default in 3.27', 'December 2024', 'Android 10+ (API 29+), on Vulkan where it can', True),
                                                       ('Desktop', 'Default in 3.47', '2026', 'macOS, Windows and Linux', False))):
        y = 150 + i * 158
        l = rule(s, M, y, RIGHT_EDGE, y, TEXT if i == 0 else HAIR)
        a = display(s, M, y + 44, 320, 72, name, 60, ACC if hot else TEXT)
        b_ = text(s, 420, y + 42, 500, 40, ver, 30, TEXT, MID, spacing=1.0)
        c = text(s, 420, y + 86, 560, 30, extra, 22, SUB, spacing=1.0)
        d = text(s, 900, y + 42, 308, 40, when, 30, SUB, align=RIGHT, spacing=1.0)
        t.click(fx(l), fx(a), fx(b_), fx(c), fx(d))
    source(s, 'Flutter docs and release notes. Web still renders with Skia.')

    # ------------------------------------------------------------ 11. Which backend
    s, t = page('On Android, Vulkan isn’t guaranteed.')
    rule(s, M, 138, RIGHT_EDGE, 138, TEXT)
    for i, (when, what, c, hot) in enumerate((('Android 9 or older', 'Skia on OpenGL ES', SUB, False),
                                              ('Android 10+, a device check fails', 'Impeller on OpenGL ES', ACC, True),
                                              ('Android 10+, every check passes', 'Impeller on Vulkan', TEXT, False))):
        y = 138 + i * 96
        text(s, M, y, 540, 96, when, 30, SUB if i == 0 else TEXT, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0)
        text(s, 640, y, 568, 96, what, 46, c, HEAD, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0, track=-50)
        rule(s, M, y + 96, RIGHT_EDGE, y + 96)
    checks = text(s, M, 452, W, 34, 'The checks, in this engine', 22, SUB, spacing=1.0)
    what_ = text(s, M, 488, W, 80, ['Emulator. Huawei. MediaTek with a vendor API below 32. Adreno 650 or older.', 'Some Exynos chips. No working Vulkan 1.1 with the extensions Impeller needs.'], 25, TEXT, spacing=1.2)
    t.click(fx(checks), fx(what_))
    proof = text(s, M, 584, W, 36, 'adb logcat | grep "Impeller rendering backend"', 24, ACC, MONO, spacing=1.0)
    t.click(fx(proof))
    source(s, 'Flutter 3.47.8: flutter_main.cc, android_context_dynamic_impeller.cc, driver_info_vk.cc. My Impeller numbers: Vulkan, per the log.')

    # ------------------------------------------------------------ 12. The trade
    s, t = page('A trade, not a free upgrade.')

    def trade_style(i, j, val):
        if i == 0:
            return dict(size=22, font=MID, color=TEXT if j == 2 else SUB)
        if j == 0:
            return dict(size=30, font=HEAD)
        if j == 1:
            return dict(size=25, color=SUB)
        if i in (2, 3):
            return dict(size=27, font=MID, color=ACC)
        return dict(size=27, font=MID)
    table(s, M, 142, (246, 430, 460), (54, 88, 88, 88, 88, 88),
          [('On Android', 'Before', 'Now'),
           ('Shaders', 'Written and compiled in the frame', 'Pre-compiled with the engine'),
           ('Cache', 'Automatic raster cache', 'No raster cache'),
           ('Paths', 'GPU and mask techniques', 'Tessellated on the CPU'),
           ('GPU API', 'OpenGL ES, the driver decides', 'Vulkan where possible, explicit'),
           ('Dart', 'Its own 1.ui thread', 'Main thread, since 3.29')], trade_style, 'Android before and now')

    # ------------------------------------------------------------ 13. Scoreboard
    s, t = page('Same app. Same phone. Two renderers.', 'The proof')
    CX = (262, 590)
    text(s, CX[0], 156, 300, 30, 'First reveal', 24, SUB, spacing=1.0)
    text(s, CX[1], 156, 280, 30, 'Second time', 24, SUB, spacing=1.0)

    def score(x, y, value, color=TEXT):
        return text(s, x, y, 330, 130, [[(value, {'color': color}), (' ms', {'size': 30, 'color': SUB, 'track': 0})]], 92, TEXT, HEAD, spacing=1.0, track=-110)
    rule(s, M, 198, 880, 198, TEXT)
    rule(s, M, 408, 880, 408)
    rule(s, M, 618, 880, 618)
    display(s, M, 268, 180, 60, 'Skia', 44, SUB)
    display(s, M, 478, 180, 60, 'Impeller', 40, TEXT)
    a = score(CX[0], 248, '1,863', ACC)
    t.click(fx(a))
    b = score(CX[1], 248, '23', SUB)
    t.click(fx(b))
    c = score(CX[0], 458, '145')
    d = score(CX[1], 458, '48')
    t.click(fx(c), fx(d, delay=250))
    shot(s, os.path.join(L, 'poster-impeller-cold.png'), 930, 40, 278, (0, 0.035, 0, 0.012), radius=14, alt='Shader Storm in the demo app, on the phone, before a reveal')
    source(s, 'Worst frame, median of 3 rounds. Infinix X6873, Mali-G615, 120 Hz. Skia on OpenGL ES, Impeller on Vulkan.', 840)

    # ------------------------------------------------------------ 14. The chart
    s, t = page('Skia’s freeze grows. Impeller’s barely does.')
    data = CategoryChartData()
    data.categories = ['48', '96', '144']
    data.add_series('Skia', (687, 1310, 1863))
    data.add_series('Impeller', (127, 145, 145))
    frame = s.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, px(M - 10), px(140), px(800), px(500), data)
    frame.name = 'Freeze time by number of new effects'
    frame._element.find('.//' + qn('p:cNvPr')).set('descr', 'At 48, 96 and 144 new effects, Skia freezes for 687, 1,310 and 1,863 ms; Impeller for 127, 145 and 145 ms.')
    chart = frame.chart
    chart.has_legend = chart.has_title = False
    chart.font.name = BODY
    val = chart.value_axis
    val.visible = val.has_major_gridlines = False
    val.minimum_scale, val.maximum_scale = 0, 2200
    cat = chart.category_axis
    cat.has_major_gridlines = False
    cat.major_tick_mark = 2
    cat.tick_labels.font.size = fs(22)
    paint(cat.tick_labels.font.color, SUB)
    paint(cat.format.line.color, HAIR)
    for series, color in zip(chart.plots[0].series, (ACC, TEXT)):
        series.smooth = False
        paint(series.format.line.color, color)
        series.format.line.width = fs(4)
        series.marker.style = XL_MARKER_STYLE.CIRCLE
        series.marker.size = 10
        series.marker.format.fill.solid()
        paint(series.marker.format.fill.fore_color, color)
        series.marker.format.line.fill.background()
    w1 = text(s, 470, 168, 270, 34, 'Skia 1,863 ms', 26, ACC, MID, RIGHT, spacing=1.0)
    w2 = text(s, 470, 516, 270, 34, 'Impeller 145 ms', 26, TEXT, MID, RIGHT, spacing=1.0)
    t.click(fx(frame, 'left', dur=1200), fx(w1, delay=900), fx(w2, delay=900))
    display(s, 900, 196, 308, 170, '13×', 150, TEXT)
    text(s, 900, 370, 308, 110, 'shorter, at 144 new effects on screen', 28, SUB, spacing=1.14)
    source(s, 'Worst frame after a cold reveal, median of 3 rounds. New effects on the axis.')

    # ------------------------------------------------------------ 15. The cost moved
    s, t = page('The cost shrank and moved. It didn’t vanish.')
    TK = W / 1714
    a1 = display(s, M, 150, 700, 44, 'Skia: 118 shaders', 34, TEXT)
    a2 = display(s, 800, 150, 408, 44, '1,714 ms', 34, ACC, RIGHT)
    g = s.shapes.add_group_shape()
    for i in range(118):
        r = g.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(M + i * 14.53 * TK), px(200), px(14.53 * TK - 1.6), px(70))
        r.fill.solid()
        paint(r.fill.fore_color, ACC)
        r.line.fill.background()
    g.name = '118 Skia programs, to scale'
    b1 = display(s, M, 300, 700, 44, 'Impeller: 40 pipelines', 34, TEXT)
    b2 = display(s, 800, 300, 408, 44, '87 ms', 34, TEXT, RIGHT)
    b3 = box(s, M, 350, 87 * TK, 70, TEXT, '40 Impeller pipelines, to scale')
    t.click(fx(a1), fx(a2), fx(g, 'left', dur=900), fx(b1, delay=500), fx(b2, delay=500), fx(b3, 'left', dur=400, delay=500))
    l = rule(s, M, 470, RIGHT_EDGE, 470)
    c1 = text(s, M, 490, 460, 30, 'Same session, second time', 24, SUB, spacing=1.0)
    c2 = display(s, M, 530, 640, 70, 'Skia 23 ms. Impeller 48 ms.', 50, TEXT)
    c3 = text(s, 760, 544, 448, 60, 'Predictable. Not always faster.', 30, SUB, align=RIGHT, spacing=1.0)
    t.click(fx(l), fx(c1), fx(c2), fx(c3, delay=300))
    source(s, 'System traces of one cold reveal, tracing on, drawn to scale. Second time: median of 3 rounds, tracing off.')

    # ------------------------------------------------------------ 16. Tessellation
    s, t = page('Tessellation: how a path becomes triangles.', 'Inside a frame')
    WX = lambda v: M + 22 + (v - 10) * (W - 44) / 450
    WY = lambda v: 245 + (v - 30) * 1.55
    steps = (('Path', 'What paint() asks for'), ('Points', 'Curves flatten'), ('Vertices', 'Two per point'), ('Triangles', 'v − 2 of them'))
    pts, edges = strip_edges(14)
    head_ = []
    for i, (h_, d) in enumerate(steps):
        x = M + i * 284
        h1 = display(s, x, 136, 270, 40, h_, 32, TEXT)
        h2 = text(s, x, 178, 270, 28, d, 22, SUB, spacing=1.0)
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
    bottom = text(s, M, 576, W, 54, [[('The demo at 8×: 16 lines × 8,000 points × 2 = ', {'color': SUB}), ('256,000+', {'color': ACC}), (' vertices.', {'color': SUB})]], 34, TEXT, HEAD, spacing=1.0, track=-30)
    t.click(fx(bottom))
    source(s, 'Illustration. On the CPU, every frame. Vertex count worked out from stroke_path_geometry.cc, not measured.')

    # ------------------------------------------------------------ 17. Command buffers
    s, t = page('The CPU records. The GPU executes.', sub='That handoff is GPU scheduling.')
    code(s, M, 190, 400, 400, ['begin render pass', '  bind pipeline', '  bind vertex buffer', '  bind uniforms', '  draw', '  ...', 'end render pass', 'submit to queue, fence'], 25)
    LX, BX = 500, 650
    BW = RIGHT_EDGE - BX
    lanes = (('1.raster', 190), ('queue', 310), ('GPU', 430))
    for name, y in lanes:
        text(s, LX, y, 140, 76, name, 21, SUB, MONO, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0)
        rule(s, LX, y + 94, RIGHT_EDGE, y + 94)
    rule(s, LX, 166, RIGHT_EDGE, 166, TEXT)
    fxs = []
    frames = ((0, TEXT), (260, SUB))
    for i, (off, c) in enumerate(frames):
        d0 = i * 900
        r1 = box(s, BX + off, 190, 210, 76, c, f'Frame {i + 1}: recorded')
        r2 = box(s, BX + off + 212, 310, 12, 76, c, f'Frame {i + 1}: submitted')
        r3 = box(s, BX + off + 230, 430, 200 if i == 0 else BW - off - 230, 76, c, f'Frame {i + 1}: executed')
        fxs += [fx(r1, 'left', dur=500, delay=d0), fx(r2, delay=d0 + 450), fx(r3, 'left', dur=500, delay=d0 + 550)]
    fence = rule(s, BX + 430, 430, BX + 430, 544, TEXT, 1, 'dash')
    fword = text(s, BX + 440, 520, 120, 26, 'fence', 20, TEXT, MONO, spacing=1.0)
    t.click(*fxs, fx(fence, delay=1500), fx(fword, delay=1500))
    source(s, 'Illustration of the order of work, not a measured trace.')

    # ------------------------------------------------------------ 18. The layer
    s, t = page('Why a layer costs more than a draw.')
    FG = WHITE if not dark else INK
    display(s, M, 138, 600, 44, 'One render pass', 34, TEXT)
    x = M
    for w_, words, hot in ((110, 'Clear', False), (746, 'All draws, in fast tile memory', False), (130, 'Resolve', False), (150, 'Store once', True)):
        label_box(s, x, 190, w_ - 3, 84, words, ACC if hot else CARD, FG if hot else TEXT, 22)
        x += w_
    head2 = display(s, M, 314, 600, 44, 'With one saveLayer', 34, TEXT)
    second = []
    x = M
    for w_, words, hot in ((150, 'Draws so far', False), (116, 'Store', True), (316, 'Offscreen pass: draw and blur', False), (116, 'Store', True), (116, 'Load', True), (176, 'Composite', False), (146, 'Store', True)):
        second.append(label_box(s, x, 366, w_ - 3, 84, words, ACC if hot else CARD, FG if hot else TEXT, 22))
        x += w_
    t.click(fx(head2), *[fx(b_, 'left', dur=250, delay=i * 130) for i, b_ in enumerate(second)])
    text(s, M, 490, W, 40, 'Measured: 64 saveLayer a frame. Removing them cut raster from 13.7 to 6.6 ms.', 28, TEXT, MID, spacing=1.0)
    text(s, M, 536, W, 40, 'The GPU side is the model. This phone’s driver doesn’t expose it.', 26, SUB, spacing=1.0)
    source(s, 'Illustration, not to scale. The accent marks a trip to main memory.')

    # ------------------------------------------------------------ 19. What it didn't fix
    s, t = new('What Impeller didn’t fix', ink)
    set_title(s, 'What Impeller\ndidn’t fix.', 104, M, 170, 780, 230, PAPER)
    text(s, M, 410, 720, 90, 'If compiling shaders isn’t the problem, what is?', 32, ASH, spacing=1.16)
    shot(s, os.path.join(L, 'poster-thrash-broken.png'), 880, 0, 300, (0, 0.045, 0, 0.02), alt='Canvas Thrash in the demo app at 8×: both lanes red')

    # ------------------------------------------------------------ 20. Drawing cost
    s, t = page('Nothing is compiling. This is pure drawing cost.')
    for i, (val, name, frm, hot) in enumerate((('129,920', 'path points', 'from 2,240 at 1×', True), ('624', 'draw calls', 'from 78 at 1×', False), ('64', 'offscreen layers', 'from 8 at 1×', False))):
        x = (M, 500, 860)[i]
        w_ = (400, 330, 348)[i]
        rule(s, x, 150, x + w_, 150, TEXT)
        display(s, x, 168, w_, 110, val, 92, ACC if hot else TEXT)
        text(s, x, 282, w_, 36, name, 30, TEXT, MID, spacing=1.0)
        text(s, x, 322, w_, 30, frm, 22, SUB, spacing=1.0)
    BK = 900 / 32
    for i, (name, v, c) in enumerate((('UI', 15.9, SUB), ('Raster', 29.7, ACC))):
        y = 420 + i * 84
        text(s, M, y, 100, 66, name, 22, SUB, MONO, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0)
        box(s, 176, y, v * BK, 66, c, f'{name}: {v} ms')
        display(s, 176 + v * BK + 12, y + 8, 180, 50, f'{v} ms', 36, TEXT)
    bx = 176 + 8.33 * BK
    rule(s, bx, 400, bx, 588, TEXT, 1.5, 'dash')
    text(s, bx + 8, 590, 240, 26, '8.3 ms budget', 20, TEXT, spacing=1.0)
    source(s, 'My demo’s dial, not a Flutter limit. Each level adds 2 lines and 1,000 points a line, so 8× is 16 lines of 8,000. p90, 3 rounds.')

    # ------------------------------------------------------------ 21. The vote
    s, t = page('Which fix helps most, on its own?')
    BX2, BK2 = 470, 620 / 29.7
    rule(s, M, 150, RIGHT_EDGE, 150, TEXT)
    fxs = []
    for i, (name, why, v) in enumerate((('Simplify paths', 'Fewer points', 18.6), ('Batch draws', 'Fewer draw calls', 28.6), ('Glow without layers', 'No offscreen passes', 21.2), ('Isolate repaints', 'Less Dart re-recording', 25.2))):
        y = 170 + i * 112
        display(s, M, y + 4, 380, 44, name, 34, TEXT)
        text(s, M, y + 48, 380, 28, why, 22, SUB, spacing=1.0)
        hot = i == 0
        b = box(s, BX2, y + 6, v * BK2, 66, ACC if hot else CARD, f'{name}: {v} ms')
        n = display(s, BX2 + 29.7 * BK2 + 18, y + 14, 100, 50, str(v), 38, ACC if hot else TEXT)
        fxs += [fx(b, 'left', dur=700, delay=i * 120), fx(n, delay=500 + i * 120)]
    t.click(*fxs)
    base = BX2 + 29.7 * BK2
    rule(s, base, 150, base, 620, TEXT, 1.5)
    text(s, base - 240, 124, 234, 24, 'No fixes: 29.7 ms', 19, TEXT, align=RIGHT, spacing=1.0)
    source(s, 'Raster p90 at 8×, each fix alone, median of 3 rounds. Batch and Isolate are within run-to-run noise. None reaches 8.3 ms alone.')

    # ------------------------------------------------------------ 22. Fix 1
    s, t = page('Fix 1: Simplify paths.')
    state = 7

    def noise(n, w, x, y, amp):
        nonlocal state
        out = []
        for k in range(n):
            state = (state * 1103515245 + 12345) & 0x7fffffff
            jitter = (state % 1000) / 1000 - 0.5
            out.append((x + w * k / (n - 1), y + 16 * math.sin(k / n * 9) + 12 * math.sin(k / n * 31) + amp * jitter))
        return out
    text(s, M, 134, 530, 28, '8,000 points a line: the demo at 8×', 22, ACC, MID, spacing=1.0)
    polyline(s, noise(320, 530, M, 214, 32), ACC, 1, 'A line with too many points')
    a_ = text(s, 678, 134, 530, 28, 'At most 2 per pixel column', 22, TEXT, MID, spacing=1.0)
    b_ = polyline(s, noise(46, 530, 678, 214, 14), TEXT, 2.5, 'The same line, simplified')
    rule(s, M, 290, RIGHT_EDGE, 290)
    code(s, M, 312, 620, 340, ['!!A new path, every frame', 'final path = Path();', 'for (var k = 0; k < n; k++) // n = 8,000', '  path.lineTo(x(k), y(k));', '', '++Simplify once, then only move it', 'final xy = decimate(series, plot.width);', 'canvas', '  ..translate(shift, 0)', '  ..drawPath(cached, stroke);'], 22)
    ch = [change(s, 780, 312 + i * 104, 428, lab, a, b, 44, u) for i, (lab, a, b, u) in enumerate((('Path points', '129,920', '12,032', None), ('Raster p90', '29.7', '18.6', 'ms'), ('UI p90', '15.9', '6.3', 'ms')))]
    t.click(fx(a_), fx(b_, 'left', dur=900), *[fx(x, delay=500) for pair in ch for x in pair])

    # ------------------------------------------------------------ 23. Fixes 2 and 3
    s, t = page('Fixes 2 and 3: fewer draws, no layers.')
    rule(s, 640, 138, 640, 636)
    for x, name, ch_, raster_, code_, hot in ((M, 'Batch draws', ('Draw calls', '640', '161'), ('18.6', '13.7'),
                                               ['!!Before: 480 draws', 'canvas.drawPath(segment, paint);', '++After: one draw', 'canvas.drawVertices(', '    vertices, BlendMode.dst, p);'], False),
                                              (672, 'Glow without layers', ('saveLayer a frame', '64', '0'), ('13.7', '6.6'),
                                               ['!!Before: per dot, a pass and a blur', 'canvas.saveLayer(bounds, blurPaint);', '++After: same glow, in the main pass', 'canvas.drawCircle(c, r, radialPaint);'], True)):
        display(s, x, 138, 530, 48, name, 38, ACC if hot else TEXT)
        change(s, x, 200, 530, *ch_, 48)
        change(s, x, 296, 530, 'Raster p90', *raster_, 48, 'ms')
        code(s, x, 416, 536, 200, code_, 21)
    source(s, 'Code condensed from thrash_canvas.dart. Applied in order, at 8×, median of 3 rounds. 640 because Fix 1 draws each line twice.')

    # ------------------------------------------------------------ 24. Fix 4
    s, t = page('Fix 4: A RepaintBoundary, on its own?')
    code(s, M, 124, W, 40, ['RepaintBoundary(child: CustomPaint(painter: ThrashGridPainter(ledger)))'], 22)
    a = display(s, M, 196, W, 90, 'Alone at 8×: almost nothing.', 74, TEXT)
    t.click(fx(a))
    r_ = rule(s, M, 312, RIGHT_EDGE, 312)
    h_ = text(s, M, 330, 500, 30, 'After the other fixes', 24, SUB, spacing=1.0)
    trio = [change(s, M + i * 389, 376, 360, lab, a_, b_, 48, u) for i, (lab, a_, b_, u) in enumerate((('UI', '4.4', '3.4', 'ms'), ('Raster', '6.6', '6.5', 'ms'), ('Grid repaints', '120', '0', 'a second')))]
    t.click(fx(r_), fx(h_), *[fx(x, delay=150) for pair in trio for x in pair])
    ans = display(s, M, 500, W, 130, ['On Impeller, a RepaintBoundary', 'saves Dart work, not GPU work.'], 56, ACC)
    t.click(fx(ans))

    # ------------------------------------------------------------ 25. The result
    s, t = page('Four fixes. From 36 fps to 120.')
    base, unit_ = 544, 12.0
    limit_y = base - 8.33 * unit_
    for i, (v, lab) in enumerate((('29.7', 'No fixes'), ('18.6', '+ Simplify'), ('13.7', '+ Batch'), ('6.6', '+ Glow'), ('6.5', '+ Isolate'))):
        x = M + i * 164
        h = float(v) * unit_
        over = float(v) > 8.33
        b = box(s, x, base - h, 134, h, ACC if over else TEXT, f'{lab}: {v} ms')
        n = display(s, x, (base - h - 50) if over else (limit_y - 50), 134, 46, v, 38, TEXT)
        text(s, x, base + 12, 150, 28, lab, 20, SUB, spacing=1.0)
        t.click(fx(b, 'up', dur=500), fx(n))
    rule(s, M, limit_y, 880, limit_y, TEXT, 1.5, 'dash')
    text(s, M, 610, 810, 30, 'UI 3.4 ms from 15.9. Layers 0 from 64. Path points 10,112 from 129,920.', 21, SUB, spacing=1.0)
    shot(s, os.path.join(L, 'poster-thrash-fixed.png'), 930, 40, 278, (0, 0.045, 0, 0.012), radius=14, alt='Canvas Thrash at 8× with all four fixes on')
    source(s, 'Raster p90 in ms at 8×. The line is 8.3 ms. Frame rates from 5 s system traces: 35.5 and 119.8 fps.', 840)

    # ------------------------------------------------------------ 26. Your own shader
    s, t = page('Your effects can be pre-compiled too.', 'Your own shader')
    code(s, M, 150, 640, 470, ['# pubspec.yaml', 'flutter:', '  shaders: [shaders/depth_fill.frag]', '', '// Once, before it is needed', 'final program = await', '    FragmentProgram.fromAsset(path);', 'final shader = program.fragmentShader();', '', '// paint(): uniforms only, one draw', 'canvas.drawPath(depth,', '    Paint()..shader = shader);'], 23)
    RX = 760
    rule(s, RX, 150, RIGHT_EDGE, 150, TEXT)
    text(s, RX, 168, 448, 30, 'depth_fill.frag, in the APK', 22, SUB, spacing=1.0)
    text(s, RX, 204, 448, 80, [[('503 B', {'color': SUB}), (' → ', {'color': SUB}), ('4,008 B', {})]], 58, TEXT, HEAD, spacing=1.0, track=-60)
    for i, (a, b, hot) in enumerate((('SPIR-V', 'For Vulkan. Already compiled.', False), ('GLSL ES', 'For Impeller’s OpenGL backend.', False), ('SkSL', 'For Skia. Compiled on the phone, at first use.', True))):
        y = 306 + i * 106
        rule(s, RX, y, RIGHT_EDGE, y)
        text(s, RX, y + 14, 448, 34, a, 25, ACC if hot else TEXT, MONO, spacing=1.0)
        text(s, RX, y + 50, 448, 50, b, 23, SUB, spacing=1.08)
    source(s, 'Code condensed. This custom shader was not timed on the phone.')

    # ------------------------------------------------------------ 27. DevTools
    s, t = page('DevTools: which thread, then which code.', 'Prove it')
    shot(s, os.path.join(L, 'devtools-frames-8x.png'), 0, 128, 1280, (0, 0.03, 0, 0.75), alt='Flutter DevTools frames chart at 8×: every frame is red, and raster is taller than UI')
    for i, (n, w_) in enumerate((('1', 'Which thread?'), ('2', 'Which event?'), ('3', 'Which code?'), ('4', 'One fix.'), ('5', 'Measure again.'))):
        x = M + i * 230
        rule(s, x, 336, x + 206, 336, TEXT)
        text(s, x, 350, 200, 28, n, 22, SUB, MONO, spacing=1.0)
        display(s, x, 386, 210, 100, w_.split(' '), 42, ACC if i == 4 else TEXT)
    code(s, M, 548, W, 40, ["Timeline.timeSync('KILN::Thrash::grid', () { ... })"], 24)
    source(s, 'Emulator in debug mode: read the shape, ignore the milliseconds.')

    # ------------------------------------------------------------ 28. Perfetto
    s, t = page('Systrace, now Perfetto: 100 ms on the phone.')
    TX, TW = 240, RIGHT_EDGE - 240
    TK2 = TW / 100
    t_ = 0.0
    while t_ <= 100:
        rule(s, TX + t_ * TK2, 128, TX + t_ * TK2, 306)
        t_ += 8.33

    def lanes_(y, name, ui, raster, c):
        a = text(s, M, y, 130, 36, name, 24, c, MID, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0)
        l1 = text(s, 172, y, 62, 36, 'main', 15, SUB, MONO, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0)
        l2 = text(s, 172, y + 40, 62, 36, 'raster', 15, SUB, MONO, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0)
        g1 = blocks(s, ui, y, 36, SUB, TX, TK2, RIGHT_EDGE, f'{name}: main thread')
        g2 = blocks(s, raster, y + 40, 36, c, TX, TK2, RIGHT_EDGE, f'{name}: raster thread')
        return a, l1, l2, g1, g2
    lanes_(134, 'Broken', trace['broken']['ui'], trace['broken']['raster'], ACC)
    a, l1, l2, g1, g2 = lanes_(224, 'Fixed', trace['fixed']['ui'], trace['fixed']['raster'], TEXT)
    t.click(fx(a), fx(l1), fx(l2), fx(g1, 'left', dur=800), fx(g2, 'left', dur=800))
    rule(s, M, 326, RIGHT_EDGE, 326, TEXT)
    effects = []
    for i, (lab, a_, b_) in enumerate((('Raster frame', '27.9', '4.8 ms'), ('SurfaceFrame::Encode', '27.1', '3.7 ms'), ('saveLayer a frame', '64', '0'), ('QueueSubmit a frame', '2', '1'), ('Frames in 5 s', '179', '604'))):
        x = M + i * 230
        one, two = change(s, x, 342, 222, lab, a_, b_, 32, lsize=16)
        effects += [fx(one, delay=i * 90), fx(two, delay=i * 90)]
    t.click(*effects)
    rule(s, M, 432, RIGHT_EDGE, 432)
    text(s, M, 456, W, 44, 'Is the raster thread waiting on the GPU?', 34, SUB, HEAD, spacing=1.0, track=-30)
    ans = display(s, M, 510, W, 110, 'No. It’s running for 24 of its 28 ms.', 62, TEXT)
    t.click(fx(ans))
    source(s, 'Recorded with atrace. Faint lines are 120 Hz deadlines. This phone’s driver exposes no GPU render stages.')

    # ------------------------------------------------------------ 29. The budget, read
    s, t = page('Read the budget from the trace.', sub='Target about 4 ms UI, 4 ms raster. Limit 8.3 ms a thread.')

    def bt_style(i, j, val):
        if i == 0:
            return None
        if j == 0:
            return dict(size=30, font=HEAD, color=ACC if i == 1 else TEXT)
        if j == 2:
            return dict(size=30, font=HEAD, color=ACC if i < 3 else TEXT)
        if j == 3:
            return dict(size=22, color=SUB)
        if j == 4:
            return dict(size=30, font=HEAD)
        return dict(size=28, font=BODY)
    table(s, M, 156, (262, 176, 210, 300, 188), (40, 64, 64, 64),
          [('', 'UI p50', 'Raster p50', '1000 ÷ raster', 'Measured'),
           ('Broken', '13.5 ms', '27.9 ms', '36 fps', '35.5 fps'),
           ('Halfway', '2.7 ms', '13.8 ms', '73 fps', '70.4 fps'),
           ('All fixes', '2.3 ms', '4.8 ms', '207, capped at 120', '119.8 fps')], bt_style, 'Budget from the traces')
    for i, h_ in enumerate(('The slowest thread sets the rate.', 'A green UI bar proves nothing.', 'The threads overlap.')):
        a = display(s, M, 416 + i * 72, W, 60, h_, 46, TEXT)
        t.click(fx(a))
    source(s, '5 s system traces at 8×, tracing on. Halfway is Simplify plus Batch.')

    # ------------------------------------------------------------ 30. Limits
    s, t = page('Three honest limits.', 'Finish')
    for i, (h_, d) in enumerate((('Order matters.', 'Isolate repaints paid off only once the big cost was gone.'),
                                 ('CPU side only.', 'The GPU’s render passes here are the model, not my trace.'),
                                 ('Skia copes worse.', 'Same chart: 188 ms a frame broken, 58 ms with every fix.'))):
        y = 158 + i * 158
        rule(s, M, y, RIGHT_EDGE, y, TEXT if i == 0 else HAIR)
        display(s, M, y + 44, 520, 70, h_, 50, TEXT)
        text(s, 600, y + 38, 608, 90, d, 28, SUB, spacing=1.16)
    rule(s, M, 158 + 3 * 158, RIGHT_EDGE, 158 + 3 * 158)

    # ------------------------------------------------------------ 31. Take home
    s, t = page('Take this home.')
    for i, (h_, d) in enumerate((('Demystifying\nthe engine', ['Skia: JIT, in the frame.', 'Impeller: AOT, on Vulkan. It tessellates on the CPU and records command buffers.']),
                                 ('Low-level\nprofiling', ['About 4 ms UI, 4 ms raster.', 'DevTools for the frame, Perfetto for the system. The slowest thread sets the rate.']),
                                 ('Taming custom\npainters', ['Fewer points, fewer draws, no saveLayer you don’t need.', 'Pre-compile your own effects. Prove every fix.']))):
        x = M + i * 389
        rule(s, x, 150, x + 358, 150, TEXT)
        display(s, x, 172, 358, 130, h_.split('\n'), 50, TEXT)
        text(s, x, 310, 358, 310, d, 27, SUB, spacing=1.18, gap=14)

    # ------------------------------------------------------------ 32. Close
    s, t = new(layout=ink)
    set_title(s, 'Impeller made\nperformance predictable.\nIt didn’t make\nexpensive work free.', 66, M, 96, 760, 330, PAPER)
    text(s, M, 436, 740, 44, 'Thread, event, code, fix, measure.', 30, ASH, spacing=1.0)
    display(s, M, 540, 700, 40, 'Collins Munene, Shipht', 28, PAPER)
    text(s, M, 582, 720, 30, 'FlutterCon Kenya, Nairobi, 5–6 Nov 2026', 21, ASH, spacing=1.0)
    box(s, 880, 150, 328, 328, WHITE, 'QR background')
    qr = s.shapes.add_picture(os.path.join(A, 'qr-repo.png'), px(892), px(162), px(304), px(304))
    qr._element.find('.//' + qn('p:cNvPr')).set('descr', f'QR code linking to {REPO}')
    qr.click_action.hyperlink.address = REPO
    text(s, 880, 496, 328, 34, 'Scan it. Run it on your phone.', 23, PAPER, MID, spacing=1.0)
    link = text(s, 880, 534, 328, 60, ['github.com/cm-collins/', 'fluttercon-demo-app'], 19, ASH, MONO, spacing=1.1)
    link.click_action.hyperlink.address = REPO

    # ------------------------------------------------------------ Backups
    def backup(heading, rows, widths, heights, foot, style, section=None):
        s, t = new(section)
        set_title(s, heading)
        table(s, M, 142, widths, heights, rows, style, heading)
        source(s, foot)

    def storm_style(i, j, val):
        if i == 0:
            return dict(size=18)
        if j == 0:
            return dict(size=28, font=HEAD)
        if j == 1:
            return dict(size=30, font=HEAD, color=ACC)
        if j == 2:
            return dict(size=30, font=HEAD)
        return dict(size=28, color=SUB)
    backup('Backup: Shader Storm medians', [('Effects', 'Skia cold', 'Impeller cold', 'Skia repeat', 'Impeller repeat', 'Skia relaunch', 'Impeller relaunch'),
                                            ('48', '687', '127', '18', '45', '58', '66'), ('96', '1,310', '145', '19', '43', '81', '73'), ('144', '1,863', '145', '23', '48', '102', '73')],
           (130, 150, 170, 150, 180, 170, 186), (58, 104, 104, 104), 'Worst frame in ms, median of 3 rounds, 120 Hz, tracing off. Infinix X6873, Flutter 3.47.8 profile builds.', storm_style, 'Backup for Q&A')

    def thrash_style(i, j, val):
        if i == 0:
            return dict(size=19)
        if j == 0:
            return dict(size=28, font=HEAD)
        if j == 2:
            return dict(size=30, font=HEAD)
        if j == 4:
            return dict(size=30, font=HEAD, color=ACC)
        return dict(size=28, color=SUB)
    backup('Backup: Canvas Thrash medians at 8×', [('Fixes on', 'Impeller UI', 'Impeller raster', 'Skia UI', 'Skia raster'),
                                                   ('None', '15.9', '29.7', '21.8', '188.4'), ('Simplify', '6.3', '18.6', '23.7', '187.7'), ('Simplify + Batch', '4.9', '13.7', '23.5', '202.3'),
                                                   ('+ Glow', '4.4', '6.6', '3.9', '61.5'), ('+ Isolate', '3.4', '6.5', '3.9', '57.7')],
           (376, 190, 230, 150, 190), (54, 84, 84, 84, 84, 84), 'Frame p90 in ms, median of 3 rounds. Skia trace with all fixes: 47 of 53 ms inside 32 line draws.', thrash_style)

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
