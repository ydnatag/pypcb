import argparse
import os
from pypcb import Net, Circuit, Board
from pypcb.lib.generic import Transistor, Resistor, Capacitor, Connector
from pypcb.back.kicad import generate_netlist, read_netlist


class BC548(Transistor):
    footprint = 'Package_TO_SOT_THT:TO-92_Inline'
    value = 'BC548'


class Resistor0805(Resistor):
    footprint = 'Resistor_SMD:R_0805_2012Metric'


class Capacitor0805(Capacitor):
    footprint = 'Capacitor_SMD:C_0805_2012Metric'


class CommonEmitter(Circuit):
    def __init__(self, transistor=Transistor):
        super().__init__()
        self.vcc = Net()
        self.gnd = Net()
        self.input = Net()
        self.output = Net()

        q1 = transistor()

        r1 = Resistor0805(1e3)
        r2 = Resistor0805(1e3)
        rc = Resistor0805(1e3)

        self.connections += [
            (r1.p1, rc.p1, self.vcc),
            (self.input, r1.p2, r2.p1, q1.b),
            (r2.p2, q1.e, self.gnd),
            (q1.c, rc.p2, self.output),
        ]


class PinHeader(Connector):
    _footprint = 'Connector_PinHeader_1.00mm:PinHeader_1x{:02}_P1.00mm_Vertical'

    @property
    def footprint(self):
        return self._footprint.format(len(self._pads))


class MyBoard(Board):
    def __init__(self):
        super().__init__()

        power_conn = PinHeader(2)
        input_conn = PinHeader(2)
        output_conn = PinHeader(2)

        common_emitters = [CommonEmitter(transistor=BC548) for i in range(5)]
        capacitors = [Capacitor0805(1e-6, name=f'c{i}') for i in range(4)]

        vcc = power_conn.p1
        gnd = power_conn.p2

        for i, c_e in enumerate(common_emitters):
            self.subcircuits[f'common_emmiter{i}'] = c_e
            self.connections += [(vcc, c_e.vcc, 'VCC'), (gnd, c_e.gnd, 'GND')]

        for left, cap, right in zip(common_emitters, capacitors, common_emitters[1::]):
            self.connections += [
                (left.output, cap.p1),
                (cap.p2, right.input),
            ]

        self.input = common_emitters[0].input
        self.output = common_emitters[-1].output

        self.connections += [
            (gnd, input_conn.p2, output_conn.p2),
            (input_conn.p1, self.input, 'INPUT'),
            (output_conn.p1, self.output, 'OUTPUT'),
        ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', type=str, required=True, help='Output netlist file')
    args = parser.parse_args()

    myboard = MyBoard()
    components_map = None
    if os.path.exists(args.file):
        with open(args.file) as f:
            netlist = read_netlist(f.read())
        components_map = {}
        for c in netlist['export']['components']:
            components_map[c['hierarchy']] = c['ref']

    netlist = generate_netlist(
        myboard,
        components_map=components_map
    )

    with open(args.file, 'w') as f:
        f.write(netlist)


if __name__ == '__main__':
    main()
