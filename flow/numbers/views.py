import formencode
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
#from pyramid.httpexceptions import HTTPNotFound
from pyramid_simpleform import Form
from pyramid_simpleform.renderers import FormRenderer

from collections import defaultdict
import networkx as nx
import networkx.readwrite.json_graph.serialize as nxjson
from flow.primes.primes import build_factor_graph, primefactors, count_sorted_list_items, factordict_to_str


def get_factor_graph(n, maxdepth):
    g = nx.Graph()
    g.add_node(n, type='self')
    for f in build_factor_graph(n, maxdepth=maxdepth):
        g.add_edge( f[1], f[3], type=f[2], power=f[4], depth=f[0])

    return g


@view_config(route_name='factors_of',
            permission='view',
            accept='application/json',
            renderer='string')
def factors_of_view_json(request):
    n = int(request.matchdict['n'], 0)
    maxdepth = request.matchdict.get('maxdepth', 2)

    request.response.content_type = "application/json; charset: utf-8"
    return nxjson.dumps(get_factor_graph(n, maxdepth))

@view_config(route_name='factors_of',
            permission='view',
            accept='text/html',
            renderer='templates/d3/graph_force.jinja2')
def factors_of_view_html(request):
    n = int(request.matchdict['n'], 0)
    maxdepth = 3

    pfactorized=list(count_sorted_list_items(primefactors(n, sort=True)))
    return {
            #'data': nxjson.dumps(get_factor_graph(n, maxdepth)),
            'n': n,
            'maxdepth': maxdepth,

            "isprime": sum(v for f, v in pfactorized) == 1, #
            "primefactordict": pfactorized,
            "primefactorization": factordict_to_str(n, pfactorized),
            "primefactorcount": sum(p for n,p in pfactorized),
            "primefactorcount_unique": len(pfactorized),

            'altreps': {
                'hex': str(hex(n)),
                'oct': str(oct(n)),
                "binary": str(bin(n))[2:],
                },

            'opts': {
                'width': 800,
                'height': 400,
                'charge': -200,
                'link_distance': 200,
                'gravity': 0.05
                },
            }


class FactorsSchema(formencode.Schema):
    allow_extra_fields = True
    # TODO
    one = formencode.validators.Number(not_empty=True)
    two = formencode.validators.Number(not_empty=True)
    format = formencode.validators.OneOf(['json','xml','png','graphml'])
    #chained_validators = [
    #    formencode.validators.FieldsMatch('pwrd','confirm_pwrd')
    #]

@view_config(permission='view', route_name='factors',
             renderer='templates/factor_graph.jinja2')
def factors_view(request):

    form = Form(request, schema=FactorsSchema)

    if 'submit' in request.POST:
        if not form.validate():
            return {'form': form}
        #session = DBSession()

        one, two = form.data['one'], form.data['two']
        maxdepth = form.data.get('maxdepth',2)

        gmeta = defaultdict(None)
        gmeta['id'] = 'TODO: uuid.uuid4()'

        # Build NX graph from seq(one,two)
        g = nx.Graph()
        for n in xrange(one, two):
            for f in build_factor_graph(n, maxdepth=maxdepth):
                g.add_edge(f[1], f[3], type=f[2], power=f[4]) # TODO

        fmt = form.data.get('format')

        if fmt == 'json':
            # FIXME: content-type: []/json; charset: UTF-8
            return {'data': nxjson.dumps(g) }

        elif fmt == 'png': # *
            # FIXME: ratelimit
            g_png = g.render('png')
            res = fs.store(g_png, type='image/png', id=gmeta['id'], uri='graphs/factorial/%s,%s.png' % (one, two)  )
            g_png_uri = res.uri
            #g_png_uri = route_url('factorial_graph', request)
            return HTTPFound(location=g_png_uri)

        elif fmt == 'xml':
            raise NotImplementedError()

        elif fmt == 'graphml':
            g_graphml = render('templates/graph.graphml.jinja2', {'g': g})
            res = fs.store(g_graphml, type='something/graphml', id=gmeta['id'], uri='graphs/factorial/%s,%s.graphml' % (one, two) )
            g_graphml_uri = res.uri
            return HTTPFound(location=g_graphml_uri)

    return {
        'form': FormRenderer(form),
        #'toolbar': toolbar_view(request),
        #'cloud': cloud_view(request),
        #'latest': latest_view(request),
        #'login_form': login_form_view(request),
    }


