#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random

from config import *

# Directions are:
# +. left to right
# -. right to left
# .+ top to bottom
# .- bottom to top

def read_words(filename):
    words = set()
    fd = open(filename)
    try:
        for line in fd.readlines():
            if "'" in line:
                continue
            line = line.strip().lower()
            if len(line) > 3 and len(line) < 7:
                words.add(line)
    finally:
        fd.close()
    return words

all_words = read_words('/usr/share/dict/words')
explicit_words = ('fuck', 'cunt', 'piss', 'bloody', 'shit', 'boob')
for word in explicit_words:
    all_words.add(word)

all_directions = ('+-', '+.', '++', '.+', '.-', '--', '-.', '-+')

styles = {
    'easy': ('10x10', ('+.', '.+')),
    'standard': ('15x15', ('+-', '+.', '++', '.+', '.-', '-.')),
    'hard': ('15x15', all_directions)
}

dirconv = {
    '-': -1,
    '.': 0,
    '+': 1,
}

letters = "abcdefghijklmnopqrstuvwxyz"

class Grid(object):
    def __init__(self, wid, hgt):
        self.wid = wid
        self.hgt = hgt
        self.data = ['.'] * (wid * hgt)
        self.used = [' '] * (wid * hgt)
        self.words = []

    def to_text(self):
        result = []
        for row in xrange(self.hgt):
            result.append(''.join(self.data[row * self.wid :
                                  (row + 1) * self.wid]))
        return '\n'.join(result)

    def used_to_text(self):
        result = []
        for row in xrange(self.hgt):
            result.append(''.join(self.used[row * self.wid :
                                  (row + 1) * self.wid]))
        return '\n'.join(result)

    def to_pdf(self, filename, words):
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import cm, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.platypus.paragraph import Paragraph
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.platypus.flowables import Spacer
        
        doc = SimpleDocTemplate(filename, pagesize=A4)
        data = [self.data[x: x + self.wid] for x in range(0, len(self.data), self.wid)]
        l = cm * 1.25
        t=Table(data, len(data[0]) * [l], len(data) * [l])
        t.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
                               ('VALIGN',(0,0),(-1,-1),'TOP'),
                               ('BOX', (0,0), (-1,-1), 1, colors.black),
                               ('FONTSIZE', (0,0), (-1,-1), 20)
                               ]))
        style = ParagraphStyle(
            'default',
            fontName='Times-Roman',
            fontSize=18,
            leading=18,
            spaceBefore=10,
            spaceAfter=10,
            bulletFontName='Times-Roman',
            bulletFontSize=18,
            bulletIndent=0,
        )
        elements = [Paragraph(FIND_THE_WORDS, style, None)]
        elements.append(Paragraph(", ".join(words), style))
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(t)
        style.fontSize = 12
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(Paragraph(BOTTOM_TEXT, style, None))
        doc.build(elements)

    def pick_word_pos(self, wordlen, directions):
        xd, yd = random.choice(directions)
        minx = (wordlen - 1, 0, 0)[xd + 1]
        maxx = (self.wid - 1, self.wid - 1, self.wid - wordlen)[xd + 1]
        miny = (wordlen - 1, 0, 0)[yd + 1]
        maxy = (self.hgt - 1, self.hgt - 1, self.hgt - wordlen)[yd + 1]
        x = random.randint(minx, maxx)
        y = random.randint(miny, maxy)
        return x, y, xd, yd

    def write_word(self, word, ox, oy, xd, yd):
        x, y = ox, oy
        for c in word:
            p = x + self.wid * y
            e = self.data[p]
            if e != '.' and e != c:
                return False
            x += xd
            y += yd

        x, y = ox, oy
        for c in word:
            p = x + self.wid * y
            self.data[p] = c
            self.used[p] = '.'
            x += xd
            y += yd

        return True

    def place_words(self, words, directions, tries=100):
        # Sort words into descending order of length
        words = list(words)
        words.sort(key = lambda x: len(x), reverse = True)

        for word in words:
            wordlen = len(word)
            while True:
                x, y, xd, yd = self.pick_word_pos(wordlen, directions)
                if self.write_word(word, x, y, xd, yd):
                    self.words.append((word, x, y, xd, yd))
                    break
                tries -= 1
                if tries <= 0:
                    return False
        return True

    def fill_in_letters(self):
        for p in xrange(self.wid * self.hgt):
            if self.data[p] == '.':
                self.data[p] = random.choice(letters)

    def remove_bad_words(self):
        return True

def make_grid(stylep="standard", words=[], tries=100):
    # Parse and validate the style parameter.
    size, directions = styles.get(stylep, (stylep, all_directions))
    size = size.split('x')
    if len(size) != 2:
        raise ValueError("Invalid style parameter: %s" % stylep)
    try:
        wid, hgt = map(int, size)
    except ValueError:
        raise ValueError("Invalid style parameter: %s" % stylep)

    directions = [(dirconv[direction[0]], dirconv[direction[1]])
                  for direction in directions]

    while True:
        while True:
            grid = Grid(wid, hgt)
            if grid.place_words(words, directions):
                break
            tries -= 1
            if tries <= 0:
                return None

        grid.fill_in_letters()
        if grid.remove_bad_words():
            return grid

        tries -= 1
        if tries <= 0:
            return None

if __name__ == '__main__':
    import sys
    random.seed()
    words = sys.argv[2:]
    grid = make_grid(sys.argv[1], ["".join(w.lower().split()) for w in words])
    if grid is None:
        print "Can't make a grid"
    else:
        print grid.to_text()
        print
        print grid.used_to_text()
    grid.to_pdf(words[0] + ".pdf", words)
