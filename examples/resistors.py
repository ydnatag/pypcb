from pypcb import Net, Circuit
from pypcb.lib.generic import Resistor
from pypcb.back.ngspice import NgSpice, VoltageSource as V
from fractions import Fraction
import pytest


def divider(net_in, net_out, gnd, factor, multiplier=1e3, error=0.1):
    assert 0 < factor < 1
    d = Fraction(factor).limit_denominator()
    assert ((factor - (d.numerator / d.denominator)) / factor) < error

    c = Circuit()
    r1 = Resistor((d.denominator - d.numerator) * multiplier)
    r2 = Resistor(d.numerator * multiplier)

    c.connections += [
        (net_in, r1.p1),
        (r1.p2, r2.p1, net_out),
        (r2.p2, gnd)
    ]

    return c


def test_divider_dc():
    div = 0.33
    nout = Net()
    v = V(1)
    vin, gnd = v.p, v.n
    c = divider(net_in=v.p, net_out=nout, factor=div, gnd=gnd)
    spice = NgSpice(c, gnd=gnd)
    traced = spice.dcsweep([(v, (-5, 5, 1))], trace=[vin, nout])
    vin_v = traced[vin]
    nout_v = traced[nout]
    assert pytest.approx(vin_v * div, 0.01) == nout_v


def test_divider_tran():
    div = 0.33
    nout = Net()
    v = V('sin(0 2 100e6)')
    vin, gnd = v.p, v.n
    c = divider(net_in=v.p, net_out=nout, factor=div, gnd=gnd)
    spice = NgSpice(c, gnd=gnd)
    traced = spice.transient(step=0.1, stop=10, units='ns', trace=[vin, nout])
    time = traced['time']
    vin_v = traced[vin]
    nout_v = traced[nout]
    assert min(time) == 0
    assert max(time) == 10e-9
    assert pytest.approx(vin_v * div, 0.01) == nout_v


if __name__ == '__main__':
    test_divider_dc()
    test_divider_tran()
