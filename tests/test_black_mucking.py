# coding: pyxl
import html
class A:
    def foo():
        lol = (<test_thing
                  test_something_whatever={{"initialsomething": initialsomething,
                                            "thisisirritating": lurrrr,
                                            "whatever": whatever,}}
              />)

        foo = (<test_thing
                  test_something_whatever={["initialsomething",
                                            "thisisirritating",
                                            "whatever",
                                            "more args",
                  ]}
              />)

        baz = (<test_thing
                  test_something_whatever={foo("initialsomething",
                                               "thisisirritating",
                                               "whatever",
                                               "more args",
                                               "again",
                                               "asdf",)}
              />)

        lol("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", <foo>
                                                            <bar />
                                                        </foo>)

        return (
            <foo>
                <bar baz="{baz}" spam="{spam}" eggs="{eggs}" />
            </foo>
        )
