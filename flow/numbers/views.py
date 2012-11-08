import formencode
#from pyramid.httpexceptions import HTTPFound
from pyramid.exceptions import HTTPNotFound
from pyramid.httpexceptions import HTTPBadRequest

#import networkx.readwrite.json_graph.serialize as nxjson
#from .primes import get_number
from pyramid.renderers import render
#from pyramid_simpleform import Form
#from pyramid_simpleform.renderers import FormRenderer
from pyramid.response import Response

#from pyramid.view import view_config
from pyramid_restler.view import RESTfulView

try:
    from collections import OrderedDict
except:
    from ordereddict import OrderedDict

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



class FactorSchema(formencode.Schema):
    allow_extra_fields = True

    n = formencode.validators.Number(not_empty=True)
    maxdepth = formencode.validators.OneOf([1,2,3]) # ...
    format = formencode.validators.OneOf(['json','xml','png','graphml'])
    _csrf = formencode.validators.String()
    #chained_validators = [
    #    formencode.validators.FieldsMatch('pwrd','confirm_pwrd')
    #]
