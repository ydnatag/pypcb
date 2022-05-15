from . import tracer
from collections.abc import Iterable

class ConnectionsMannager:
    def __init__(self, circuit):
        self.circuit = circuit
        self._connections = []

    def isvalid(self, *nets):
        return all(isinstance(x, (Net, Pad, str)) for x in nets)

    def __iadd__(self, connections):
        if isinstance(connections, tuple) and self.isvalid(*connections):
            connections = [connections]

        if isinstance(connections, Iterable):
            for connection in connections:
                if self.isvalid(*connection):
                    self._connections.append(connection)
                    for net in connection:
                        if isinstance(net, Pad):
                            net._connected = True
                            if not net._owner._owner:
                                self.circuit.components += net._owner
                else:
                    raise ValueError(f'{connection}')
            return self

    def __iter__(self):
        return iter(self._connections)

class ComponentsMannager:
    def __init__(self, circuit):
        self.circuit = circuit
        self._components = {}

    def __iadd__(self, components):
        if not isinstance(components, Iterable):
            components = [components]

        for component in components:
            if not isinstance(component, Component):
                raise ValueError(f'{component} must be a Component')
            if component.name in self._components:
                raise ValueError(f'Component {component.name} is already in the circuit')

            self._components[component.name] = component
            component._owner = self.circuit
        return self

    def __iter__(self):
        return iter(self._components.items())
        


class CircuitMannager:
    def __init__(self, circuit):
        self.cicuit = circuit
        self._circuits = {}

    def __setitem__(self, field, circuit):
        if not isinstance(circuit, Circuit):
            raise ValueError(f"{circuit} must be a Circuit")
        if field in self._circuits:
            raise ValueError(f"{field} already in use")

        self._circuits[field] = circuit

    def __iter__(self):
        return iter(self._circuits.items())


class Component:
    def __init__(self, *, name=None, src_loc_at=0):
        self.src_loc = tracer.get_src_loc(1 + src_loc_at)
        if name is not None and not isinstance(name, str):
            raise TypeError("Name must be a string, not {!r}".format(name))
        self.name = name or tracer.get_var_name(depth=2 + src_loc_at)
        self._owner = None
        self._pads = []

    def add_pad(self, pin, name):
        pad = Pad(self, name=name, pin=pin)
        setattr(self, name, pad)
        self._pads.append(pad)

    def __str__(self):
        return self.name


class Circuit:
    def __init__(self):
        self._owner = None
        self.connections = ConnectionsMannager(self)
        self.components = ComponentsMannager(self)
        self.subcircuits = CircuitMannager(self)

    def get_nets(self, clean_nets=True):
        def reduce(netlist):
            new_netlist =[]
            reduced = False
            def get_net_index(net):
                for i, n in enumerate(new_netlist):
                    if net in n:
                        return i
                return None
        
            for nets in netlist:
                for net in nets:
                    idx = get_net_index(net)
                    if idx is not None:
                        break
                if idx is None:
                    new_netlist.append(nets)
                else:
                    new_netlist[idx] += nets
                    reduced = True
            return new_netlist, reduced

        def do_clean_nets(netlist):
            return [tuple(set(n for n in node if isinstance(n, (Pad, str)))) for node in netlist]

        nets = list(self.connections)
        for circuit_name, circuit in self.subcircuits:
            nets += circuit.get_nets(clean_nets=False)

        netlist, reduced = reduce(nets)
        while reduced:
            netlist, reduced = reduce(netlist)

        if clean_nets:
            netlist = do_clean_nets(netlist)
        return netlist
        

    def get_components(self):
        components = {component: '/' + name  for name, component in self.components}
        for circuit_name, circuit in self.subcircuits:
            subcircuit_components = circuit.get_components()
            components.update({component: '/' + circuit_name + name for component, name in subcircuit_components.items()})
        return components

    def build(self):
        return self.get_nets(), self.get_components()


class Board(Circuit):
    pass

class Net:
    def __init__(self, *, name=None, src_loc_at=0):
        self.src_loc = tracer.get_src_loc(1 + src_loc_at)
        if name is not None and not isinstance(name, str):
            raise TypeError("Name must be a string, not {!r}".format(name))
        self.name = name or tracer.get_var_name(depth=2 + src_loc_at)
        self._connected = False

    def __repr__(self):
        return self.name + '@' + hex(id(self))

class Pad(Net):
    def __init__(self, owner, name, pin):
        self.name = name
        self.pin = pin
        self._owner = owner
        self._connected = False

    def __repr__(self):
        return str(self._owner) + '.' + self.name + '@' + hex(id(self))
