#!/usr/bin/env python


import sys
from pyxl.codec.transform import pyxl_reverse_string, pyxl_transform_string


if __name__ == '__main__':
    if sys.argv[1] == '-r':
        invert = True
        fname = sys.argv[2]
    else:
        invert = False
        fname = sys.argv[1]
    with open(fname, 'r') as f:
        contents = f.read()
        if invert:
            print(pyxl_reverse_string(contents), end='')
        else:
            print(pyxl_transform_string(contents, invertible=True), end='')
