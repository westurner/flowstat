import formencode
from pyramid.view import view_config
#from pyramid.httpexceptions import HTTPFound
#from pyramid.httpexceptions import HTTPNotFound
from pyramid_simpleform import Form
from pyramid_simpleform.renderers import FormRenderer

from collections import defaultdict

from pyramid.renderers import render

#import networkx.readwrite.json_graph.serialize as nxjson
from flow.models.json import nxjson as nxjson


#from pyramid_restler.view import RESTfulView

from ..numbers.views import NumberGraphRESTfulView

class GraphsRESTfulView(NumberGraphRESTfulView):
    def render_json(self, value):
        renderer = self._renderers['json']
        return dict(
            body=self.context.to_json(value, self.fields, self.wrap),
            charset=renderer[1],
            content_type=renderer[0][0],
        )

    def render_html(self, value):
        renderer = self._renderers['html']
        return dict(
            body=render('graphs/templates/reference_graph.jinja2', value,
                        self.request),
            charset=renderer[1],
            content_type=renderer[0][0]
        )

    def render_graphml(self, value):
        renderer = self._renderers['graphml']
        return dict(
            body=render('graphs/templates/graph.graphml.jinja2',
                        {'g': value}),
            charset=renderer[1],
            content_type=renderer[0][0]
        )



#def get_reference_graph(n, maxdepth):
#    g = nx.Graph()
#    g.add_node(n, type='self')
#    for f in build_reference_graph(n, maxdepth=maxdepth):
#        g.add_edge( f[1], f[3], type=f[2], power=f[4], depth=f[0])
#
#    return g

from pyramid.util import DottedNameResolver
dotted_name_resolver = DottedNameResolver()

def get_reference_graph(cls, argdict=None):
    # TODO reference graph collection
    argdict = argdict or {}
    if isinstance(cls, basestring):
        try:
            reference_graph = "networkx.generators.%s" % cls
            cls = dotted_name_resolver.resolve(reference_graph)
            if not hasattr(cls, '__name__'):
                raise Exception('not a class') # TODO: validation dict
        except ImportError:
            raise
        except AttributeError:
            raise
    else:
        raise TypeError()

    try:
        # TODO: arguments from test_examples
        return cls(argdict.get('n', 7))
    except Exception:
        raise


def build_graph_formset(graph, *args, **kwargs):
    """introspect parameter formset for graph

    :returns: {
        'n': 'int:slider',
        'm': 'double:slider:range(0, x, default=y)',
        /# ...
    }
    """
    pass

@view_config(route_name='reference_graph',
            permission='view',
            accept='application/json',
            renderer='string')
def reference_graph_view_json(request):
    graphname = request.matchdict.get('graphname')
    request.response_content_type = "application/json; charset: utf-8"
    return nxjson.dumps(get_graph(graphname))

def get_graph(graphname):
    g = get_reference_graph(graphname)
    return dict(
            graphname=graphname,
            graph=nxjson.node_link_data(g),
            title='graph: %s' % graphname,
            params=dict(
                n={'name':'n',
                    'type': 'int',
                    'default': 7,
                    'range': [0,1000],
                    },
            ),
            defaults={
                '0': { 'n': 7 },
                '1': { 'n': 12 },
                '2': { 'n': 24 },
            },
            attributes=dict(
                n_nodes=g.number_of_nodes(),
                n_edges=g.number_of_edges(),
                #'hex': str(hex(n)),
                #'oct': str(oct(n)),
                #"binary": str(bin(n))[2:],
            ),
            d3opts=dict(
                width=800,
                height=400,
                charge=-184,
                linkdistance=80,
                gravity=0.05
            ),
        )


@view_config(route_name='reference_graph',
            permission='view',
            accept='text/html',
            renderer='graphs/templates/reference_graph.jinja2')
def reference_graph_view_html(request):
    graphname = request.matchdict.get('graphname')
    request.response.charset = 'utf-8'
    request.response.content_type = 'application/json'
    return get_graph(graphname)


class ReferenceGraphSchema(formencode.Schema):
    allow_extra_fields = True
    # TODO
    one = formencode.validators.Number(not_empty=True)
    two = formencode.validators.Number(not_empty=True)
    format = formencode.validators.OneOf(['json', 'xml', 'png', 'graphml'])
    #chained_validators = [
    #    formencode.validators.FieldsMatch('pwrd','confirm_pwrd')
    #]

@view_config(permission='view', route_name='reference_graphs',
             renderer='graphs/templates/reference_graphs.jinja2')
def references_view(request):

    form = Form(request, schema=ReferenceGraphSchema)

    if 'submit' in request.POST:
        if not form.validate():
            return {'form': form}
        #session = DBSession()

        graphname = form.data['graphname']
        #one, two = form.data['one'], form.data['two']

        gmeta = defaultdict(None)
        gmeta['id'] = 'TODO: uuid.uuid4()'

        g = get_reference_graph(graphname, request.matchdict)

        fmt = form.data.get('format')

        if fmt == 'json':
            # FIXME: content-type: []/json; charset: UTF-8
            return {'data': nxjson.dumps(g) }

        #elif fmt == 'png': # *
            ## FIXME: ratelimit
            #g_png = g.render('png')
            #res = fs.store(g_png,
                        #type='image/png',
                        #id=gmeta['id'],
                        #uri='graphs/referenceial/%s,%s.png' % (one, two))
            #g_png_uri = res.uri
            ##g_png_uri = route_url('referenceial_graph', request)
            #return HTTPFound(location=g_png_uri)

        #elif fmt == 'xml':
            #raise NotImplementedError()

        #elif fmt == 'graphml':
            #g_graphml = render('templates/graph.graphml.jinja2', {'g': g})
            #res = fs.store(g_graphml,
                #type='something/graphml',
                #id=gmeta['id'],
                #uri='graphs/referenceial/%s,%s.graphml' % (one, two) )
            #g_graphml_uri = res.uri
            #return HTTPFound(location=g_graphml_uri)

    return {
        'title': 'graphs',
        'form': FormRenderer(form),
        'altreps': {},
        #'toolbar': toolbar_view(request),
        #'cloud': cloud_view(request),
        #'latest': latest_view(request),
        #'login_form': login_form_view(request),
    }


import StringIO as io
from .reference import generate_networkx_graph_reference

@view_config(route_name='reference_graph_docs',
            permission='view',
            accept='text/html',
            renderer='string')
def pyramid_view(request):
    request.response.charset = 'utf-8'
    request.response.content_type = 'text/html ; charset: utf-8'

    output_buffer = io.StringIO()
    generate_networkx_graph_reference(output=output_buffer)
    return render_rst2html(
        io.StringIO(
            output_buffer.getvalue().encode('ascii', 'replace')) )


def render_rst2html(source=None, source_path=None):
    try:
        import locale
        locale.setlocale(locale.LC_ALL, '')
    except:
        pass

    from docutils.core import publish_file
    #from docutils.core import default_description

    # The `pygments_code_block_directive`_ module defines and registers a new
    # directive `code-block` that uses the `pygments`_ source highlighter to
    # render code in color::

    #import pygments_code_block_directive

    #description = __doc__ + default_description
    return publish_file(
        source=source,
        source_path=source_path,
        writer_name='html')

