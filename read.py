#!/usr/bin/env python

import sys
from PIL import Image, ImageSequence
import numpy as np

from pprint import pprint

from utils.rect import rects_of_color
from utils.scale import scale
from export.svg import save as svg_save
from export.tgs import save as tgs_save

frames = []
i = 0
for frame in ImageSequence.Iterator(im):
    indexed = np.array(frame)

    palette = frame.getpalette()
    colors = []
    color = []

    for comp in palette:
        color.append(comp)
        if len(color) >= 3:
            colors.append(color)
            color = []

    # dedup
    """
    i = 0
    while i < len(colors):
        color = colors[i]
        if color in colors[(i+1):]:
            colors.pop(i)
        else:
            i = i + 1
    """

    stats = frame.getcolors()
    stats.sort(key=lambda i: i[0], reverse=True)
        
    all_rects = []
    for stat in stats[1:]:
        index = stat[1]
        color = colors[index]
        rects = rects_of_color(indexed, index, color)

        rects.sort(key=lambda rect: rect['coords'][0])
        runs = []
        for rect in rects:
            is_included_in_run = False
            if rect['coords'][0][0] != 0:
                for run in runs:
                    if run['coords'][1][0] == rect['coords'][0][0] \
                            and run['coords'][0][1] == rect['coords'][0][1]:
                        run['coords'] = (run['coords'][0], rect['coords'][1])
                        is_included_in_run = True
            if not is_included_in_run:
                runs.append(rect)

        all_rects.extend(runs)

    sizeX = frame.size[0]
    sizeY = frame.size[1]
    ratio = (512 / sizeY) if sizeX < sizeY else (512 / sizeX)
    all_rects = scale(all_rects, ratio)

    for rect in all_rects:
        rect['startFrame'] = i
        rect['endFrame'] = i

    svg_save(all_rects, "/tmp/smile%s.svg" % i)

    frames.append(all_rects)

    i = i + 1

for i in range(len(frames) - 1, 0, -1):
    frame = frames[i]
    prev_frame = frames[i - 1]
    for shape in frame:
        if shape['type'] == 'rect':
            for prev_shape in prev_frame:
                if prev_shape['type'] == 'rect' \
                    and prev_shape['coords'] == shape['coords'] \
                    and prev_shape['color'] == shape['color'] \
                    and shape['startFrame'] == prev_shape['endFrame'] + 1:
                        prev_shape['endFrame'] = shape['endFrame']
                        frame.remove(shape)
                        break

tgs_save(frames, sys.argv[2])
