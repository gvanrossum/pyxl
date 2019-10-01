# coding: pyxl

from pyxl import html

# Only testing that this produces valid code
def f(self):
   x = <ul class="something">{x for x in range(10)}</ul>
   y = <ul class="something">{x
                           for x in range(10)}</ul>

   z = <ul class="something">{(x)for(x) in range(10)}</ul>

   # These *shouldn't* get parens
   w = <ul class="something">{(x for x in range(10))}</ul>
   w = <ul class="something">{[x for x in range(10)]}</ul>
