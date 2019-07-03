from pyxl.codec.register_invertible import pyxl_encode, pyxl_decode

import os

dir_path = os.path.dirname(os.path.abspath(__file__))

def _roundtrip(file_name):
    path = os.path.join(dir_path, file_name)
    with open(path, "rb") as f:
        contents = f.read()
        assert contents == pyxl_encode(pyxl_decode(contents)[0])[0], (
            "Could not round-trip file %s" % file_name)

# TODO: it would be better if each file was automatically a separate test case...
def test_error_cases():
    cases = os.listdir(dir_path)
    for file_name in cases:
        if file_name.endswith('.py'):
            _roundtrip(file_name)
