#!/usr/bin/env python


import codecs, encodings
import sys
from pyxl.codec.transform import pyxl_decode, PyxlIncrementalDecoder, PyxlStreamReader


def search_function(encoding):
    if encoding != 'pyxl': return None
    # Assume utf8 encoding
    utf8=encodings.search_function('utf8')
    return codecs.CodecInfo(
        name = 'pyxl',
        encode = utf8.encode,
        decode = pyxl_decode,
        incrementalencoder = utf8.incrementalencoder,
        incrementaldecoder = PyxlIncrementalDecoder,
        streamreader = PyxlStreamReader,
        streamwriter = utf8.streamwriter)


# This import will do the actual registration with codecs
import pyxl.codec.fast_register

_USAGE = """\
Wraps a python command to allow it to recognize pyxl-coded files with
no source modifications.

Usage:
    python -m pyxl.codec.register -m module.to.run [args...]
    python -m pyxl.codec.register path/to/script.py [args...]
"""

if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == '-m':
        mode = 'module'
        module = sys.argv[2]
        del sys.argv[1:3]
    elif len(sys.argv) >= 2:
        mode = 'script'
        script = sys.argv[1]
        sys.argv = sys.argv[1:]
    else:
        print(_USAGE, file=sys.stderr)
        sys.exit(1)

    if mode == 'module':
        import runpy
        runpy.run_module(module, run_name='__main__', alter_sys=True)
    elif mode == 'script':
        with open(script) as f:
            global __file__
            __file__ = script
            # Use globals as our "locals" dictionary so that something
            # that tries to import __main__ (e.g. the unittest module)
            # will see the right things.
            exec(f.read(), globals(), globals())
