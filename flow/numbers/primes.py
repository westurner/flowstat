#!/usr/bin/env python
# encoding: utf-8
"""
Prime Factors

See: http://stackoverflow.com/questions/4643647/fast-prime-factorization-module
"""
#pylint: disable-msg: E501

import random
import operator
import networkx as nx
from collections import defaultdict
from itertools import product, repeat

def primesbelow(N):
    """
    Input N>=6, Returns a list of primes, 2 <= p < N

    See: http://stackoverflow.com/questions/2068372/fastest-way-to-list-all-primes-below-n-in-python/3035188#3035188
    """
    correction = N % 6 > 1
    N = {
        0: N,
        1: N - 1,
        2: N + 4,
        3: N + 3,
        4: N + 2,
        5: N + 1}[N % 6]
    sieve = [True] * (N // 3)
    sieve[0] = False
    for i in range(int(N ** .5) // 3 + 1):
        if sieve[i]:
            k = (3 * i + 1) | 1
            sieve[k * k // 3:: 2 * k] = [False] * ((N // 6 - (k * k) // 6 - 1) // k + 1)
            sieve[(k * k + 4 * k - 2 * k * (i % 2)) // 3:: 2 * k] = [False] * ((N // 6 - (k * k + 4 * k - 2 * k * (i % 2)) // 6 - 1) // k + 1)
    return [2, 3] + [(3 * i + 1) | 1 for i in range(1, N // 3 - correction) if sieve[i]]


_smallprimeset = 100000
smallprimeset = set(primesbelow(_smallprimeset))
smallprimes = (2,) + tuple(n for n in xrange(3, 1000, 2) if n in smallprimeset)

def isprime(n, precision=7):
    """
    Miller Rabin Primality Test

    See: http://en.wikipedia.org/wiki/Miller-Rabin_primality_test#Algorithm_and_running_time
    """
    if n == 1 or n % 2 == 0:
        return False
    elif n < 1:
        raise ValueError("Out of bounds, first argument must be > 0")
    elif n < _smallprimeset:
        return n in smallprimeset

    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1

    for repeat in range(precision):
        a = random.randrange(2, n - 2)
        x = pow(a, d, n)

        if x == 1 or x == n - 1:
            continue

        for r in range(s - 1):
            x = pow(x, 2, n)
            if x == 1:
                return False
            if x == n - 1:
                break
        else:
            return False

    return True


def pollard_brent(n):
    """
    Pollard-Brent

    https://comeoncodeon.wordpress.com/2010/09/18/pollard-rho-brent-integer-factorization/
    """
    if n % 2 == 0:
        return 2
    if n % 3 == 0:
        return 3

    y, c, m = random.randint(1, n - 1), random.randint(1, n - 1), random.randint(1, n - 1)
    g, r, q = 1, 1, 1
    while g == 1:
        x = y
        for i in range(r):
            y = (pow(y, 2, n) + c) % n

        k = 0
        while k < r and g == 1:
            ys = y
            for i in range(min(m, r - k)):
                y = (pow(y, 2, n) + c) % n
                q = q * abs(x - y) % n
            g = gcd(q, n)
            k += m
        r *= 2
    if g == n:
        while True:
            ys = (pow(ys, 2, n) + c) % n
            g = gcd(abs(x - ys), n)
            if g > 1:
                break

    return g


def factorization(n):
    factors = {}
    for p1 in primefactors(n):
        try:
            factors[p1] += 1
        except KeyError:
            factors[p1] = 1
    return factors


totients = {}


def totient(n):
    if n == 0:
        return 1

    try:
        return totients[n]
    except KeyError:
        pass

    tot = 1
    for p, exp in factorization(n).items():
        tot *= (p - 1) * p ** (exp - 1)

    totients[n] = tot
    return tot


def gcd(a, b):
    if a == b:
        return a
    while b > 0:
        a, b = b, a % b
    return a


def lcm(a, b):
    return abs(a * b) // gcd(a, b)


def primefactors(n, sort=False):
    factors = []

    limit = int(n ** .5) + 1
    for checker in smallprimes:
        #print smallprimes[-1]
        if checker > limit:
            break
        while n % checker == 0:
            factors.append(checker)
            n //= checker
            limit = int(n ** .5) + 1
            if checker > limit:
                break

    if n < 2:
        return factors
    else:
        return factors + bigfactors(n, sort)


def bigfactors(n, sort=False):
    factors = []
    while n > 1:
        if isprime(n):
            factors.append(n)
            break
        factor = pollard_brent(n)
        # recurse to factor the not necessarily prime factor returned by pollard-brent
        factors.extend(bigfactors(factor, sort))
        n //= factor

    if sort:
        factors.sort()
    return factors


def _all_factors(prime_dict):
    """
    See: http://stackoverflow.com/questions/1010381/python-factorization
    """
    series = [[(p ** e) for e in range(maxe + 1)] for p, maxe in prime_dict]
    for multipliers in product(*series):
        yield reduce(operator.mul, multipliers)


def all_factors(n):
    """
    :param n: number to factorize
    :type n: int

    :returns: all integer factors of n (one-inclusive)
    :rtype: generator
    """
    if isprime(n):
        return n
    return _all_factors(count_sorted_list_items(primefactors(n)))

from collections import namedtuple
FactorEdge = namedtuple('FactorEdge', ['depth', 'n', 'egtype', 'f', 'power'])

lbl_primefactor = 'primeFactor'
lbl_subfactor = 'factor'
def build_factor_graph(n, depth=1, maxdepth=1):
    """
    Given n, generate a list of edges:
     + Prime factors of n
     for each Factor of n
       + Prime factors of factors of n
       + Factors of factors of n (recursive)

    :param n: number to factorize
    :type n: int

    :returns: generator of edge tuples
    :rtype: generator
    """

    if n <= 1:
        raise ValueError('n must be greater than 1')

    # yield ('', n, 'loneliest', 1, inf.)
    if not (depth-1):
        yield ('', n, 'self', n, 1)
    if isprime(n):
        return
        #raise ValueError('n is prime')

    prime_factors = dict( count_sorted_list_items(primefactors(n,sort=True)) )

    for f, power in prime_factors.iteritems():
        yield FactorEdge(depth, n, lbl_primefactor, f, power)

    factors = _all_factors(prime_factors.iteritems())
    factors.next() # Skip '1'
    for f in factors:
        if f != n and f not in prime_factors:
            yield FactorEdge(depth, n, lbl_subfactor, f, 1)
            if not maxdepth or depth < maxdepth:
                for f in build_factor_graph(f, depth=depth+1, maxdepth=maxdepth):
                    yield f

def main():
    """
    Test Prime Factors
    """
    pass


# Python >= 2.6 (defaultdict)
def count_unsorted_list_items(items):
    """
    :param items: iterable of hashable items to count
    :type items: iterable

    :returns: dict of counts like Py2.7 Counter
    :rtype: dict
    """
    counts = defaultdict(int)
    for item in items:
        counts[item] += 1
    return dict(counts)
    # OrderedDict >= 2.7


# Python >= 2.2 (generators)
def count_sorted_list_items(items):
    """
    :param items: sorted iterable of items to count
    :type items: sorted iterable

    :returns: generator of (item,count) tuples
    :rtype: generator
    """
    if not items:
        return
    elif len(items) == 1:
        yield (items[0], 1)
        return
    prev_item = items[0]
    count = 1
    for item in items[1:]:
        if prev_item == item:
            count += 1
        else:
            yield (prev_item, count)
            count = 1
            prev_item = item
    yield (item, count)
    return


FACTOR_MAXDEPTH = 1
def get_factor_graph(n, maxdepth=FACTOR_MAXDEPTH):
    g = nx.Graph()
    g.add_node(n, type='self')
    for f in build_factor_graph(n, maxdepth=maxdepth):
        g.add_edge( f[1], f[3], type=f[2], power=f[4], depth=f[0])

    return g


def get_factor_range_graph(one, two, maxdepth=FACTOR_MAXDEPTH):
    # Build NX graph from seq(one,two)
    g = nx.Graph()
    for n in xrange(one, two):
        for f in build_factor_graph(n, maxdepth=maxdepth):
            g.add_edge(f[1], f[3], type=f[2], power=f[4]) # TODO


def get_factor_dict(n, maxdepth=FACTOR_MAXDEPTH):
    return count_sorted_list_items(
                primefactors(n,
                    sort=True))


def factordict_to_str(n, factors):
    return (' * '.join(
                ( (
                    (count >1) and '%s**%s' % (f, count,) or str(f))
                        for f,count in factors)))

import flow.models.json.nxjson as nxjson
from ordereddict import OrderedDict
def get_number(n, maxdepth=None):
    factorized = list(get_factor_dict(n, maxdepth))
    factorization = factordict_to_str(n, factorized)
    factorcount_uniq = len(factorized)
    factorcount = sum(v for k,v in factorized)
    is_prime = (factorcount == 1)

    factorgraph = nxjson.node_link_data(
                        get_factor_graph(n,
                            maxdepth ))

    return OrderedDict(
            n=n,
            title=' = '.join((str(n), str(factorization))),
            maxdepth=maxdepth,
            isprime=is_prime,
            primefactordict=factorized,
            primefactorization=factorization,
            primefactorcount=factorcount,
            primefactorcount_unique=factorcount_uniq,
            graph=factorgraph,

            attributes=OrderedDict(
                hex=str(hex(n)),
                oct=str(oct(n)),
                binstr=str(bin(n))[2:],
            ),

            d3opts=dict(
                width=800,
                height=400,
                charge=-184,
                linkdistance=184,
                gravity=-0.00
                ),
            )


import unittest


class TestListCounters(unittest.TestCase):
    def test_count_unsorted_list_items(self):
        D = (
            ([], []),
            ([2], [(2, 1)]),
            ([2, 2], [(2, 2)]),
            ([2, 2, 2, 2, 3, 3, 5, 5], [(2, 4), (3, 2), (5, 2)]),
            ([2, 2, 4, 2], [(2, 3), (4, 1)]),
            ([5, 1, 1, 2], [(5, 1), (1, 2), (2, 1)]),
            )
        for inp, exp_outp in D:
            counts = count_unsorted_list_items(inp)
            print inp, exp_outp, counts
            self.assertEqual(counts, dict(exp_outp))

    def test_count_sorted_list_items(self):
        D = (
            ([], []),
            ([2], [(2, 1)]),
            ([2, 2], [(2, 2)]),
            ([2, 2, 2, 2, 3, 3, 5, 5], [(2, 4), (3, 2), (5, 2)]),
            ([5, 1, 1, 2], [(5, 1), (1, 2), (2, 1)]),
            )
        for inp, exp_outp in D:
            counts = list(count_sorted_list_items(inp))
            print inp, exp_outp, counts
            self.assertEqual(counts, exp_outp)

        #inp, exp_outp = UNSORTED_FAIL = ([2,2,4,2], [(2,3), (4,1)])
        #self.assertEqual(exp_outp, list( count_sorted_list_items(inp) ))
        # ... [(2,2), (4,1), (2,1)]


class TestPrimeFactors(unittest.TestCase):

    def test_prime_factors(self):
        D = (
            (1, [], {}),
            (2, [2], {2: 1}),
            (12, [2, 2, 3], {2: 2, 3: 1}),
            (3600, [2, 2, 2, 2, 3, 3, 5, 5], {2: 4, 3: 2, 5: 2}),
            (123123412542, [2, 3, 13, 41, 38500129L], {2: 1, 3: 1, 13: 1, 41: 1, 38500129L: 1}),
        )
        print "FACTORS"
        for n, expected, powers in D:
            factors = primefactors(n)
            fpowers = list(count_sorted_list_items(factors))
            print n, factors, fpowers
            self.assertEqual(factors, expected)
            self.assertEqual(dict(fpowers), powers)

    def test_factorization(self):
        D = (
            (360, [1, 5, 3, 15, 9, 45, 2, 10, 6, 30, 18, 90, 4, 20, 12, 60, 36, 180, 8, 40, 24, 120, 72, 360]),
        )
        for inp, exp_outp in D:
            outp = list(all_factors(inp))
            self.assertEqual(outp, exp_outp)

class TestFactorGraph(unittest.TestCase):
    def test_build_factor_graph(self):
        D_FAIL = [] #[1, 2, 3]
        D = [ 12, 25]
        for n in D_FAIL:
            print "Should Fail:", n
            self.assertRaises(ValueError, lambda x: list(build_factor_graph(x)), n)

        for n in D:
            print "Factors Of:", n
            for edge in build_factor_graph(n):
                print edge
        raise NotImplementedError()


if __name__ == "__main__":
    import optparse
    import logging

    prs = optparse.OptionParser(usage="./")

    prs.add_option('-g','--factor-graph',
                    dest='build_factor_graph',
                    type='int',
                    action='store',
                    )
    prs.add_option('-m','--max-depth',
                    dest='max_depth',
                    type='int',
                    default=1,
                    action='store',)

    prs.add_option('-p','--prime-factors',
                    dest='build_prime_factors',
                    type='int',
                    action='store',)
    prs.add_option('-x','--expand',
                    dest='expand_prime_factors',
                    action='count',)


    prs.add_option('-v', '--verbose',
                    dest='verbose',
                    action='store_true',)
    prs.add_option('-q', '--quiet',
                    dest='quiet',
                    action='store_true',)
    prs.add_option('-t', '--test',
                    dest='run_tests',
                    action='store_true',)

    (opts, args) = prs.parse_args()

    if not opts.quiet:
        logging.basicConfig()

        if opts.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    if opts.run_tests:
        import sys
        sys.argv = [sys.argv[0]] + args
        import unittest
        exit(unittest.main())

    if opts.build_prime_factors:
        n=opts.build_prime_factors
        factors = primefactors(n, sort=True)
        factors = count_sorted_list_items(factors)
        print '=',n,'='
        if not opts.expand_prime_factors:
            for f in factors:
                print f
        else:
            factors = list(factors)
            for f, c in factors:
                print '**'.join((str(f),str(c))),'=',f**c

            print '\n',

            if opts.expand_prime_factors > 2:
                print ' * '.join(
                            ('*'.join(str(x) for x in repeat(f,count)))
                                for f, count in factors),'=', n
                print '\n',
            elif opts.expand_prime_factors > 1:
                print ' * '.join(
                        ('%s**%s' % (f, count,)
                            for f,count in factors)),'=', n
                print '\n',

    if opts.build_factor_graph:
        for edge in build_factor_graph(opts.build_factor_graph, maxdepth=opts.max_depth):
            print edge

    main()
