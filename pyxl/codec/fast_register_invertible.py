import codecs

def search_function(encoding):
    if encoding != 'pyxl':
        return None
    import pyxl.codec.register_invertible
    return pyxl.codec.register_invertible.search_function(encoding)

codecs.register(search_function)
