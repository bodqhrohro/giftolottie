from pprint import pprint

def scale(shapes, ratio):
    newShapes = []
    for shape in shapes:
        newShape = dict(shape)
        newShape['coords'] = [(c[0] * ratio, c[1] * ratio) for c in shape['coords']]
        newShapes.append(newShape)

    return newShapes
