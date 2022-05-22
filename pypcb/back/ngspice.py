from .. import Component, Net
from pypcb.lib.generic import TransistorBJT, Resistor, Capacitor
import subprocess
import numpy as np


class NgSpice:
    def __init__(self, circuit, gnd):
        self._gnd = gnd
        self.nets = circuit.get_nets(clean_nets=False)
        self.components = circuit.get_components()
        self.process()

    def _get_net_map(self):
        nets_map = {
            n: i + 1
            for i, net in enumerate(self.nets)
            for n in net
        }
        # GND must to be net 0
        for net in self.nets:
            if self._gnd in net:
                for n in net:
                    nets_map[n] = 0
        return nets_map

    def _get_comp_map(self):
        types = set(c.REF for c in self.components.keys())
        current = {t: 1 for t in types}

        def get_ref(component):
            letter = component.REF
            while True:
                ret = current[letter]
                current[letter] += 1
                ref = letter + str(ret)
                return ref

        return {c: get_ref(c) for c in self.components}

    def process(self):
        self._net_map = net_map = self._get_net_map()
        self._comp_map = comp_map = self._get_comp_map()

        models = {}
        circuit = []
        for c in self.components:
            if isinstance(c, TransistorBJT):
                val = f'{comp_map[c]} {net_map[c.c]} {net_map[c.b]} {net_map[c.e]} {c.spice_name}'
            elif isinstance(c, (Resistor, Capacitor, VoltageSource)):
                val = f'{comp_map[c]} {net_map[c.p1]} {net_map[c.p2]} {c.value}'

            if hasattr(c, 'spice_name') and c.spice_name not in models:
                models[c.spice_name] = ' '.join(c.spice_model.split())
            circuit.append(val)

        self.circuit = '\n'.join(list(models.values()) + circuit)

    def get_dot_save(self, trace):
        if isinstance(trace, (tuple, list)):
            for t in trace:
                if not isinstance(t, Net):
                    raise NotImplementedError('Currently only net trace is supported')
            trace = ' '.join(str(self._net_map[t]) for t in trace)
        else:
            raise NotImplementedError('Only net trace for selected nets is supported')
        return f'.save {trace}'

    def run(self, spice):
        process = subprocess.Popen(
            ['ngspice', '-s'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate(spice.encode('utf-8'))
        if process.returncode:
            print(spice.encode('utf-8'))
            raise RuntimeError('Error running ngpsice')
        data = stdout.split(b'Binary:\n')[1]
        data = np.frombuffer(data, dtype=np.float64)
        return data

    @staticmethod
    def get_variables(data, variables):
        n_variables = len(variables)
        rv = {}
        for i, v in enumerate(variables):
            rv[v] = data[i::n_variables]
        return rv

    def dcsweep(self, sweep, trace=None):
        dc_cmd = ['.dc']
        for v, (start, stop, inc) in sweep:
            dc_cmd.append(
                '{} {} {} {}'.format(
                    self._comp_map[v],
                    start,
                    stop,
                    inc,
                )
            )
        spice = '\n'.join([
            'test -s',
            self.circuit,
            self.get_dot_save(trace),
            ' '.join(dc_cmd),
            ".end",
        ])

        data = self.run(spice)
        return self.get_variables(data, [s[0] for s in sweep] + list(trace))

    def transient(self, step, stop, units='ns', trace=None):
        assert units in ['ns', 'us', 'ms', 's']

        tran_cmd = f'.tran {step}{units} {stop}{units}'
        spice = '\n'.join([
            'test -s',
            self.circuit,
            self.get_dot_save(trace),
            tran_cmd,
            ".end",
        ])

        data = self.run(spice)
        variables = ['time'] + list(trace)
        return self.get_variables(data, variables)


class VoltageSource(Component):
    REF = 'V'

    def __init__(self, value, *, name=None, src_loc_at=0):
        super().__init__(name=name, src_loc_at=src_loc_at + 1)
        self.value = value
        self.add_pad('1', 'p1')
        self.add_pad('2', 'p2')
        self.p = self.p1
        self.n = self.p2
