# coding: pyxl
import unittest2
from pyxl import html
from pyxl.base import PyxlException, x_base
from pyxl.element import x_element

class PyxlTests(unittest2.TestCase):

    def test_basics(self):
        self.assertEqual(<div />.to_string(), '<div></div>')
        self.assertEqual(<img src="blah" />.to_string(), '<img src="blah" />')
        self.assertEqual(<div class="c"></div>.to_string(), '<div class="c"></div>')
        self.assertEqual(<div><span></span></div>.to_string(), '<div><span></span></div>')
        self.assertEqual(<frag><span /><span /></frag>.to_string(), '<span></span><span></span>')

    def test_escaping(self):
        self.assertEqual(<div class="&">&{'&'}</div>.to_string(), '<div class="&amp;">&&amp;</div>')
        self.assertEqual(<div>{html.rawhtml('&')}</div>.to_string(), '<div>&</div>')

    def test_comments(self):
        pyxl = (
            <div
                class="blah" # attr comment
                >  # comment1
                <!-- comment2 -->
                text# comment3
                # comment4
            </div>)
        self.assertEqual(pyxl.to_string(), '<div class="blah">text</div>')

    def test_cond_comment(self):
        s = 'blahblah'
        self.assertEqual(
            <cond_comment cond="lt IE 8"><div class=">">{s}</div></cond_comment>.to_string(),
            '<!--[if lt IE 8]><div class="&gt;">blahblah</div><![endif]-->')
        self.assertEqual(
            <cond_comment cond="(lt IE 8) & (gt IE 5)"><div>{s}</div></cond_comment>.to_string(),
            '<!--[if (lt IE 8) & (gt IE 5)]><div>blahblah</div><![endif]-->')

    def test_decl(self):
        self.assertEqual(
            <script><![CDATA[<div><div>]]></script>.to_string(),
            '<script><![CDATA[<div><div>]]></script>')

    def test_form_error(self):
        self.assertEqual(
            <form_error name="foo" />.to_string(),
            '<form:error name="foo" />')

    def test_enum_attrs(self):
        class x_foo(x_base):
            __attrs__ = {
                'value': ['a', 'b'],
            }

            def _to_list(self, l):
                pass

        self.assertEqual(<foo />.attr('value'), 'a')
        self.assertEqual(<foo />.value, 'a')
        self.assertEqual(<foo value="b" />.attr('value'), 'b')
        self.assertEqual(<foo value="b" />.value, 'b')
        with self.assertRaises(PyxlException):
            <foo value="c" />

        class x_bar(x_base):
            __attrs__ = {
                'value': ['a', None, 'b'],
            }

            def _to_list(self, l):
                pass

        with self.assertRaises(PyxlException):
            <bar />.attr('value')

        with self.assertRaises(PyxlException):
            <bar />.value

        class x_baz(x_base):
            __attrs__ = {
                'value': [None, 'a', 'b'],
            }

            def _to_list(self, l):
                pass

        self.assertEqual(<baz />.value, None)

    def test_render_args_are_added_to_pyxl_attributes(self):

        class x_foo(x_element):
            def render(self, value: int):
                return <span>{value}</span>

        self.assertEqual(<foo />.value, None)
        self.assertEqual(<foo value="10" />.value, 10)
        with self.assertRaises(PyxlException):
            <foo value="boo" />.value

        self.assertEqual(<foo value="11" />.to_string(), '<span>11</span>') 

    def test_render_arg_supports_enum(self):

        class x_foo(x_element):
            def render(self, value: ['a', 'b']):
                return <span>{value}</span>

        self.assertEqual(<foo />.value, 'a')
        self.assertEqual(<foo value="b" />.value, 'b')
        with self.assertRaises(PyxlException):
            <foo value="c" />.value

    def test_render_arg_without_annotation(self):

        class x_foo(x_element):
            def render(self, value):
                return <span>{value}</span>

        self.assertEqual(<foo />.to_string(), '<span></span>')
        self.assertEqual(<foo value="123" />.to_string(), '<span>123</span>')
        self.assertEqual(<foo value="boo" />.to_string(), '<span>boo</span>')

    def test_underscore_in_render_arg(self):

        class x_foo(x_element):
            def render(self, a_b_c: int):
                return <span>{a_b_c}</span>

        self.assertEqual(<foo a_b_c="1" />.to_string(), '<span>1</span>')

    def test_attr_collision(self):

        with self.assertRaises(PyxlException):

            class x_foo(x_element):

                __attrs__ = {
                    'laughing': object
                }

                def render(self, laughing):
                    pass

if __name__ == '__main__':
    unittest2.main()
