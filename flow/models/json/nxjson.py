
__all__ = ['dump','dumps','load','loads', 'node_link_data']

import json
from . import default_json_encoder

from networkx.readwrite.json_graph import node_link_data
from networkx.readwrite.json_graph import node_link_graph

class NXJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        obj = default_json_encoder(obj)
        return node_link_data(obj)


class NXJSONDecoder(json.JSONDecoder):
    def decode(self, s):
        d = loads(s)
        return node_link_graph(d)


from functools import wraps
def nxjson_wrap_output(f):
    # if config.DEBUG: indent, prettyprint
    # else
    nxjsonkwargs = dict(cls=NXJSONEncoder,
            ensure_ascii=False,
            separators=(',',':'),
            encoding='utf-8',
    )
    @wraps(f)
    def wrapper(*args, **kwargs):
        kwargs.update(nxjsonkwargs)
        return f(*args, **kwargs)
    return wrapper

def nxjson_wrap_input(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        kwargs['cls'] = NXJSONEncoder
        return f(*args, **kwargs)
    return wrapper

dump = nxjson_wrap_output(json.dump)
dumps = nxjson_wrap_output(json.dumps)
load = nxjson_wrap_input(json.load)
loads = nxjson_wrap_input(json.loads)
