# Test that black commutes with the pyxl encoder.
# This test is pretty fragile since it uses black internals
# It was tested on black 19.3b0.

import os
import pytest

from pyxl.codec.transform import pyxl_transform_string, pyxl_invert_string

dir_path = os.path.dirname(os.path.abspath(__file__))

def _black_roundtrip(path):
    import black

    with open(path, "r", encoding='utf8') as f:
        contents = f.read()

    # Run black on the file. We manually encode and decode ourselves
    # to avoid needing to make black find the right codec.
    mode = black.FileMode()
    output = pyxl_invert_string(
        black.format_str(pyxl_transform_string(contents, invertible=True), mode=mode)
    )

    # Now we decode both versions with the traditional codec and compare.
    orig_pyxl = pyxl_transform_string(contents, invertible=False)
    new_pyxl = pyxl_transform_string(output, invertible=False)

    black.assert_equivalent(orig_pyxl, new_pyxl)

# TODO: it would be better if each file was automatically a separate test case...
def test_black_commute():
    try:
        import black
    except ImportError:
        pytest.skip()

    cases = os.listdir(dir_path)
    for file_name in cases:
        if file_name.endswith('.py'):
            _black_roundtrip(os.path.join(dir_path, file_name))
