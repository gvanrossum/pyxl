from pyxl.codec.transform import pyxl_transform_string, pyxl_reverse_string

import os

dir_path = os.path.dirname(os.path.abspath(__file__))

def _roundtrip(file_name):
    path = os.path.join(dir_path, file_name)
    with open(path, "r") as f:
        contents = f.read()
        depyxled = pyxl_transform_string(contents, invertible=True)
        assert contents == pyxl_reverse_string(depyxled), (
            "Could not round-trip file %s" % file_name)

# TODO: it would be better if each file was automatically a separate test case...
def test_error_cases():
    cases = os.listdir(dir_path)
    for file_name in cases:
        if file_name.endswith('.py'):
            _roundtrip(file_name)
