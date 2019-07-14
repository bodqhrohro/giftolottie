#!/usr/bin/env python

import sys
import os
from subprocess import run
from tempfile import NamedTemporaryFile

import vendor.gif2numpy
import numpy as np

from pprint import pprint

from utils.rect import rects_of_color
from utils.scale import scale
from export.svg import save as svg_save
from export.tgs import save as tgs_save

tmpfile = NamedTemporaryFile(delete=False)
run(["gifsicle", "-U", sys.argv[1]], stdout=tmpfile)
tmpfile.close()

frames, exts, image_specs = vendor.gif2numpy.convert(tmpfile.name, BGR2RGB=False)

os.remove(tmpfile.name)

colors = image_specs['Color table values']
size = image_specs['Image Size']

processed_frames = []

for i, frame in enumerate(frames):
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

    all_rects = []
    for color in colors:
        if color == (254, 0, 254):
            continue

        rects = rects_of_color(frame, color)

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

    sizeX, sizeY = size
    ratio = (512 / sizeY) if sizeX < sizeY else (512 / sizeX)
    all_rects = scale(all_rects, ratio)

    for rect in all_rects:
        rect['startFrame'] = i
        rect['endFrame'] = i

    svg_save(all_rects, "/tmp/smile%s.svg" % i)

    processed_frames.append(all_rects)

for i in range(len(processed_frames) - 1, 0, -1):
    frame = processed_frames[i]
    prev_frame = processed_frames[i - 1]
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

tgs_save(processed_frames, sys.argv[2])
