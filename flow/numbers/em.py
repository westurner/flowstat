#!/usr/bin/env python
# encoding: utf-8
"""
EM Units
"""

def hz_to_wavelength(hz):
    """
    see:http://www.photonics.byu.edu/fwnomograph.phtml

    c = freq_hz * wavelength_m

    wavelength_m = c / freq_hz
    """
    c = 299792458.0
    return float(c / hz)


def scale_units(val, UNITS, uniti = None):
    if uniti:
        unit = UNITS[uniti] # Hz
    else:
        rmin = 0
        rmax = -1
        for uniti, unit in enumerate(UNITS):
            if not unit[3]:
                next
            if val >= unit[0]:
                rmin = uniti
            else:
                rmax = uniti
                break
        unitmin = UNITS[rmin]
        unitmax = UNITS[rmax]
        #print unitmin, (val / unitmin[0]), unitmin[1]
        #print unitmax, (val / unitmax[0]), unitmin[1]
        if unitmin[3] >= unitmax[3]:
            unit = unitmin
            uniti = rmin
        else:
            unit = unitmax
            uniti = rmax

    return ((val / unit[0]), unit[1])

DIST_SI = (
    (1e-24, u"ym", "yoctometre", 1),
    (1e-21, u"zm", "zeptometre", 1),
    (1e-18, u"am", "attometre",  1),
    (1e-15, u"fm", "femtometre", 1),
    (1e-12, u"pm", "picometre",  1),
    (1e-9,  u"nm", "nanometre",  1),
    (1e-6,  u"μm", "micrometre", 1),
    (1e-3,  u"mm", "millimetre", 1),
    (1e-2,  u"cm", "centimetre", 1),
    (1e-1,  u"dm", "decimetre",  1),
    (1e0,   u"m" , "metre",      2),
    (1e1,   u"dam", "decametre", 1),
    (1e2,   u"hm", "hectometre", 1),
    (1e3,   u"km", "kilometre",  2),
    (1e6,   u"Mm", "megametre",  0),
    (1e9,   u"Gm", "gigametre",  0),
    (1e12,  u"Tm", "terametre",  0),
    (1e15,  u"Pm", "petametre",  0),
    (1e18,  u"Em", "exametre",   0),
    (1e21,  u"Zm", "zettametre", 0),
    (1e24,  u"Ym", "yottametre", 0),
)

HZ_SI = (
    (1e-24, u"yHz", "yoctohertz", 1),
    (1e-21, u"zHz", "zeptohertz", 1),
    (1e-18, u"aHz", "attohertz",  1),
    (1e-15, u"fHz", "femtohertz", 1),
    (1e-12, u"pHz", "picohertz",  1),
    (1e-9,  u"nHz", "nanohertz",  1),
    (1e-6,  u"μHz", "microhertz", 1),
    (1e-3,  u"mHz", "millihertz", 1),
    (1e-2,  u"cHz", "centihertz", 1),
    (1e-1,  u"dHZ", "decihertz",  1),
    (1e0,   u"Hz" , "hertz",      2),
    (1e1,   u"daHz", "decahertz", 1),
    (1e2,   u"hHz", "hectohertz", 1),
    (1e3,   u"kHz", "kilohertz",  2),
    (1e6,   u"MHz", "megahertz",  2),
    (1e9,   u"GHz", "gigahertz",  2),
    (1e12,  u"THz", "terahertz",  2),
    (1e15,  u"PHz", "petahertz",  1),
    (1e18,  u"EHz", "exahertz",   1),
    (1e21,  u"ZHz", "zettahertz", 1),
    (1e24,  u"YHz", "yottahertz", 1),
)

def scale_hz(hz):
    if hz > 0 and hz < 1000:
        return scale_units(hz, HZ_SI, 10)  # default to Hz
    else:
        return scale_units(hz, HZ_SI)

def scale_m(m):
    if m > 0 and m < 1000:
        return scale_units(m, DIST_SI, 10)
    else:
        return scale_units(m, DIST_SI)

import unittest
class TestHertz(unittest.TestCase):
    def test_hertz(self):
        bands = (
            # Brain
            ( "delta",  ( 0.1, 4), ),
            ( "theta",  ( 4,   8), ),
            ( "alpha",  ( 8,   12), ),
            ( "mu",     ( 8,   13), ),
            ( "beta",   (12,   30), ), # low,beta,high 12-15,15-18,19-30
            ( "gamma",  (30,   100), ), # 100+:

            # Compassion (Gamma)
            ( "compassion", (25, 40), ),

            # Bass Guitar (Gamma)
            ( "bassguit B0", (30.87, 30.87), ),

            ( "bassguit E1", (41.20, 41.20), ),
            ( "bassguit A1", (55,    55), ),
            ( "bassguit D2", (73.42, 73.42), ),
            ( "bassguit G2", (98,    98), ),

            # Guitar Standard Pitches (Gamma, 
            ( "guit E2", (82.41,  82.41), ),
            ( "guit A2", (110,    110), ),
            ( "guit D3", (146.83, 146.83), ),
            ( "guit G3", (196.00, 196.00), ),
            ( "guit B3", (246.94, 246.94), ),
            ( "guit E4", (329.63, 329.63), ),

            #   0	1	2	3	4	5	6	7	8	9	10	11	12
            #   E2  F	F♯	G	A♭	A	B♭	B	C	C♯	D	E♭	E
            #   B	C	C♯	D	E♭	E	F	F♯	G	A♭	A	B♭	B
            #   G	A♭	A	B♭	B	C	C♯	D	E♭	E	F	F♯	G
            #   D	E♭	E	F	F♯	G	A♭	A	B♭	B	C	C♯	D
            #   A	B♭	B	C	C♯	D	E♭	E	F	F♯	G	A♭	A
            #   E4	F	F♯	G	A♭	A	B♭	B	C	C♯	D	E♭	E

            # Human Voice
            ( "human voice", (80, 1100), ),

            #( "soprano", (c-5), ),
            #( "mezzo-soprano", (a3, a5), ),
            #( "contralto", (f3, f5), ),
            #( "tenor", (c3, c5), ),
            #( "baritone", (f2,f4), ),
            #( "bass", (e2, e4), ),


            ( "human hearing", ( 20, 2.0*1e4, ), ),
            ( "ultrasound",   (20*1e4, 20*1e4, ), ), # 20000, inf.
            ( "dog hearing" , ( 40, 6.0*1e4, ), ),

            ( "bat hearing",  ( 20, 1.2*1e5, ), ),

            ( "mice hearing", ( 1*1e4, 90*1e4, ), ),

            ( "dolphin type I: A", ( 2*1e4, 2*1e4, ), ),
            (" dolphin type I: B", ( 110*1e4, 110*1e4, ), ),

            ( "whale/bottlenose type II", ( 0.25*1e4, 150*1e4 ), ),

            ( "free-water protons", (63*1e6, 63*1e6), ),  # @ 1.5 teslas

            # proton EFNR       equator, poles
            ( "EFNR VLF->ULF", (1.3*1e2, 2.5*1e2), ),

            ( "audio CD", (4.41*1e4, 4.41*1e4), ),


            ( "micro", (300*1e6, 300*1e9), ),

            ( "long wave", (148.5*1e4, 283.5*1e4), ),
            ( "medium wave", (520*1e6, 1610*1e6), ),
            ( "amateur radio", (1.8*1e6, 2.0*1e6), ),
            ( "short wave",  (2.3*1e6, 26.1*1e6), ),

            ( "FM radio", (87.5*1e6, 108.0*1e6), ),
            ( "TV", (54*1e6, 890*1e6), ),

            # Visible
            ( "violet", (668*1e12, 789*1e12), ),
            ( "blue", (631*1e12, 668*1e12), ),
            ( "cyan", (606*1e12, 630*1e12), ),
            ( "green", (526*1e12, 606*1e12), ),
            ( "yellow", (508*1e12, 526*1e12), ),
            ( "orange", (484*1e12, 508*1e12), ),
            ( "red", (400*1e12, 484*1e12), ),
        )
        smin = min(b[1][0] for b in bands)
        smax = max(b[1][1] for b in bands)
        print "BANDS"
        print smin, smax
        print hz_to_wavelength(smin or 1)
        print hz_to_wavelength(smax)
        for b, (bmin, bmax) in bands:
            print b
            print "%s  %f" % (scale_hz(bmin), scale_m(hz_to_wavelength(bmin)))
            print "%s  %f" % (scale_hz(bmax), scale_m(hz_to_wavelength(bmax)))

        raise NotImplementedError()

    def test_scale_hz(self):
        D = (
                (3.2e9, (3.2, "GHz")),
                (3.2e2, (320, "Hz")),
                (3.2e12, (3.2, "THz")),
        )
        for inp, exp_outp in D:
            outp = scale_hz(inp)
            self.assertEqual(outp, exp_outp)
            print outp
        raise NotImplementedError()

    def test_scale_m(self):
        D = (
                (3.2e9, (3200000, "km")),
                (3.2e2, (320, "m")),
                (3.2e-3, (1, 1))
        )
        for inp, exp_outp in D:
            outp = scale_m(inp)
            self.assertEqual(outp, exp_outp)
            print outp
        raise NotImplementedError()



def main():
    """
    EM Units Main
    """
    pass


if __name__ == "__main__":
    import optparse
    import logging

    prs = optparse.OptionParser(usage="./")

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
        sys.argv = sys.argv[0]+args
        import unittest
        exit(unittest.main())

    main()
