import numpy as np
from pprint import pprint

def rects_of_color(arr, index, color):
    coords = np.where(arr == index)
    coords = zip(coords[1], coords[0])

    return [{'type': 'rect', 'color': color, 'coords': ((c[0], c[1]), (c[0]+1, c[1]+1))} for c in coords]
