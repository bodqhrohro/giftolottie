import gzip
import json

FPS = 60
MAX_DURATION = FPS * 3

def frame_to_duration(frame, exts, end = False):
    duration = 0
    frame_count = frame + 1 if end else frame
    for i in range(frame_count):
        duration += exts[i]['delay_time']
    return duration

def gif_duration_to_fr(duration, scale_factor):
    return duration / 100.0 * FPS / scale_factor

def save(frames, name, exts):
    duration = 0
    for ext in exts:
        duration += ext['delay_time']
    scale_factor = 1.0 if duration < MAX_DURATION else duration / MAX_DURATION

    tree = {
        'tgs': 1,
        'v': '5.5.2',
        'fr': FPS,
        'ip': 0,
        'op': round(gif_duration_to_fr(duration, scale_factor)) - 1,
        'w': 512,
        'h': 512,
        'nm': '',
        'ddd': 0,
        'assets': [],
        'comps': [],
    }

    frame_seqs = []
    for frame in frames:
        for shape in frame:
            is_seq_exists = False
            for frame_seq in frame_seqs:
                if frame_seq[0]['startFrame'] == shape['startFrame'] \
                        and frame_seq[0]['endFrame'] == shape['endFrame']:
                    frame_seq.append(shape)
                    is_seq_exists = True
                    break
            if not is_seq_exists:
                frame_seqs.append([shape])
                

    tree['layers'] = [frame_seq_to_layer(frame_seq, exts, scale_factor) for frame_seq in frame_seqs]

    json_tree = json.dumps(tree)
    json_bytes = json_tree.encode('utf-8')

    with gzip.open(name, 'wb') as f:
        f.write(json_bytes)


def shape_to_tgs(shape):
    tgs_shape = {
        'ty': 'gr',
        'nm': '',
        'bm': 0,
    }

    size_x = shape['coords'][1][0] - shape['coords'][0][0]
    size_y = shape['coords'][1][1] - shape['coords'][0][1]

    center_x = shape['coords'][0][0] + size_x / 2
    center_y = shape['coords'][0][1] + size_y / 2

    tgs_shape['it'] = [
        {
            'ty': 'rc',
            'nm': '',
            'd': 1,
            'p': {
                'k': (center_x, center_y)
            },
            's': {
                'k': (size_x, size_y)
            },
            'r': { 'k': 0 },
        },
        {
            'ty': 'fl',
            'nm': '',
            'c': {
                'a': 0,
                'k': [
                    round(shape['color'][0] / 255, 3),
                    round(shape['color'][1] / 255, 3),
                    round(shape['color'][2] / 255, 3),
                    255,
                ],
            },
            'o': {
                'a': 0,
                'k': 100,
            },
            'r': 1,
            'bm': 0,
        },
        {
            'ty': 'tr',
            'o': {
                'a': 0,
                'k': 100,
            },
            'r': {
                'a': 0,
                'k': 0,
            },
            'p': {
                'a': 0,
                'k': [0, 0, 0],
            },
            'a': {
                'a': 0,
                'k': [0, 0, 0],
            },
            's': {
                'a': 0,
                'k': [100, 100, 100],
            },
            'nm': '',
        },
    ]

    return tgs_shape

def frame_seq_to_layer(frame_seq, exts, scale_factor):
    ref_shape = frame_seq[0]
    layer = {
        'ty': 4,
        'ks': {
            'o': {
                'a': 0,
                'k': 100,
            },
            'r': {
                'a': 0,
                'k': 0,
            },
            'p': {
                'a': 0,
                'k': [0, 0, 0],
            },
            'a': {
                'a': 0,
                'k': [0, 0, 0],
            },
            's': {
                'a': 0,
                'k': [100, 100, 100],
            },
        },
        'ao': 0,
        'ddd': 0,
        'ip': round(gif_duration_to_fr(frame_to_duration(ref_shape['startFrame'], exts), scale_factor)),
        'op': round(gif_duration_to_fr(frame_to_duration(ref_shape['endFrame'], exts, end = True), scale_factor)) + 1,
        'sr': 1,
        'nm': '',
    }
    layer['st'] = layer['ip']
    layer['shapes'] = [shape_to_tgs(shape) for shape in frame_seq]

    return layer
