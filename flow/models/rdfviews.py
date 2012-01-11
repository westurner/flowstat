
import json
import formencode
from pyramid.view import view_config
from pyramid.renderers import render

from pyramid_simpleform import Form
from pyramid_simpleform.renderers import FormRenderer

from flow.models.rdfmodels import rdf_session
from flow.utils.rdfxml import serializeXML
#from SPARQLExceptions import QueryBadFormed


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



