import shutil
import sys
import os.path
from distutils.sysconfig import get_python_lib

python_lib = get_python_lib()
if len(sys.argv) > 1 and sys.argv[1] == '--invertible':
    shutil.copy('pyxl_invertible.pth', os.path.join(python_lib, 'pyxl.pth'))
else:
    shutil.copy('pyxl.pth', python_lib)
