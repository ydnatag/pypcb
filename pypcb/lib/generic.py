from .. import Component, Pad

class Resistor(Component):
    REF = 'R'
    def __init__(self, value, *, name=None, src_loc_at=0):
        super().__init__(name=name, src_loc_at=src_loc_at + 1)
        self.add_pad('1', 'p1')
        self.add_pad('2', 'p2')
        self.value = value

class Capacitor(Component):
    REF = 'C'
    def __init__(self, value, *, name=None, src_loc_at=0):
        super().__init__(name=name, src_loc_at=src_loc_at + 1)
        self.add_pad('1', 'p1')
        self.add_pad('2', 'p2')
        self.value = value

class Transistor(Component):
    REF = 'Q'
    def __init__(self, *, name=None, src_loc_at=0):
        super().__init__(name=name, src_loc_at=src_loc_at + 1)
        self.add_pad('1', 'b')
        self.add_pad('2', 'c')
        self.add_pad('3', 'e')

class Connector(Component):
    REF = 'J'
    def __init__(self, n, *, name=None, src_loc_at=0):
        super().__init__(name=name, src_loc_at=src_loc_at + 1)
        self.value = self.name
        for i in range(n):
            self.add_pad(f'{i+1}', f'p{i+1}')

