#!/usr/bin/env python3
"""Builds the talk's PowerPoint decks next to this script: beyond-skia.pptx (light) and beyond-skia-dark.pptx.

usage: python3 build_pptx.py        (needs python-pptx, Pillow, and the files in local/)

Every slide has one message and one visual, and nothing else. The explanation lives in the speaker's
voice and the demo app, so speaker notes come from speaker_notes.json.
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
FINAL = os.path.expanduser('~/Documents/fluttercon')  # the presentation lives outside the codebase

# Ink, paper and grey, plus two colours with fixed meanings: ember is the cost, or late; cyan is Impeller, or on time.
TEXT, BG, SUB, CARD, ACC, HAIR, COOL = TC.TEXT_1, TC.BACKGROUND_1, TC.TEXT_2, TC.BACKGROUND_2, TC.ACCENT_1, TC.ACCENT_2, TC.ACCENT_3
THEMES = {
    'light': dict(dk1='141414', lt1='F7F6F2', dk2='6B6A66', lt2='E9E7E0', accent1='D63C0A', accent2='D5D3CB',
                  accent3='0277BD', accent4='6B6A66', accent5='D63C0A', accent6='D5D3CB', hlink='141414', folHlink='6B6A66'),
    'dark': dict(dk1='F4F3EF', lt1='0B0B0C', dk2='A3A29D', lt2='2A2B30', accent1='FF5C28', accent2='38383C',
                 accent3='4FC3F7', accent4='8E8D89', accent5='FF5C28', accent6='38383C', hlink='F4F3EF', folHlink='8E8D89'),
}
INK = RGBColor(0x0B, 0x0B, 0x0C)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
PAPER = RGBColor(0xF4, 0xF3, 0xEF)
ASH = RGBColor(0xAE, 0xAD, 0xA8)
EMBER = RGBColor(0xFF, 0x5C, 0x28)
CYAN = RGBColor(0x4F, 0xC3, 0xF7)
GREY = RGBColor(0x55, 0x55, 0x52)

HEAD, BODY, MID, MONO = 'Inter Display Medium', 'Inter', 'Inter Medium', 'JetBrains Mono'
FONTS = ((HEAD, 'regular', 'InterDisplay-500.ttf'), (BODY, 'regular', 'Inter-400.ttf'), (MID, 'regular', 'Inter-500.ttf'),
         (MONO, 'regular', 'JetBrainsMono-400.ttf'))
NS = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
FONT_REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/font'

# The grid: side margins, the title line, and the line shared by the source and the logo.
M, W, RIGHT_EDGE, TITLE_Y, TITLE_SIZE, FOOT_Y = 72, 1136, 1208, 44, 60, 664
CT, CB = 160, 636  # the content area: every slide has one message and one visual, inside these lines
GUT = 32  # a 12-column grid with 32 px gutters: gx(k) is the left edge of column k, gw(n) the width of n columns

# The only font sizes in the deck, by job.
T_TAG, T_LABEL, T_CODE, T_BODY, T_H3, T_H1, T_NUM, T_HERO, T_MEGA = 18, 20, 24, 28, 36, 60, 72, 104, 160
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
    rpr.set('spc', str(int(-TITLE_SIZE * 1.5)))
    for shape in master.placeholders:
        idx = shape.placeholder_format.idx
        if idx == 0:
            shape.left, shape.top, shape.width, shape.height = px(M), px(TITLE_Y), px(W), px(76)
        elif idx == 1:
            shape.left, shape.top, shape.width, shape.height = px(M), px(150), px(W), px(480)
        else:
            shape.left, shape.top, shape.width, shape.height = px(M), px(FOOT_Y), px(200), px(24)


def layout_title(layout):
    for shape in list(layout.placeholders):
        if shape.placeholder_format.idx == 0:
            shape.left, shape.top, shape.width, shape.height = px(M), px(TITLE_Y), px(W), px(76)
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
            run._r.get_or_add_rPr().set('noProof', '1')
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
    return text(slide, x, y, w, h, value, size, color, HEAD, align, spacing=1.0, track=-size * 1.4, name=name)


def box(slide, x, y, w, h, fill=CARD, name=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(x), px(y), px(w), px(h))
    shape.fill.solid()
    paint(shape.fill.fore_color, fill)
    shape.line.fill.background()
    if name:
        shape.name = name
    return shape


def label_box(slide, x, y, w, h, value, fill, color, size=T_CODE, font=MID, name=None):
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


def set_title(slide, value, size=TITLE_SIZE, x=M, y=TITLE_Y, w=W + 32, h=76, color=None):
    shape = slide.shapes.title
    shape.name = '!!title'  # Morph glides titles from slide to slide
    shape.left, shape.top, shape.width, shape.height = px(x), px(y), px(w), px(h)
    tf = shape.text_frame
    tf.word_wrap = True
    par = tf.paragraphs[0]
    par.line_spacing = 1.0
    for i, part in enumerate(value.split('\n')):
        if i:
            par.add_line_break()
        run = par.add_run()
        run.text = part
        run.font.size = fs(size)
        run.font.bold = False
        run._r.get_or_add_rPr().set('spc', str(int(-size * 1.5)))
        run._r.get_or_add_rPr().set('noProof', '1')
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
        self.media = []

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

    def video(self, pic, ms):
        """Plays by itself when the slide appears, and loops."""
        self.media.append((pic.shape_id, ms))

    def write(self):
        sld = self.slide._element
        for old in sld.findall(qn('p:timing')):
            sld.remove(old)
        sld.find(qn('p:clrMapOvr')).addnext(etree.fromstring(f'''<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:p="{NS['p']}"><mc:Choice xmlns:p159="http://schemas.microsoft.com/office/powerpoint/2015/09/main" xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main" Requires="p159"><p:transition spd="slow" p14:dur="800"><p159:morph option="byObject"/></p:transition></mc:Choice><mc:Fallback><p:transition spd="med"><p:fade/></p:transition></mc:Fallback></mc:AlternateContent>'''))
        if not self.steps and not self.media:
            return
        self.by_id = {int(n.get('id')): n.getparent().getparent() for n in sld.iter(qn('p:cNvPr'))}
        out = []
        for spid, ms in self.media:
            outer, inner, eff, cmd = self.nid(), self.nid(), self.nid(), self.nid()
            out.append(f'''<p:par><p:cTn id="{outer}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/><p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst><p:childTnLst><p:par><p:cTn id="{inner}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst><p:par><p:cTn id="{eff}" presetID="1" presetClass="mediacall" presetSubtype="0" fill="hold" nodeType="afterEffect"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst><p:cmd type="call" cmd="playFrom(0.0)"><p:cBhvr><p:cTn id="{cmd}" dur="{ms}" fill="hold"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:cmd></p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>''')
        for effects in self.steps:
            inner = ''.join(self.entrance(e['id'], e['kind'], e.get('delay', 0), e.get('dur', 450), 'clickEffect' if j == 0 else 'withEffect')
                            for j, e in enumerate(effects))
            out.append(f'''<p:par><p:cTn id="{self.nid()}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst><p:par><p:cTn id="{self.nid()}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>{inner}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>''')
        nodes = ''.join(f'''<p:video><p:cMediaNode vol="0"><p:cTn id="{self.nid()}" repeatCount="indefinite" fill="hold" display="0"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cMediaNode></p:video>''' for spid, _ in self.media)
        bld = ''
        for s in self.bld:
            has_fill = self.by_id[s].find(qn('p:spPr')).find(qn('a:noFill')) is None
            bld += f'<p:bldP spid="{s}" grpId="0"' + (' animBg="1"' if has_fill else '') + '/>'
        sld.append(etree.fromstring(f'''<p:timing xmlns:p="{NS['p']}"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>{''.join(out)}</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst><p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>{nodes}</p:childTnLst></p:cTn></p:par></p:tnLst>{f'<p:bldLst>{bld}</p:bldLst>' if bld else ''}</p:timing>'''))


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

    def page(title, section=None):
        s, t = new(section)
        set_title(s, title)
        return s, t

    def tag(s, value, color=SUB):
        """Only where honesty needs it: a few quiet words, level with the logo."""
        return text(s, M, FOOT_Y, 980, 24, value, T_TAG, color, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0, name='Tag')

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
        return text(s, x, y, w, h, out, T_CODE, TEXT, MONO, spacing=1.22, name='Code')

    def result(s, y, a, b, unit, size=T_NUM):
        """One measured change, large."""
        return text(s, M, y, W, size * 1.3, [[(a, {'color': SUB}), (' → ', {'color': SUB}), (b, {}), (' ' + unit, {'color': SUB, 'size': T_BODY, 'track': 0})]], size, TEXT, HEAD, spacing=1.0, track=-size)

    def vis(name):
        return os.path.join(L, 'visuals', f'{name}.jpg')

    def full(s, name, alt, at=2):
        """A full-screen picture behind everything else on the slide."""
        art = s.shapes.add_picture(vis(name), 0, 0, px(1280), px(720))
        art._element.find('.//' + qn('p:cNvPr')).set('descr', alt)
        s.shapes._spTree.remove(art._element)
        s.shapes._spTree.insert(at, art._element)
        return art

    def logo_on_art(s):
        pic = s.shapes.add_picture(os.path.join(L, 'fluttercon-dark.png'), px(RIGHT_EDGE - 116), px(FOOT_Y + 2), px(116), px(20))
        pic._element.find('.//' + qn('p:cNvPr')).set('descr', 'FlutterCon logo')

    MS = dict(frame=15500, cmd=13000, layer=19000, simplify=11000, batch=13000, repaint=12000, frames=9000, wall=6200, layers=10500)

    def clip(s, t, name, x, y, w, h, alt):
        """An animated explainer that plays by itself and loops. The poster is what a PDF or preview shows."""
        pic = s.shapes.add_movie(os.path.join(L, 'visuals', f'{name}.mp4'), px(x), px(y), px(w), px(h), poster_frame_image=vis(name), mime_type='video/mp4')
        pic.name = name
        pic._element.find('.//' + qn('p:cNvPr')).set('descr', alt)
        t.video(pic, MS[name])
        return pic

    def explainer(title, sentence, section=None):
        """A title, one sentence that teaches the idea, and the animation that shows it."""
        s, t = new(section, ink)
        set_title(s, title, color=PAPER)
        text(s, M, 122, W, 40, sentence, T_BODY, ASH, spacing=1.0, name='Explanation')
        return s, t

    def ink_code(s, x, y, w, h, lines):
        out = []
        for line in lines:
            c = PAPER
            if line.startswith('!!'):
                line, c = '// ' + line[2:].strip(), EMBER
            elif line.startswith('++'):
                line, c = '// ' + line[2:].strip(), CYAN
            out.append([(line, {'color': c})])
        return text(s, x, y, w, h, out, T_CODE, PAPER, MONO, spacing=1.22, name='Code')

    PLATES = dict(plain=(CARD, RGBColor(0x08, 0x09, 0x0B) if dark else RGBColor(0xC9, 0xC7, 0xBF), TEXT),
                  cyan=(COOL, RGBColor(0x1F, 0x6F, 0x96) if dark else RGBColor(0x01, 0x4F, 0x82), INK if dark else WHITE),
                  ember=(ACC, RGBColor(0x9C, 0x35, 0x14) if dark else RGBColor(0x8F, 0x28, 0x06), INK if dark else WHITE),
                  ghost=(None, None, SUB))

    def plate(s, x, y, w, h, words, kind='plain', size=T_BODY, font=MID, name=None):
        """The deck's one block: a flat top with a thin lower edge, so it reads as a solid layer."""
        top, edge, ink_ = PLATES[kind]
        group = s.shapes.add_group_shape()
        if edge is not None:
            e = group.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(x), px(y + h), px(w), px(6))
            e.fill.solid()
            paint(e.fill.fore_color, edge)
            e.line.fill.background()
        b_ = group.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(x), px(y), px(w), px(h))
        if top is None:
            b_.fill.background()
            paint(b_.line.color, SUB)
            b_.line.width = fs(1.5)
            etree.SubElement(b_.line._get_or_add_ln(), qn('a:prstDash')).set('val', 'dash')
        else:
            b_.fill.solid()
            paint(b_.fill.fore_color, top)
            b_.line.fill.background()
        tf = b_.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left, tf.margin_right = px(20), px(14)
        tf.margin_top = tf.margin_bottom = 0
        par = tf.paragraphs[0]
        par.alignment = LEFT
        par.line_spacing = 1.08
        r = par.add_run()
        r.text = words
        r.font.size, r.font.bold, r.font.name = fs(size), False, font
        paint(r.font.color, ink_)
        r._r.get_or_add_rPr().set('noProof', '1')
        group.name = name or words
        return group

    def mix(c1, c2, amount):
        """A step between two theme colours, for the overdraw heat picture."""
        slot = {BG: 'lt1', ACC: 'accent1', SUB: 'dk2', TEXT: 'dk1'}
        one, two = THEMES[variant][slot[c1]], THEMES[variant][slot[c2]]
        return RGBColor(*[int(int(one[i:i + 2], 16) * (1 - amount) + int(two[i:i + 2], 16) * amount) for i in (0, 2, 4)])

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
    set_title(s, 'Beyond\nSkia', T_HERO, M, 150, gw(7), 256, INK)
    text(s, M, 412, gw(7) - 60, 90, 'GPU scheduling and profiling with Impeller on Android 10+', T_BODY, GREY, spacing=1.14)
    photo = s.shapes.add_picture(os.path.join(L, 'speaker.jpg'), px(gx(8)), px(96), px(gw(4)), px(372))
    photo.crop_bottom = 1 - 372 / (gw(4) * 1200 / 1020)
    photo._element.find('.//' + qn('p:cNvPr')).set('descr', 'Collins Munene')
    geom = photo._element.find('.//' + qn('a:prstGeom'))
    geom.set('prst', 'round2SameRect')
    av = geom.find(qn('a:avLst'))
    for key, val in (('adj1', 50000), ('adj2', 0)):
        gd = etree.SubElement(av, qn('a:gd'))
        gd.set('name', key)
        gd.set('fmla', f'val {val}')
    display(s, gx(8), 484, gw(4), 46, 'Collins Munene', T_H3, PAPER)
    text(s, gx(8), 530, gw(4) + 40, 30, 'DevOps and Software Engineer, Shipht', T_LABEL, ASH, spacing=1.0, track=-20)

    # ------------------------------------------------------------ 2. The map
    s, t = new(layout=ink)
    set_title(s, 'Impeller tamed\none kind of jank.', T_HERO, M, 58, W, 256, PAPER)
    shot(s, vis('spark-jank'), gx(0), 336, gw(6), alt='Every raster frame of a Skia run: flat, then one frame of 1.8 seconds')
    shot(s, vis('spark-draw'), gx(6), 336, gw(6), alt='Every raster frame of the broken chart: all of them far above the 8.3 ms line')
    text(s, gx(0), 536, gw(6), 50, [[('Tamed: ', {'color': ASH}), ('compilation jank', {'color': CYAN})]], T_H3, PAPER, HEAD, spacing=1.0, track=-40)
    text(s, gx(0), 584, gw(6), 34, 'One frame, 1.8 s', T_CODE, ASH, spacing=1.0)
    text(s, gx(6), 536, gw(6), 50, [[('Still here: ', {'color': ASH}), ('drawing cost', {'color': EMBER})]], T_H3, PAPER, HEAD, spacing=1.0, track=-40)
    text(s, gx(6), 584, gw(6), 34, 'Every frame, 28 ms', T_CODE, ASH, spacing=1.0)
    tag(s, 'Real frames from the traces. Each chart has its own scale.', ASH)

    # ------------------------------------------------------------ 3. One frame
    s, t = page('One frame, from vsync to pixels.', 'How Flutter draws')
    TH, TY = 280, CT + 4
    cards = []
    panel = box(s, gx(0), TY, gw(4), TH, CARD, 'A DisplayList')
    list_ = text(s, gx(0) + 24, TY, gw(4) - 40, TH, ['drawPath(line)', 'drawCircle(dot)', 'drawVertices()', 'saveLayer(blur)'], T_CODE, TEXT, MONO, anchor=MSO_ANCHOR.MIDDLE, spacing=1.5)
    tri = shot(s, vis('tess-4'), gx(4), TY, gw(4), (0.04, 0.12, 0.48, 0.211), alt='The same line, cut into triangles')
    pix = shot(s, vis('chart-full'), gx(8), TY, gw(4), (0, 0.08, 0.5, 0.223), alt='The finished chart in pixels')
    groups = [[panel, list_], [tri], [pix]]
    for i, (who, verb, hot, shapes_) in enumerate((('Dart', 'Records', False, groups[0]), ('Engine, on 1.raster', 'Prepares', True, groups[1]), ('GPU', 'Executes', False, groups[2]))):
        x, w_ = gx(i * 4), gw(4)
        a = text(s, x, TY + TH + 16, w_, 36, who, T_BODY, SUB, spacing=1.0)
        b = display(s, x, TY + TH + 52, w_, 92, verb, T_NUM, ACC if hot else TEXT)
        t.click(*[fx(q) for q in shapes_], fx(a), fx(b))

    # ------------------------------------------------------------ 4. The budget
    s, t = explainer('Every frame gets 8.3 ms.', 'A frame that misses the tick leaves the old frame on screen.')
    clip(s, t, 'frame', 0, 172, 1280, 456, 'Frames against the 8.3 ms ticks. On target, every tick shows a new frame. Measured at 28 ms raster, the screen repeats the old frame.')

    # ------------------------------------------------------------ 5. Compilation jank
    s, t = explainer('Compilation jank.', 'Skia compiles each new shader inside the frame. Nothing moves until they finish.', 'Before: Skia')
    clip(s, t, 'wall', 0, 172, 1280, 456, 'A real Skia frame: 118 shaders compile one after another for 1.82 seconds, beside a tiny bar for one frame’s budget')
    tag(s, 'Every block is one real shader from the trace, to scale.', ASH)

    # ------------------------------------------------------------ 6. The engine, before and now
    s, t = new('Now: Impeller', ink)
    set_title(s, 'The Android engine, before and now.', color=PAPER)
    full(s, 'engine-before', 'The engine before: nothing compiled ahead; 1.raster writes and compiles shaders; OpenGL ES')
    now = full(s, 'engine-now', 'The engine now: impellerc compiles shaders ahead; 1.raster binds pipelines, tessellates and records; no raster cache; Vulkan', 3)
    t.click(fx(now, dur=700))
    tag(s, 'Android, simplified. iOS and macOS use Metal.', ASH)

    # ------------------------------------------------------------ 7. Late and early
    s, t = page('Skia compiles late. Impeller compiles early.')
    col_x = [gx(2 + 2 * i) for i in range(5)]
    CWD = gw(2)
    for x, st in zip(col_x, ('Engine build', 'App build', 'App start', 'First use', 'Every frame')):
        text(s, x, CT + 4, CWD + 24, 30, st, T_LABEL, SUB, spacing=1.0)
    rule(s, M, 196, RIGHT_EDGE, 196, TEXT)
    rule(s, M, 408, RIGHT_EDGE, 408)
    for y, name, kind in ((222, 'Skia', 'JIT'), (434, 'Impeller', 'AOT')):
        display(s, gx(0), y, gw(2) + 16, 46, name, T_H3, TEXT)
        text(s, gx(0), y + 48, gw(2), 34, kind, T_CODE, SUB, MONO, spacing=1.0)
    a = plate(s, col_x[3], 222, CWD, 156, 'In the frame', 'ember', T_CODE)
    t.click(fx(a))
    b = plate(s, col_x[0], 434, CWD, 156, 'Engine shaders', 'cyan', T_CODE)
    c = plate(s, col_x[1], 434, CWD, 156, 'Your .frag', 'cyan', T_CODE)
    d = plate(s, col_x[3], 434, CWD, 156, 'A little left: 2.2 ms a pipeline', 'ghost', T_CODE)
    t.click(fx(b), fx(c, delay=150), fx(d, delay=300))

    # ------------------------------------------------------------ 8. Which backend
    s, t = page('On Android, Vulkan isn’t guaranteed.')
    RH = 88
    rows_ = []
    for i, (when, what, kind) in enumerate((('Android 9 or older', 'Skia on OpenGL ES', 'ghost'),
                                            ('Android 10+, a device check fails', 'Impeller on OpenGL ES', 'ember'),
                                            ('Android 10+, every check passes', 'Impeller on Vulkan', 'cyan'))):
        y = CT + 8 + i * (RH + 18)
        a = text(s, gx(0), y, gw(6) - 16, RH, when, T_BODY, SUB if i == 0 else TEXT, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0)
        b = plate(s, gx(6), y, gw(6), RH, what, kind, T_H3, HEAD)
        if i:
            rows_ += [a, b]
    t.click(*[fx(x, delay=i * 90) for i, x in enumerate(rows_)])
    proof = plate(s, gx(0), 500, W, 76, 'adb logcat | grep "Impeller rendering backend"', 'plain', T_CODE, MONO)
    t.click(fx(proof))

    # ------------------------------------------------------------ 9. Scoreboard
    s, t = page('Same app. Same phone. Two renderers.', 'The proof')
    CX = (gx(3), gx(8))
    text(s, CX[0], CT + 6, gw(4), 36, 'First reveal', T_BODY, SUB, spacing=1.0)
    text(s, CX[1], CT + 6, gw(4), 36, 'Second time', T_BODY, SUB, spacing=1.0)

    def score(x, y, value, color=TEXT):
        return text(s, x, y, gw(5), 150, [[(value, {'color': color}), (' ms', {'size': T_BODY, 'color': SUB, 'track': 0})]], T_HERO, TEXT, HEAD, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0, track=-T_HERO * 1.4)
    rule(s, M, 206, RIGHT_EDGE, 206, TEXT)
    rule(s, M, 360, RIGHT_EDGE, 360)
    rule(s, M, 514, RIGHT_EDGE, 514)
    text(s, gx(0), 206, gw(3), 154, 'Skia', T_H3, SUB, HEAD, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0, track=-40)
    text(s, gx(0), 360, gw(3), 154, 'Impeller', T_H3, TEXT, HEAD, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0, track=-40)
    a = score(CX[0], 208, '1,863', ACC)
    t.click(fx(a))
    b_ = score(CX[1], 208, '23', SUB)
    t.click(fx(b_))
    c = score(CX[0], 362, '145', COOL)
    d = score(CX[1], 362, '48', COOL)
    t.click(fx(c), fx(d, delay=250))
    e = display(s, M, 536, W, 80, '13× shorter.', T_H1, TEXT)
    t.click(fx(e))
    tag(s, 'Worst frame, median of 3 rounds. Infinix X6873, 120 Hz.')

    # ------------------------------------------------------------ 10. The cost moved
    s, t = page('The cost shrank and moved. It didn’t vanish.')
    TK = W / 1714
    a1 = display(s, M, CT + 10, gw(8), 46, 'Skia: 118 shaders', T_H3, TEXT)
    a2 = display(s, gx(8), CT + 10, gw(4), 46, '1,714 ms', T_H3, ACC, RIGHT)
    g = s.shapes.add_group_shape()
    for i in range(118):
        r = g.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(M + i * 14.53 * TK), px(218), px(14.53 * TK - 1.6), px(136))
        r.fill.solid()
        paint(r.fill.fore_color, ACC)
        r.line.fill.background()
    g.name = '118 Skia programs, to scale'
    b1 = display(s, M, 398, gw(8), 46, 'Impeller: 40 pipelines', T_H3, TEXT)
    b2 = display(s, gx(8), 398, gw(4), 46, '87 ms', T_H3, COOL, RIGHT)
    b3 = box(s, M, 456, 87 * TK, 136, COOL, '40 Impeller pipelines, to scale')
    t.click(fx(a1), fx(a2), fx(g, 'left', dur=900), fx(b1, delay=500), fx(b2, delay=500), fx(b3, 'left', dur=400, delay=500))
    tag(s, 'Real traces of one cold reveal, to scale.')

    # ------------------------------------------------------------ 11. The mountain
    s, t = new('Inside a frame', ink)
    set_title(s, 'To the GPU, everything is triangles.', color=PAPER)
    full(s, 'mountain', 'The same mountain twice: on the left as a mesh of triangles, on the right as finished pixels')
    logo_on_art(s)

    # ------------------------------------------------------------ 12. Tessellation
    s, t = new(layout=ink)
    set_title(s, 'Tessellation: how a path becomes triangles.', color=PAPER)
    stages = [full(s, f'tess-{i + 1}', a, 2 + i) for i, a in enumerate(('A stretch of the demo’s real line', 'The line as points', 'Two vertices at each point', 'The vertices joined into a triangle strip'))]
    head_ = [text(s, gx(i * 3), CT + 6, gw(3), 46, h_, T_H3, PAPER, HEAD, spacing=1.0, track=-40) for i, h_ in enumerate(('Path', 'Points', 'Vertices', 'Triangles'))]
    for art, h_ in zip(stages, head_):
        t.click(fx(art, dur=500), fx(h_))
    bottom = text(s, M, 586, W, 54, [[('256,000+', {'color': EMBER}), (' vertices, on the CPU, every frame.', {'color': PAPER})]], T_H3, PAPER, HEAD, spacing=1.0, track=-40)
    t.click(fx(bottom))
    tag(s, 'The demo’s real line, with the stroke widened. The count is worked out, not measured.', ASH)
    logo_on_art(s)

    # ------------------------------------------------------------ 13. Who does what
    s, t = page('Who does what.')
    for x, heading, lines in ((gx(0), 'The CPU, on 1.raster', ['Replays the DisplayList', 'Gets the pipelines', 'Tessellates paths', 'Fills the vertex buffers', 'Records and submits commands']),
                              (gx(6), 'The GPU', ['Runs the vertex shaders', 'Turns triangles into pixels', 'Runs the fragment shaders', 'Writes the finished image'])):
        display(s, x, CT + 2, gw(6), 46, heading, T_H3, TEXT)
        for i, line in enumerate(lines):
            plate(s, x, CT + 58 + i * 84, gw(6), 72, line, 'ember' if line.startswith('Tessellates') else 'plain', T_BODY, BODY)

    # ------------------------------------------------------------ 14. Command buffers
    s, t = explainer('The CPU records. The GPU executes.', 'The raster thread writes the list and moves on. The GPU runs it later.')
    clip(s, t, 'cmd', 0, 172, 1280, 456, 'Frame 1 is recorded as a command buffer, submitted to the queue and run by the GPU, while the raster thread is already recording frame 2')
    tag(s, 'Illustration of the order of work: this is GPU scheduling.', ASH)

    # ------------------------------------------------------------ 15. Overdraw
    s, t = new(layout=ink)
    set_title(s, 'Overdraw: painting the same pixel again.', color=PAPER)
    full(s, 'stack', 'A screen pulled apart into three layers: an image, a card and text')
    pin = full(s, 'stack-pin', 'The same layers, with one pixel marked on each', 3)
    ink_code(s, gx(6), 228, gw(6), 300, ['Stack(', '  children: [', '    Image.asset(\'bg.png\'),    // 1×', '    Card(                     // 2×', '      child: Text(\'KSh 900\'), // 3×', '    ),', '  ],', ')'])
    t.click(fx(pin, dur=500))
    text(s, gx(6), FOOT_Y, 440, 24, 'Illustration. Not measured in my demo.', T_TAG, ASH, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0, name='Tag')
    logo_on_art(s)

    # ------------------------------------------------------------ 16. The layer
    s, t = explainer('Why a layer costs more than a draw.', 'A layer forces round trips from fast tile memory to slow main memory.')
    clip(s, t, 'layer', 0, 172, 1280, 456, 'One render pass needs one trip to main memory. The same frame with one saveLayer needs four.')
    tag(s, 'Illustration: the Vulkan model, not my trace.', ASH)

    # ------------------------------------------------------------ 17. What it didn't fix, and the bill
    s, t = new('What Impeller didn’t fix', ink)
    set_title(s, 'What Impeller\ndidn’t fix.', T_HERO, M, 58, gw(9) - 20, 256, PAPER)
    bill = []
    for x, w_, val, name, c in ((gx(0), gw(3), '129,920', 'path points', EMBER), (gx(3) + 24, gw(2), '624', 'draw calls', PAPER), (gx(5) + 24, gw(2), '64', 'layers', PAPER)):
        bill.append(display(s, x, 356, w_ + 24, 92, val, T_NUM, c))
        bill.append(text(s, x, 448, w_ + 24, 36, name, T_BODY, ASH, spacing=1.0))
    bill.append(text(s, M, 530, gw(8), 60, 'Nothing is compiling.', T_H3, PAPER, HEAD, spacing=1.0, track=-40))
    t.click(*[fx(x, delay=i * 60) for i, x in enumerate(bill)])
    shot(s, os.path.join(L, 'poster-thrash-broken.png'), RIGHT_EDGE - 300, 0, 300, (0, 0.045, 0, 0.02), alt='Canvas Thrash in the demo app at 8×: both lanes red')

    # ------------------------------------------------------------ 18. The vote
    s, t = page('Which fix helps most, on its own?')
    BX2, BASE = gx(4), gx(10) + 40
    BK2 = (BASE - BX2) / 29.7
    text(s, BASE - 300, CT + 2, 294, 26, 'No fixes: 29.7 ms', T_LABEL, SUB, align=RIGHT, spacing=1.0)
    rule(s, M, 192, RIGHT_EDGE, 192, TEXT)
    fxs = []
    for i, (name, v) in enumerate((('Simplify paths', 18.6), ('Batch draws', 28.6), ('Glow without layers', 21.2), ('Isolate repaints', 25.2))):
        y = 192 + i * 110
        text(s, gx(0), y, gw(4) + 20, 110, name, T_H3, TEXT, HEAD, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0, track=-40)
        hot = i == 0
        b = box(s, BX2, y + 16, v * BK2, 78, COOL if hot else CARD, f'{name}: {v} ms')
        n = text(s, BASE + 16, y, RIGHT_EDGE - BASE - 16, 110, str(v), T_H3, COOL if hot else TEXT, HEAD, RIGHT, MSO_ANCHOR.MIDDLE, spacing=1.0, track=-40)
        fxs += [fx(b, 'left', dur=700, delay=i * 120), fx(n, delay=500 + i * 120)]
    t.click(*fxs)
    rule(s, BASE, 192, BASE, CB, TEXT, 1.5)

    # ------------------------------------------------------------ 19. One pixel column
    s, t = new(layout=ink)
    set_title(s, 'One pixel column. 25 points.', color=PAPER)
    full(s, 'macro', 'One pixel column of the demo’s line, on a pixel grid, holding 25 real points')
    text(s, M, 286, gw(6) - 30, 150, ['8,000 points a line,', 'on a chart 316 pixels wide.'], T_H3, PAPER, HEAD, spacing=1.16, track=-40)
    tag(s, 'Real points from the demo. The vertical scale is approximate.', ASH)
    logo_on_art(s)

    # ------------------------------------------------------------ 20. Fix 1
    s, t = explainer('Fix 1: Simplify paths.', 'Keep each column’s lowest and highest point. The picture stays the same.')
    clip(s, t, 'simplify', 0, 172, 1280, 456, 'A line sweeps across the real chart. Behind it each pixel column keeps 2 points, not 25, and the chart looks the same.')
    tag(s, 'Drawn from the demo’s real data.', ASH)

    # ------------------------------------------------------------ 21. Fix 2
    s, t = explainer('Fix 2: Batch draws.', 'Each segment was its own draw. As two triangles each, they all fit in one.')
    clip(s, t, 'batch', 0, 172, 1280, 456, 'Each segment of the heat strip sends its own draw, 480 in all. Then all the segments go in one drawVertices call.')
    tag(s, 'Illustration of the heat strip. Draw calls overall at 8×: 640 → 161.', ASH)

    # ------------------------------------------------------------ 22. Fix 3
    s, t = new(layout=ink)
    set_title(s, 'Fix 3: Glow without saveLayer.', color=PAPER)
    clip(s, t, 'layers', 672, 116, 608, 536, 'Each glowing dot lifts its own offscreen layer off the chart, 64 in all. Then they sink away, and the same glow needs none.')
    text(s, M, 136, gw(6) - 24, 76, 'Each dot was its own layer. A gradient gives the same glow with none.', T_BODY, ASH, spacing=1.14)
    text(s, M, 230, gw(6), 100, [[('64', {'color': EMBER}), (' → ', {'color': ASH}), ('0', {'color': CYAN}), (' layers a frame', {'color': ASH, 'size': T_BODY, 'track': 0})]], T_NUM, PAPER, HEAD, spacing=1.0, track=-90)
    ink_code(s, M, 340, gw(6), 170, ['!!Before: a pass and a blur', 'canvas.saveLayer(bounds, blur);', '++After: same glow, main pass', 'canvas.drawCircle(c, r, glow);'])
    text(s, M, 518, gw(6), 30, 'These can trigger a saveLayer too:', T_LABEL, ASH, spacing=1.0)
    text(s, M, 548, gw(6), 72, ['Opacity  ShaderMask  ColorFilter', 'Clip.antiAliasWithSaveLayer'], T_LABEL, PAPER, MONO, spacing=1.2)
    tag(s, 'Dots placed by the demo’s formula. Layout and heights are illustrative.', ASH)

    # ------------------------------------------------------------ 23. Fix 4
    s, t = explainer('Fix 4: A RepaintBoundary, on its own?', 'Dart stops re-recording the grid. The raster thread still draws it every frame.')
    clip(s, t, 'repaint', 0, 172, 1280, 404, 'Without a boundary, Dart records the grid and lines every frame. With one, Dart records only the lines, and the raster thread still draws both.')
    a = text(s, gx(0), 590, gw(6), 56, 'Alone at 8×: almost nothing.', T_H3, PAPER, HEAD, spacing=1.0, track=-40)
    t.click(fx(a))
    ans = text(s, gx(6), 590, gw(6), 56, 'Dart work, not GPU work.', T_H3, EMBER, HEAD, RIGHT, spacing=1.0, track=-40)
    t.click(fx(ans))

    # ------------------------------------------------------------ 24. The result
    s, t = page('Four fixes. From 36 fps to 120.')
    BWD = (W - 4 * GUT) / 5
    base, unit_ = 586, 12.4
    limit_y = base - 8.33 * unit_
    for i, (v, lab) in enumerate((('29.7', 'No fixes'), ('18.6', '+ Simplify'), ('13.7', '+ Batch'), ('6.6', '+ Glow'), ('6.5', '+ Isolate'))):
        x = M + i * (BWD + GUT)
        h = float(v) * unit_
        over = float(v) > 8.33
        b = box(s, x, base - h, BWD, h, ACC if over else COOL, f'{lab}: {v} ms')
        n = display(s, x, (base - h - 52) if over else (limit_y - 52), BWD, 48, v, T_H3, TEXT)
        text(s, x, base + 10, BWD, 34, lab, T_CODE, SUB, spacing=1.0)
        t.click(fx(b, 'up', dur=500), fx(n))
    rule(s, M, limit_y, RIGHT_EDGE, limit_y, TEXT, 1.5, 'dash')
    tag(s, 'Raster p90 in ms at 8×, median of 3 rounds. The line is 8.3 ms.')

    # ------------------------------------------------------------ 25. Your own shader
    s, t = page('Your effects can be pre-compiled too.', 'Your own shader')
    code(s, gx(0), CT + 8, gw(7), 400, ['# pubspec.yaml', 'shaders: [shaders/depth_fill.frag]', '', '// Once, before it is needed', 'final program = await', '    FragmentProgram.fromAsset(path);', '', '// paint(): one draw', 'canvas.drawPath(depth, shaderPaint);'])
    RX, RW = gx(7), gw(5)
    text(s, RX, CT + 2, RW, 80, [[('503', {'color': SUB}), (' → ', {'color': SUB}), ('4,008 B', {})]], T_H1, TEXT, HEAD, spacing=1.0, track=-80)
    for i, (words, kind) in enumerate((('SPIR-V for Vulkan', 'cyan'), ('GLSL ES for OpenGL ES', 'plain'), ('SkSL for Skia', 'ember'))):
        plate(s, RX, CT + 96 + i * 92, RW, 78, words, kind, T_BODY, MID)
    tag(s, 'This shader wasn’t timed on the phone.')

    # ------------------------------------------------------------ 26. DevTools
    s, t = page('DevTools: which thread, then which code.', 'Prove it')
    shot(s, os.path.join(L, 'devtools-frames-8x.png'), 0, CT - 8, 1280, (0, 0.037, 0.498, 0.759), alt='Flutter DevTools frames chart at 8×: every frame is red, and raster is taller than UI')
    STEP5 = (W + GUT) / 5
    for i, w_ in enumerate(('Which thread?', 'Which event?', 'Which code?', 'One fix.', 'Measure again.')):
        x = M + i * STEP5
        rule(s, x, 476, x + STEP5 - GUT, 476, TEXT)
        display(s, x, 494, STEP5 - GUT + 8, 110, w_.split(' '), T_H3, ACC if i == 4 else TEXT)
    tag(s, 'Emulator in debug mode: read the shape, not the milliseconds.')

    # ------------------------------------------------------------ 27. Perfetto
    s, t = explainer('Systrace, now Perfetto: 5 s of frames.', 'Every bar is one raster frame, at real speed. The dashed line is 8.3 ms.')
    clip(s, t, 'frames', 0, 172, 1280, 372, 'Every raster frame in five seconds. Broken: 179 tall frames above the 8.3 ms line. Fixed: 604 short frames below it.')
    ans = display(s, M, 554, W, 84, 'No. It’s running for 24 of its 28 ms.', T_H1, PAPER)
    t.click(fx(ans))
    tag(s, 'Recorded with atrace, tracing on. Same scale in both rows.', ASH)

    # ------------------------------------------------------------ 28. The budget, read
    s, t = page('Read the budget from the trace.')

    def bt_style(i, j, val):
        if j == 0:
            return dict(size=T_H3, font=HEAD, color=ACC if i == 1 else (COOL if i == 3 else TEXT))
        if j == 2:
            return dict(size=T_H3, font=HEAD, color=ACC if i < 3 else COOL)
        if j == 3:
            return dict(size=T_H3, font=HEAD, color=COOL if i == 3 else TEXT)
        return dict(size=T_H3, color=SUB)
    table(s, M, CT + 2, (gw(3) + GUT, gw(3) + GUT, gw(3) + GUT, gw(3)), (40, 88, 88, 88),
          [('', 'UI', 'Raster', 'Frame rate'),
           ('Broken', '13.5 ms', '27.9 ms', '35.5 fps'),
           ('Halfway', '2.7 ms', '13.8 ms', '70.4 fps'),
           ('All fixes', '2.3 ms', '4.8 ms', '119.8 fps')], bt_style, 'Budget from the traces')
    lesson = display(s, M, 510, W, 84, 'The slowest thread sets the rate.', T_H1, ACC)
    t.click(fx(lesson))
    tag(s, 'Trace medians at 8×, tracing on. Target: about 4 ms UI, 4 ms raster.')

    # ------------------------------------------------------------ 29. Take home
    s, t = page('Take this home.', 'Finish')
    rule(s, M, CT + 6, RIGHT_EDGE, CT + 6, TEXT)
    for i, (h_, d) in enumerate((('Demystifying the engine', 'Skia: JIT, in the frame. Impeller: AOT, on Vulkan.'),
                                 ('Low-level profiling', 'About 4 ms UI, 4 ms raster. The slowest thread sets the rate.'),
                                 ('Taming custom painters', 'Fewer points, fewer draws, no saveLayer you don’t need.'))):
        y = CT + 6 + i * 150
        text(s, gx(0), y, gw(6), 150, h_, T_H3, TEXT, HEAD, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0, track=-40)
        text(s, gx(6), y, gw(6), 150, d, T_BODY, SUB, anchor=MSO_ANCHOR.MIDDLE, spacing=1.16)
        rule(s, M, y + 150, RIGHT_EDGE, y + 150)

    # ------------------------------------------------------------ 30. Close
    s, t = new(layout=ink)
    set_title(s, 'Impeller made\nperformance predictable.\nIt didn’t make\nexpensive work free.', T_NUM, M, 72, gw(9), 370, PAPER)
    full(s, 'close-bg', 'The demo’s chart, dimmed')
    display(s, M, 434, gw(8), 40, 'Collins Munene, Shipht', T_BODY, PAPER)
    link = text(s, M, 474, gw(9), 30, 'github.com/cm-collins/fluttercon-demo-app', T_LABEL, ASH, MONO, spacing=1.0)
    link.click_action.hyperlink.address = REPO
    box(s, gx(9), 84, gw(3), gw(3), WHITE, 'QR background')
    qr = s.shapes.add_picture(os.path.join(A, 'qr-repo.png'), px(gx(9) + 10), px(94), px(gw(3) - 20), px(gw(3) - 20))
    qr._element.find('.//' + qn('p:cNvPr')).set('descr', f'QR code linking to {REPO}')
    qr.click_action.hyperlink.address = REPO
    logo_on_art(s)

    # ------------------------------------------------------------ Backups
    def backup(heading, rows, widths, heights, foot, style, section=None):
        s, t = new(section)
        set_title(s, heading)
        table(s, M, CT - 12, widths, heights, rows, style, heading)
        tag(s, foot)

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
    os.makedirs(os.path.join(FINAL, 'light-version'), exist_ok=True)
    out = os.path.join(FINAL, 'Beyond-Skia.pptx') if dark else os.path.join(FINAL, 'light-version', 'Beyond-Skia-Light.pptx')
    prs.save(out)
    print(variant, os.path.getsize(out) // 1024, 'KB,', len(prs.slides), 'slides')


if __name__ == '__main__':
    build('light')
    build('dark')
