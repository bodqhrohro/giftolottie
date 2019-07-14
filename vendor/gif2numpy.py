 #!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import numpy as np
import os
from pkg_resources import parse_version
from kaitaistruct import __version__ as ks_version, KaitaiStruct, KaitaiStream, BytesIO
from enum import Enum
from builtins import bytes
version = "1.3"

"""
Version history:
1.3: Additional flag for BGR2RGB conversion, by default this flag is set and a BGR2RGB color conversion 
     takes place, better time optimization of color table mapping
1.2: Bug fix for multiple frame gif images, pixel error in frames fixed
1.1: single frame and multiple frame gif images are now supported
1.0: first release just for still single images
"""

if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))

class Gif(KaitaiStruct):
    """GIF (Graphics Interchange Format) is an image file format, developed
    in 1987. It became popular in 1990s as one of the main image formats
    used in World Wide Web.
    
    GIF format allows encoding of palette-based images up to 256 colors
    (each of the colors can be chosen from a 24-bit RGB
    colorspace). Image data stream uses LZW (Lempel–Ziv–Welch) lossless
    compression.
    
    Over the years, several version of the format were published and
    several extensions to it were made, namely, a popular Netscape
    extension that allows to store several images in one file, switching
    between them, which produces crude form of animation.
    
    Structurally, format consists of several mandatory headers and then
    a stream of blocks follows. Blocks can carry additional
    metainformation or image data.
    """

    class BlockType(Enum):
        extension = 33
        local_image_descriptor = 44
        end_of_file = 59

    class ExtensionLabel(Enum):
        graphic_control = 249
        comment = 254
        application = 255

    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.hdr = self._root.Header(self._io, self, self._root)
        self.logical_screen_descriptor = self._root.LogicalScreenDescriptorStruct(self._io, self, self._root)
        if self.logical_screen_descriptor.has_color_table:
            self._raw_global_color_table = self._io.read_bytes((self.logical_screen_descriptor.color_table_size * 3))
            io = KaitaiStream(BytesIO(self._raw_global_color_table))
            self.global_color_table = self._root.ColorTable(io, self, self._root)

        self.blocks = []
        i = 0
        while True:
            _ = self._root.Block(self._io, self, self._root)
            self.blocks.append(_)
            if  ((self._io.is_eof()) or (_.block_type == self._root.BlockType.end_of_file)) :
                break
            i += 1

    class ImageData(KaitaiStruct):
        """
        .. seealso::
           - section 22 - https://www.w3.org/Graphics/GIF/spec-gif89a.txt
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.lzw_min_code_size = self._io.read_u1()
            self.subblocks = self._root.Subblocks(self._io, self, self._root)


    class ColorTableEntry(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.red = self._io.read_u1()
            self.green = self._io.read_u1()
            self.blue = self._io.read_u1()


    class LogicalScreenDescriptorStruct(KaitaiStruct):
        """
        .. seealso::
           - section 18 - https://www.w3.org/Graphics/GIF/spec-gif89a.txt
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.screen_width = self._io.read_u2le()
            self.screen_height = self._io.read_u2le()
            self.flags = self._io.read_u1()
            self.bg_color_index = self._io.read_u1()
            self.pixel_aspect_ratio = self._io.read_u1()

        @property
        def has_color_table(self):
            if hasattr(self, '_m_has_color_table'):
                return self._m_has_color_table if hasattr(self, '_m_has_color_table') else None

            self._m_has_color_table = (self.flags & 128) != 0
            return self._m_has_color_table if hasattr(self, '_m_has_color_table') else None

        @property
        def color_table_size(self):
            if hasattr(self, '_m_color_table_size'):
                return self._m_color_table_size if hasattr(self, '_m_color_table_size') else None

            self._m_color_table_size = (2 << (self.flags & 7))
            return self._m_color_table_size if hasattr(self, '_m_color_table_size') else None


    class LocalImageDescriptor(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.left = self._io.read_u2le()
            self.top = self._io.read_u2le()
            self.width = self._io.read_u2le()
            self.height = self._io.read_u2le()
            self.flags = self._io.read_u1()
            if self.has_color_table:
                self._raw_local_color_table = self._io.read_bytes((self.color_table_size * 3))
                io = KaitaiStream(BytesIO(self._raw_local_color_table))
                self.local_color_table = self._root.ColorTable(io, self, self._root)

            self.image_data = self._root.ImageData(self._io, self, self._root)

        @property
        def has_color_table(self):
            if hasattr(self, '_m_has_color_table'):
                return self._m_has_color_table if hasattr(self, '_m_has_color_table') else None

            self._m_has_color_table = (self.flags & 128) != 0
            return self._m_has_color_table if hasattr(self, '_m_has_color_table') else None

        @property
        def has_interlace(self):
            if hasattr(self, '_m_has_interlace'):
                return self._m_has_interlace if hasattr(self, '_m_has_interlace') else None

            self._m_has_interlace = (self.flags & 64) != 0
            return self._m_has_interlace if hasattr(self, '_m_has_interlace') else None

        @property
        def has_sorted_color_table(self):
            if hasattr(self, '_m_has_sorted_color_table'):
                return self._m_has_sorted_color_table if hasattr(self, '_m_has_sorted_color_table') else None

            self._m_has_sorted_color_table = (self.flags & 32) != 0
            return self._m_has_sorted_color_table if hasattr(self, '_m_has_sorted_color_table') else None

        @property
        def color_table_size(self):
            if hasattr(self, '_m_color_table_size'):
                return self._m_color_table_size if hasattr(self, '_m_color_table_size') else None

            self._m_color_table_size = (2 << (self.flags & 7))
            return self._m_color_table_size if hasattr(self, '_m_color_table_size') else None


    class Block(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.block_type = self._root.BlockType(self._io.read_u1())
            _on = self.block_type
            if _on == self._root.BlockType.extension:
                self.body = self._root.Extension(self._io, self, self._root)
            elif _on == self._root.BlockType.local_image_descriptor:
                self.body = self._root.LocalImageDescriptor(self._io, self, self._root)


    class ColorTable(KaitaiStruct):
        """
        .. seealso::
           - section 19 - https://www.w3.org/Graphics/GIF/spec-gif89a.txt
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.entries = []
            i = 0
            while not self._io.is_eof():
                self.entries.append(self._root.ColorTableEntry(self._io, self, self._root))
                i += 1



    class Header(KaitaiStruct):
        """
        .. seealso::
           - section 17 - https://www.w3.org/Graphics/GIF/spec-gif89a.txt
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.magic = self._io.ensure_fixed_contents(b"\x47\x49\x46")
            self.version = (self._io.read_bytes(3)).decode(u"ASCII")


    class ExtGraphicControl(KaitaiStruct):
        """
        .. seealso::
           - section 23 - https://www.w3.org/Graphics/GIF/spec-gif89a.txt
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.block_size = self._io.ensure_fixed_contents(b"\x04")
            self.flags = self._io.read_u1()
            self.delay_time = self._io.read_u2le()
            self.transparent_idx = self._io.read_u1()
            self.terminator = self._io.ensure_fixed_contents(b"\x00")

        @property
        def transparent_color_flag(self):
            if hasattr(self, '_m_transparent_color_flag'):
                return self._m_transparent_color_flag if hasattr(self, '_m_transparent_color_flag') else None

            self._m_transparent_color_flag = (self.flags & 1) != 0
            return self._m_transparent_color_flag if hasattr(self, '_m_transparent_color_flag') else None

        @property
        def user_input_flag(self):
            if hasattr(self, '_m_user_input_flag'):
                return self._m_user_input_flag if hasattr(self, '_m_user_input_flag') else None

            self._m_user_input_flag = (self.flags & 2) != 0
            return self._m_user_input_flag if hasattr(self, '_m_user_input_flag') else None


    class Subblock(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.num_bytes = self._io.read_u1()
            self.bytes = self._io.read_bytes(self.num_bytes)


    class ExtApplication(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.application_id = self._root.Subblock(self._io, self, self._root)
            self.subblocks = []
            i = 0
            while True:
                _ = self._root.Subblock(self._io, self, self._root)
                self.subblocks.append(_)
                if _.num_bytes == 0:
                    break
                i += 1


    class Subblocks(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.entries = []
            i = 0
            while True:
                _ = self._root.Subblock(self._io, self, self._root)
                self.entries.append(_)
                if _.num_bytes == 0:
                    break
                i += 1


    class Extension(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.label = self._root.ExtensionLabel(self._io.read_u1())
            _on = self.label
            if _on == self._root.ExtensionLabel.application:
                self.body = self._root.ExtApplication(self._io, self, self._root)
            elif _on == self._root.ExtensionLabel.comment:
                self.body = self._root.Subblocks(self._io, self, self._root)
            elif _on == self._root.ExtensionLabel.graphic_control:
                self.body = self._root.ExtGraphicControl(self._io, self, self._root)
            else:
                self.body = self._root.Subblocks(self._io, self, self._root)

#================================================================
# Bit-level operations
#================================================================
class BitReader(object):
    '''Reads bits from a byte string'''
    
    __slots__ = [
        "_str",
        "_ptr",
        "_len",
    ]

    #------------------------------------------------
    # Construction
    #------------------------------------------------
    def __init__(self, byte_string):
        '''Initialize the reader with a complete byte string'''
        if not isinstance(byte_string, bytes):
            raise TypeError("Requires bytelike object")
        self._str = bytes(byte_string)
        self._ptr = 0
        self._len = len(byte_string) * 8
    
    #------------------------------------------------
    # Bit operations
    #------------------------------------------------
    def read(self, amount):
        '''Read bits from the byte string and returns int'''
        #--- Initialize indices ---
        byte_start, start = divmod(self._ptr, 8)
        byte_end, end = divmod(min(self._ptr+amount, self._len), 8)
        #Error check
        if byte_start > self._len:
            return 0
        
        #--- Read bits ---
        if byte_start == byte_end:
            #Reading from one byte
            byte = self._str[byte_start]
            if start:
                byte >>= start
            byte &= ~(-1 << (end - start))
            #Adjust pointer
            self._ptr = (byte_end << 3) | end
            bit_str = byte
        else:
            #Reading from many bytes
            bit_str = 0
            bit_index = 0
            i = byte_start
            #Read remaining piece of the start
            if start:
                bit_str |= self._str[i] >> start
                bit_index += (8 - start)
                i += 1
            #Grab entire bytes if necessary
            while i < byte_end:
                bit_str |= (self._str[i] << bit_index)
                bit_index += 8
                i += 1
            #Read beginning piece of end byte
            if end:
                byte = self._str[i] & (~(-1 << end))
                bit_str |= (byte << bit_index)
                bit_index += end
        
        #--- Update pointer ---
        self._ptr = (byte_end << 3) | end
        return bit_str

def cvtColor(image):
    "converts color from BGR to RGB and BGRA to RGBA and vice versa"
    if len(image.shape)>=3:
        np8_image = image.astype(np.uint8)
        if image.shape[2] == 3:
            b, g, r = np.dsplit(np8_image, np8_image.shape[-1])
            return np.dstack([r, g, b])
        elif image.shape[2] == 4:
            b, g, r, a = np.dsplit(np8_image, np8_image.shape[-1])
            return np.dstack([r, g, b, a])
    return image

#================================================================
# LZW compression algorithms
#================================================================
def lzw_decompress(raw_bytes, lzw_min):
    '''Decompress the LZW data and yields output'''
    #Initialize streams
    code_in = BitReader(raw_bytes)
    idx_out = []
    #Set up bit reading
    bit_size = lzw_min + 1
    bit_inc = (1 << (bit_size)) - 1
    #Initialize special codes
    CLEAR = 1 << lzw_min
    END = CLEAR + 1
    code_table_len = END + 1
    #Begin reading codes
    code_last = -1
    while code_last != END:
        #Get the next code id
        code_id = code_in.read(bit_size)
        #Check the next code
        if code_id == CLEAR:
            #Reset size readers
            bit_size = lzw_min + 1
            bit_inc = (1 << (bit_size)) - 1
            code_last = -1
            #Clear the code table
            code_table = [-1] * code_table_len
            for x in range(code_table_len):
                code_table[x] = (x,)
        elif code_id == END:
            #End parsing
            break
        elif code_id < len(code_table) and code_table[code_id] is not None:
            current = code_table[code_id]
            #Table has code_id - output code
            idx_out.extend(current)
            k = (current[0],)
        elif code_last not in (-1, CLEAR, END):
            previous = code_table[code_last]
            #Code not in table
            k = (previous[0],)
            idx_out.extend(previous + k)
        #Check increasing the bit size
        if len(code_table) == bit_inc and bit_size < 12:
            bit_size += 1
            bit_inc = (1 << (bit_size)) - 1
        #Update the code table with previous + k
        if code_last not in (-1, CLEAR, END):
            code_table.append(code_table[code_last] + k)
        code_last = code_id
    return idx_out

def paste(mother, child, x, y):
    "Pastes the numpy image child into the numpy image mother at position (x, y)"
    size = mother.shape
    csize = child.shape
    if y+csize[0]<0 or x+csize[1]<0 or y>size[0] or x>size[1]: return mother
    sel = [int(y), int(x), csize[0], csize[1]]
    csel = [0, 0, csize[0], csize[1]]
    if y<0:
        sel[0] = 0
        sel[2] = csel[2] + y
        csel[0] = -y
    elif y+sel[2]>=size[0]:
        sel[2] = int(size[0])
        csel[2] = size[0]-y
    else:
        sel[2] = sel[0] + sel[2]
    if x<0:
        sel[1] = 0
        sel[3] = csel[3] + x
        csel[1] = -x
    elif x+sel[3]>=size[1]:
        sel[3] = int(size[1])
        csel[3] = size[1]-x
    else:
        sel[3] = sel[1] + sel[3]
    childpart = child[csel[0]:csel[2], csel[1]:csel[3]]
    mother[sel[0]:sel[2], sel[1]:sel[3]] = childpart
    return mother

def convert(gif_filename, BGR2RGB=True):
    """converts an image specified by its filename gif_filename to a numpy image
       if BGR2RGB is True (default) there will also be a color conversion from BGR to RGB"""
    if not os.path.isfile(gif_filename):
        raise IOError("File does not exist")
    frames = []
    frames_specs = []
    image_specs = {}
    gifread = open(gif_filename, "rb")
    raw = gifread.read()
    gifread.close()
    # print(len(raw))
    image_specs["Length"] = len(raw)
    data = Gif(KaitaiStream(BytesIO(raw)))
    # print("Header", data.hdr.magic, data.hdr.version)
    image_specs["Header"] = str(data.hdr.magic).replace("b'", "").strip("'") + " " + str(data.hdr.version)
    lsd = data.logical_screen_descriptor
    image_width = lsd.screen_width
    image_height = lsd.screen_height
    # print("Color table size", repr(lsd.color_table_size), "Has color table", lsd.has_color_table, "Image width", image_width, "image height", image_height, "Flags", lsd.flags, "Background color", lsd.bg_color_index, "Pixel aspect ratio", lsd.pixel_aspect_ratio)
    image_specs["Color table size"] = lsd.color_table_size
    image_specs["Color table existing"] = lsd.has_color_table
    image_specs["Image Size"] = image_width, image_height
    image_specs["Flags"] = lsd.flags
    image_specs["Background Color"] = lsd.bg_color_index
    image_specs["Pixel Aspect Ratio"] = lsd.pixel_aspect_ratio
    # print("Color table length", len(data.global_color_table.entries))
    image_specs["Color table length"] = len(data.global_color_table.entries)
    gcte = data.global_color_table.entries
    color_table = []
    for i in range(len(gcte)):
        color_table.append((gcte[i].red, gcte[i].green, gcte[i].blue))
    # print("Color table values", color_table)
    image_specs["Color table values"] = color_table
    # print(len(data.blocks))
    image_specs["Data Blocks count"]  = len(data.blocks)
    frames = []
    exts = []
    first_frame = True
    for i in range(len(data.blocks)):
        # print("Block_type", data.blocks[i].block_type, "block_count:", i)
        if data.blocks[i].block_type == Gif.BlockType.local_image_descriptor:
            imgdata = data.blocks[i].body.image_data
            left = data.blocks[i].body.left
            top = data.blocks[i].body.top
            width = data.blocks[i].body.width
            height = data.blocks[i].body.height
            flags = data.blocks[i].body.flags
            has_color_table = data.blocks[i].body.has_color_table
            if has_color_table:
                local_color_table = data.blocks[i].body.local_color_table
            lzw_min = imgdata.lzw_min_code_size
            if exts == []:
                exts.append({})
            exts[-1]["left"] = left
            exts[-1]["top"] = top
            exts[-1]["width"] = width
            exts[-1]["height"] = height
            exts[-1]["flags1"] = flags
            exts[-1]["has_color_table"] = has_color_table
            if has_color_table:
                exts[-1]["local_color_table"] = local_color_table
            exts[-1]["lzw_min"] = lzw_min
            all_bytes = b""
            alle = 0
            for j in range(len(imgdata.subblocks.entries)):
                # print(imgdata.subblocks.entries[i].num_bytes, sep=" ", end=", ")
                block_len = imgdata.subblocks.entries[j].num_bytes
                alle = alle + block_len
                # print(len(imgdata.subblocks.entries[i].bytes), repr(imgdata.subblocks.entries[i].bytes))
                all_bytes = all_bytes + imgdata.subblocks.entries[j].bytes
            # print("alle", alle)
            # print(len(all_bytes))
            # print("single frame attr at block no.:", i, left, top, width, height, flags, has_color_table, lzw_min)
            # if has_color_table:
            #     print(local_color_table)
            uncompressed = lzw_decompress(all_bytes, lzw_min)
            np_len = len(uncompressed)
            # print("Uncompressed image: type/length, image_data[:100]", type(uncompressed), np_len, uncompressed[:100])
            if len(color_table[0])==1:
                np_image = np.zeros((np_len), dtype=np.uint8)
                channels = 1
            elif len(color_table[0])==2:
                np_image = np.zeros((np_len*2), dtype=np.uint8)
                channels = 2
            elif len(color_table[0])==3:
                np_image = np.zeros((np_len*3), dtype=np.uint8)
                channels = 3
            elif len(color_table[0])==4:
                np_image = np.zeros((np_len*4), dtype=np.uint8)
                channels = 4
            if has_color_table:
                np_image = np.array([local_color_table[byt] if byt != exts[-1]['transparent_idx'] else (254, 0, 254) for byt in uncompressed])
            else:
                np_image = np.array([color_table[byt] if byt != exts[-1]['transparent_idx'] else (254, 0, 254) for byt in uncompressed])
            # print("image_height, image_width, channels", image_height, image_width, channels)
            np_image = np.reshape(np_image, (height, width, channels))
            # print(np_image.shape, np_image[329-height,329-width,0])
            if BGR2RGB:
                if channels == 3 or channels == 4:
                    np_image = cvtColor(np_image)
                else:
                    np_image = np_image.astype(np.uint8)    
            else:
                np_image = np_image.astype(np.uint8)
            if len(exts) > 1:
                displace_flags = (exts[-2]['flags'] >> 2) & 7
                if displace_flags == 2:
                    first_frame = True
            if first_frame:
                first_frame = False
                frame1 = np_image.copy()
            else:
                old_frame = frames[-1].copy()
                if has_color_table:
                    if BGR2RGB:
                        transp_idx = local_color_table[exts[-1]['transparent_idx']][::-1] # RGB -> BGR
                    else:
                        transp_idx = local_color_table[exts[-1]['transparent_idx']] # RGB -> RGB
                else:
                    if BGR2RGB:
                        transp_idx = color_table[exts[-1]['transparent_idx']][::-1] # RGB -> BGR
                    else:
                        transp_idx = color_table[exts[-1]['transparent_idx']] # RGB -> RGB
                transp_idx = np.array(transp_idx)
                # cv2.imshow("old_frame", old_frame)
                new_frame = paste(frame1.copy(), np_image, exts[-1]['left'], exts[-1]['top'])
                # cv2.imshow("new_frame", new_frame)
                f = np.all((new_frame==transp_idx), axis=-1)
                flattened_image = np.reshape(new_frame, (new_frame.shape[0]*new_frame.shape[1], channels))
                old_flattened_image = np.reshape(old_frame, (old_frame.shape[0]*old_frame.shape[1], channels))
                f = np.reshape(f, (old_frame.shape[0]*old_frame.shape[1], 1))
                np_image = np.array([old_flattened_image[i] if j else flattened_image[i] for i, j in enumerate(f)])
                np_image = np.reshape(np_image, (old_frame.shape[0], old_frame.shape[1], channels))
                # cv2.imshow("last_frame", np_image)
                # cv2.waitKey()
            frames.append(np_image)
        elif data.blocks[i].block_type == Gif.BlockType.extension:
            label = data.blocks[i].body.label
            # print("label of extension", label)
            if label == Gif.ExtensionLabel.graphic_control:
                body = data.blocks[i].body.body
                # print("body, label of extension", body, label)
                block_size = data.blocks[i].body.body.block_size
                flags = data.blocks[i].body.body.flags
                delay_time = data.blocks[i].body.body.delay_time
                transparent_idx = data.blocks[i].body.body.transparent_idx
                terminator = data.blocks[i].body.body.terminator
                frame_count = len(frames)
                ext_dict = {"block_size": block_size, "flags": flags, "delay_time": delay_time, "transparent_idx": transparent_idx, "terminator": terminator}
                exts.append(ext_dict)
                # print(i, "block_size, flags, delay_time, transparent_idx, terminator", block_size, flags, delay_time, transparent_idx, terminator)
            elif label == Gif.ExtensionLabel.application:
                application_id = data.blocks[i].body.body.application_id
                subblocks = data.blocks[i].body.body.subblocks
                image_specs["application_id"] = application_id.bytes 
                for k in range(len(subblocks)):
                    image_specs["application_subblocks"+str(k)] = subblocks[k].bytes
            elif label == Gif.ExtensionLabel.comment:
                subblocks = data.blocks[i].body.body
                image_specs["comment"] = b"".join([b.bytes for b in subblocks.entries])
        else: # data.blocks[i].block_type == Gif.BlockType.end_of_file
            pass
    return frames, exts, image_specs

if __name__ == '__main__':
    import cv2
    images = "Images/hopper.gif", "Images/audrey.gif", "Images/Rotating_earth.gif", "Images/testcolors.gif"
    for image in images:
        frames, exts, image_specs = convert(image)
        print()
        print("Image:", image)
        print()
        print("len frames", len(frames))
        print("len exts", len(exts))
        print("exts:", exts)
        print("image_specs:", image_specs)
        for i in range(len(frames)):
            cv2.imshow("np_image", frames[i])
            print(exts[i])
            k = cv2.waitKey(0) 
            if k == 27: 
                break
            cv2.destroyWindow("np_image")
