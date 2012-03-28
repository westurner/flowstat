from flow.models.context import PlainContext

from .primes import get_number
def NumbersContextFactory(request):
    return PlainContext(request,
            get_member=lambda n: n and get_number(int(n, 0)),
            get_collection=lambda *args, **kwargs: dict(),
            index_key='n'
            )
