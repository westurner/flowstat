import formencode
from pyramid.view import view_config
from pyramid.renderers import render

from pyramid_simpleform import Form
from pyramid_simpleform.renderers import FormRenderer

from flow.rdfmodels import rdf_session
#from SPARQLExceptions import QueryBadFormed
import json
from flow.utils.rdfxml import serializeXML

class SPARQLQuerySchema(formencode.Schema):
    allow_extra_fields = True
    query = formencode.validators.String(not_empty=True) # ..
    format = formencode.validators.OneOf(['json','xml'])

@view_config(permission='view', route_name='sparql_query',
        renderer='string')
def sparql_query(request):

    store = rdf_session.default_store
    results_json = None

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if 'query' in request.GET:
            try:
                results_json = json.dumps(store.execute_sparql(request.GET['query']))
            except Exception, e:
                results_json = {'error': str(e) }
            
            request.response_content_type = 'application/sparql-results+json'
            return render('string', results_json, request)
    else:

        form = Form(request, schema=SPARQLQuerySchema)
        querystr = """SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 200"""

        if 'form.submitted' in request.POST and form.validate():
            querystr = form.data['query']
            format = form.data.get('format','json')
            try:
                results = store.execute_sparql(querystr, format=format)
                if format=='json':
                    results_json = json.dumps(results, indent=4)
                elif format=='xml':
                    try:
                        results_json = serializeXML(results)
                    except:
                        raise
            except Exception, e:
                results_json = str(e)
                raise
            #results_json = json.dumps([x for x in results])

        request.response_content_type = 'text/html'
        return render('templates/sparql_query.jinja2', {
            'form': FormRenderer(form),
            'query': querystr,
            'results': results_json,
            }, request)


@view_config(permission='view', route_name='deniz', renderer='deniz.jinja2')
def deniz(request):
    return {}


from collections import defaultdict
import networkx as nx

class FactorsSchema(formencode.Schema):
    allow_extra_fields = True
    # TODO
    one = formencode.validators.Integer(not_empty=True)
    two = formencode.validators.Integer(not_empty=True)
    format = formencode.validators.OneOf(['json','xml','png','graphml'])
    #chained_validators = [
    #    formencode.validators.FieldsMatch('pwrd','confirm_pwrd')
    #]


@view_config(permission='view', route_name='factors',
             renderer='templates/factor_graph.jinja2')
def factors_view(request):

    form = Form(request, schema=FactorsSchema)

    if 'form.submitted' in request.POST and form.validate():
        #session = DBSession()

        one, two = form.data['one'], form.data['two']

        gmeta = defaultdict(None)
        gmeta['id'] = 'TODO: uuid.uuid4()'
        g = nx.Graph()

        for n in xrange(one, two):
            g.add_node(n)
            for f in prfactors(n):
                g.add_edge(n, f, {'a':'factorOf'})

        fmt = form.data.get('format')

        if fmt == 'json':
            g_json = g.serialize('json') # client side render
            # FIXME: content-type: []/json; charset: UTF-8
            return g_json

        elif fmt == 'png': # *
            # FIXME: ratelimit
            g_png = g.render('png')
            res = fs.store(g_png, type='image/png', id=gmeta['id'], uri='graphs/factorial/%s,%s.png' % (one, two)  )
            g_png_uri = res.uri
            #g_png_uri = route_url('factorial_graph', request)
            return HTTPFound(location=g_png_uri)

        elif fmt == 'xml':
            raise NotImplementedError()

        #elif form.data.get('format') == 'graphml'):
        else:
            g_graphml = render('templates/graph.graphml.jinja2', {'g': g})
            res = fs.store(g_graphml, type='something/graphml', id=gmeta['id'], uri='graphs/factorial/%s,%s.graphml' % (one, two) )
            g_graphml_uri = res.uri
            return HTTPFound(location=g_graphml_uri)

    return {
        'form': FormRenderer(form),
        'toolbar': toolbar_view(request),
        'cloud': cloud_view(request),
        'latest': latest_view(request),
        'login_form': login_form_view(request),
    }


