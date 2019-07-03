# coding: pyxl

# I test interactions with black manually with
# cp tests/test_black_mucking.py /tmp/out.py; black /tmp/out.py && cat /tmp/out.py
# and spot checking the result to make sure I like it.

import html
class A:
    def foo():
        lol = (<test_thing
                  test_something_whatever={{"aaaaaaaaaaaaaaaa": aaaaaaaaaaaaaaaa,
                                            "bbbbbbbbbbbbbbbb": lurrrr,
                                            "whatever": whatever,}}
               />)

        # Unfortunately black doesn't understand the real column
        # positions so does not wrap this
        foo = (<test_thing
                  test_something_whatever={["initialsomething",
                                            "bbbbbbbbbbbbbbbb",
                                            "whatever",
                                            "more args",]}
               />)

        baz = (<test_thing
                  test_something_whatever={foo("initialsomething",
                                               "bbbbbbbbbbbbbbbb",
                                               "whatever",
                                               "more args",
                                               "again",
                                               "asdf",)}
               />)

        lol("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", <foo>
                                                            <bar />
                                                        </foo>)

        a = (<testing>
                hello {world}
             </testing>)

        b = (<testing>
                 hello {{"initialsomething": initialsomething,
                         "bbbbbbbbbbbbbbbb": lurrrr,
                         "whatever": whatever,}} world
             </testing>)

        indented_annoyingly = <frag>
            this is very popular...
        </frag>

        return (
            <foo>
                <bar baz="{baz}" spam="{spam}" eggs="{eggs}" />
            </foo>
        )
