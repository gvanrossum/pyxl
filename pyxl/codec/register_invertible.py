#!/usr/bin/env python


import codecs, io, encodings
import sys
import traceback
from encodings import utf_8
from pyxl.codec.transform import (
    pyxl_encode, pyxl_decode, PyxlIncrementalDecoderInvertible, PyxlIncrementalEncoder,
    PyxlStreamReaderInvertible, PyxlStreamWriter,
)


def search_function(encoding):
    if encoding != 'pyxl': return None
    # Assume utf8 encoding
    utf8=encodings.search_function('utf8')
    return codecs.CodecInfo(
        name = 'pyxl',
        encode = pyxl_encode,
        decode = lambda b: pyxl_decode(b, invertible=True),
        incrementalencoder = PyxlIncrementalEncoder,
        incrementaldecoder = PyxlIncrementalDecoderInvertible,
        streamreader = PyxlStreamReaderInvertible,
        streamwriter = PyxlStreamWriter,
    )


# This import will do the actual registration with codecs
import pyxl.codec.fast_register_invertible

if __name__ == '__main__':
    if sys.argv[1] == '-r':
        invert = True
        fname = sys.argv[2]
    else:
        invert = False
        fname = sys.argv[1]
    with open(fname, 'rb') as f:
        contents = f.read()
        if invert:
            print(pyxl_reverse_string(contents.decode('utf-8')).decode('utf-8'), end='')
        else:
            print(pyxl_transform_string(contents), end='')
