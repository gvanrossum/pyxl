#!/usr/bin/env python


import codecs, io, encodings
import sys
import traceback
from encodings import utf_8
from pyxl.codec.tokenizer_invertible import pyxl_reverse_tokenize, pyxl_tokenize, pyxl_untokenize

def pyxl_transform(stream):
    try:
        output = pyxl_untokenize(pyxl_tokenize(stream.readline))
    except Exception as ex:
        print(ex)
        traceback.print_exc()
        raise

    return output.rstrip()

def pyxl_reverse(stream):
    try:
        output = pyxl_untokenize(pyxl_reverse_tokenize(stream.readline))
    except Exception as ex:
        print(ex)
        traceback.print_exc()
        raise

    return output.rstrip()

def pyxl_transform_string(input):
    stream = io.StringIO(bytes(input).decode('utf-8'))
    return pyxl_transform(stream)

def pyxl_reverse_string(input):
    stream = io.StringIO(input)
    return pyxl_reverse(stream)

def pyxl_encode(input, errors='strict'):
    return pyxl_reverse_string(input), len(input)

def pyxl_decode(input, errors='strict'):
    return pyxl_transform_string(input), len(input)

class PyxlIncrementalDecoder(utf_8.IncrementalDecoder):
    def decode(self, input, final=False):
        self.buffer += input
        if final:
            buff = self.buffer
            self.buffer = b''
            return super(PyxlIncrementalDecoder, self).decode(
                pyxl_transform_string(buff).encode('utf-8'), final=True)
        else:
            return ''

class PyxlIncrementalEncoder(utf_8.IncrementalEncoder):
    def encode(self, input, final=False):
        self.buffer += input
        if final:
            buff = self.buffer
            self.buffer = u''
            return super(PyxlIncrementalEncoder, self).encode(
                pyxl_reverse_string(buff), final=True)
        else:
            return b''


class PyxlStreamReader(utf_8.StreamReader):
    def __init__(self, *args, **kwargs):
        codecs.StreamReader.__init__(self, *args, **kwargs)
        self.stream = io.StringIO(pyxl_transform(self.stream))


class PyxlStreamWriter(utf_8.StreamWriter):
    def __init__(self, *args, **kwargs):
        codecs.StreamReader.__init__(self, *args, **kwargs)
        self.stream = io.StringIO(pyxl_reverse(self.stream))

def search_function(encoding):
    if encoding != 'pyxl': return None
    # Assume utf8 encoding
    utf8=encodings.search_function('utf8')
    return codecs.CodecInfo(
        name = 'pyxl',
        encode = pyxl_encode,
        decode = pyxl_decode,
        incrementalencoder = PyxlIncrementalEncoder,
        incrementaldecoder = PyxlIncrementalDecoder,
        streamreader = PyxlStreamReader,
        streamwriter = utf8.streamwriter)


codecs.register(search_function)

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
            print(pyxl_reverse_string(contents.decode('utf-8')))
        else:
            print(pyxl_transform_string(contents))
