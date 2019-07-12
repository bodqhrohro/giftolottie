import svgwrite

def save(shapes, name):
    svg = svgwrite.Drawing(filename = name, size = ("512px", "512px"))

    for shape in shapes:
        if shape['type'] == 'rect':
            svg.add(svg.rect(
                insert = (str(shape['coords'][0][0]) + "px", str(shape['coords'][0][1]) + "px"),
                size = (
                    str(shape['coords'][1][0] - shape['coords'][0][0]) + "px",
                    str(shape['coords'][1][1] - shape['coords'][0][1]) + "px",
                ),
                #stroke_width = "0",
                fill = "rgb(" + ",".join(map(str, shape['color'])) + ")"
            ))

    svg.save()
