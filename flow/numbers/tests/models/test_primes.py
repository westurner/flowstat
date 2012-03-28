import unittest

#from ..primes import count_sorted_list_items
#from ..primes import count_unsorted_list_items
#from ..primes import primefactors
#from ..primes import all_factors
#from ..primes import build_factor_graph

class TestListCounters(unittest.TestCase):
    def test_count_unsorted_list_items(self):
        from ...primes import count_unsorted_list_items
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
            #print inp, exp_outp, counts
            self.assertEqual(counts, dict(exp_outp))

    def test_count_sorted_list_items(self):
        from ...primes import count_sorted_list_items
        D = (
            ([], []),
            ([2], [(2, 1)]),
            ([2, 2], [(2, 2)]),
            ([2, 2, 2, 2, 3, 3, 5, 5], [(2, 4), (3, 2), (5, 2)]),
            ([5, 1, 1, 2], [(5, 1), (1, 2), (2, 1)]),
            )
        for inp, exp_outp in D:
            counts = list(count_sorted_list_items(inp))
            #print inp, exp_outp, counts
            self.assertEqual(counts, exp_outp)

        #inp, exp_outp = UNSORTED_FAIL = ([2,2,4,2], [(2,3), (4,1)])
        #self.assertEqual(exp_outp, list( count_sorted_list_items(inp) ))
        # ... [(2,2), (4,1), (2,1)]


class TestPrimeFactors(unittest.TestCase):

    def test_prime_factors(self):
        from ...primes import primefactors
        from ...primes import count_sorted_list_items

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
        from ...primes import all_factors
        D = (
            (360, [1, 5, 3, 15, 9, 45, 2, 10, 6, 30, 18, 90, 4, 20, 12, 60, 36, 180, 8, 40, 24, 120, 72, 360]),
        )
        for inp, exp_outp in D:
            outp = list(all_factors(inp))
            self.assertEqual(outp, exp_outp)

class TestFactorGraph(unittest.TestCase):
    def test_build_factor_graph(self):
        from ...primes import build_factor_graph
        D_FAIL = [] #[1, 2, 3]
        D = [ 12, 25]
        for n in D_FAIL:
            print "Should Fail:", n
            self.assertRaises(ValueError, lambda x: list(build_factor_graph(x)), n)

        for n in D:
            print "Factors Of:", n
            for edge in build_factor_graph(n):
                print edge

