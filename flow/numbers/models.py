from flow.models.context import PlainContext

from .primes import get_number
def NumbersContextFactory(request):
    return PlainContext(request, fn=lambda id: get_number(int(id, 0)))
