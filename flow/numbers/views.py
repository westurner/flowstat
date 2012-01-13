import formencode
from pyramid.httpexceptions import HTTPFound
from pyramid.exceptions import HTTPNotFound
from pyramid.httpexceptions import HTTPBadRequest

import networkx.readwrite.json_graph.serialize as nxjson
from .primes import (get_number, get_factor_graph, FACTOR_MAXDEPTH,
                    get_factor_range_graph)

from pyramid.renderers import render
from pyramid_simpleform import Form
from pyramid_simpleform.renderers import FormRenderer
from pyramid.response import Response
from collections import defaultdict
from ordereddict import OrderedDict

from pyramid.view import view_config
from pyramid_restler.view import RESTfulView

#from collections import namedtuple
#RendererMimetypeTuple = namedtuple('RendererMimetypeTuple', __RENDERERS.iterkeys())
#_renderers = RendererMimetypes(*RENDERERS.itervalues())

class NumberGraphRESTfulView(RESTfulView):
    #def render_to_response(self, member):
    #    raise Exception(member)

    _entity_name = 'number'
    _renderers = OrderedDict((
        ('html', (('text/html',), 'utf-8',)),
        ('json', (('application/json',), 'utf-8')),
        ('xml', (('application/xml',), 'utf-8')),
        ('graphml', (('application/graphml',), 'utf-8')),
    ))

    def determine_renderer(self):
        request = self.request
        rendererstr = (request.matchdict or {}).get('renderer', '').lstrip('.')

        if rendererstr:
            if rendererstr in self._renderers:
                return rendererstr
            return 'to_404'
        for rndrstr, (ct, charset) in self._renderers.iteritems():
            if request.accept.best_match(ct):
                return rndrstr
        return 'to_404'

    def render_to_response(self, value, fields=None):
        rendererstr = self.determine_renderer()
        try:
            renderer = getattr(self, 'render_{0}'.format(rendererstr))
        except AttributeError:
            name = self.__class__.__name__
            raise HTTPBadRequest(
                '{0} view has no renderer "{1}".'.format(name, rendererstr))

        renderer_output = renderer(value)
        if 'body' in renderer_output:
            return Response(**renderer_output)

        return self.render_to_404(value)

    def render_to_404(self, value):
        # scrub value
        return HTTPNotFound(self.context)

    def render_json(self, value):
        renderer=self._renderers['json']
        response_data = dict(
            body=self.context.to_json(value, self.fields, self.wrap),
            charset=renderer[1],
            content_type=renderer[0][0],
        )
        return response_data

    def render_html(self, value):
        renderer=self._renderers['html']
        return dict(
            body=render('numbers/templates/number.jinja2', value,
                        self.request),
            charset=renderer[1],
            content_type=renderer[0][0]
        )

    def render_graphml(self, value):
        renderer=self._renderers['graphml']
        return dict(
            body=render('graphs/templates/graph.graphml.jinja2',
                        {'g': value}),
            charset=renderer[1],
            content_type=renderer[0][0]
        )


@view_config(route_name='number_n',
            permission='view',
            accept='application/json',
            renderer='string')
def number_view_json(request):
    n = int(request.matchdict['n'], 0)
    maxdepth = request.matchdict.get('maxdepth', 2)

    request.response.content_type = "application/json; charset: utf-8"
    return nxjson.dumps(
            get_factor_graph(n,
                maxdepth))


@view_config(route_name='number_n',
            permission='view',
            accept='text/html',
            renderer='graphs/templates/d3/graph_force.jinja2')
def number_view_html(request):
    try:
        n = int(request.matchdict['n'], 0)
        maxdepth = FACTOR_MAXDEPTH
    except:
        form = Form(request, schema=FactorSchema)

        if 'form.submitted' in request.POST and form.validate():
            n = form.data['n']
            maxdepth = form.data.get('maxdepth', FACTOR_MAXDEPTH)

            return get_number(n, maxdepth)




class FactorSchema(formencode.Schema):
    allow_extra_fields = True

    n = formencode.validators.Number(not_empty=True)
    maxdepth = formencode.validators.OneOf([1,2,3]) # ...
    format = formencode.validators.OneOf(['json','xml','png','graphml'])
    _csrf = formencode.validators.String()
    #chained_validators = [
    #    formencode.validators.FieldsMatch('pwrd','confirm_pwrd')
    #]

class FactorRangeSchema(formencode.Schema):
    allow_extra_fields = False

    one = formencode.validators.Number(not_empty=True)
    two = formencode.validators.Number(not_empty=True)
    format = formencode.validators.OneOf(['json','xml','png','graphml'])
    #chained_validators = [
    #    lambda validate one, two: one <= two
    ##   formencode.validators.FieldsMatch('one','two'')
    #]


@view_config(permission='view', route_name='number_form',
             renderer='graphs/templates/factor_graph.jinja2')
def number_view(request):

    form = Form(request, schema=FactorRangeSchema)

    if 'submit' in request.POST:
        if not form.validate():
            return {'form': FormRenderer(form)}
        #session = DBSession()

        one = form.data['one']
        two = form.data['two']

        maxdepth = form.data.get('maxdepth')

        gmeta = defaultdict(None)
        gmeta['id'] = 'TODO: uuid.uuid4()'

        g = get_factor_range_graph(one, two, maxdepth=maxdepth)

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
        'title': 'numbers',
        'form': FormRenderer(form),
        #'toolbar': toolbar_view(request),
        #'cloud': cloud_view(request),
        #'latest': latest_view(request),
        #'login_form': login_form_view(request),
    }


