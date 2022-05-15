from ..lib.generic import Resistor, Capacitor, Transistor
from textwrap import dedent
import jinja2


def read_netlist(netlist):
    assert netlist.count('(') == netlist.count(')')

    def _check_brackets(brackets):
        level = 0
        for b in brackets:
            if b[0] == '(':
                level += 1
            if b[0] == ')':
                level -= 1
            assert level >= 0

    def _find_all(p, s):
        def gen_find_all():
            i = s.find(p)
            while i != -1:
                yield i
                i = s.find(p, i+1)
        return list(gen_find_all())

    def _get_name(start):
        return netlist[start:netlist.find(' ', start)].replace('\n', '')
    
    def _get_value(start, end):
        return netlist[netlist.find(' ', start):end].lstrip().replace('"', '').replace('\n', '')

    def _get_tree(brackets, is_list=False):
        if is_list:
            nodes = []
        else:
            nodes = {}
        start = None
        opened = 0
    
        for i, (b, idx) in enumerate(brackets):
            if b == '(':
                opened += 1
                if start is None:
                    start = i
            if b == ')':
                opened -= 1
                if opened == 0:
                    end = i
                    idx_start = brackets[start][1]+1
                    idx_end = idx
                    name = _get_name(idx_start)

                    if name == 'components' or name == 'nets':
                        value = _get_tree(brackets[start+1:end], is_list=True)
                    elif name == 'node':
                        if 'nodes' not in nodes:
                            nodes['nodes'] = []
                        nodes['nodes'].append(_get_tree(brackets[start+1:end]))
                        start = None
                        continue
                    elif end == start + 1:
                        value = _get_value(idx_start, idx_end)
                    else:
                        value = _get_tree(brackets[start+1:end])
    
                    if is_list:
                        nodes.append(value)
                    else:
                        nodes[name] = value
                    start = None
        return nodes

    left_brackets = _find_all('(', netlist)
    right_brackets = _find_all(')', netlist)
    brackets = sorted(
        [
            *[('(', idx) for idx in left_brackets],
            *[(')', idx) for idx in right_brackets]
        ],
        key=lambda x: x[1]
    )
    _check_brackets(brackets)
    return _get_tree(brackets)

class _Net:
    def __init__(self, name, nodes):
        self.nodes = nodes
        self.name = name

    def __iter__(self):
        return iter(self.nodes)

def generate_netlist(board, components_map=None):
    board_components = board.get_components()
    nets = board.get_nets()

    components_type = set(c.REF for c in board_components.keys())
    current = {t: 1 for t in components_type}
    taken = []
    current_net = 0

    def get_ref(component):
        letter = component.REF
        while True:
            ret = current[letter]
            current[letter] += 1
            ref = letter + str(ret)
            if ref not in taken:
                taken.append(ref)
                return ref

    def get_net_name(net):
        nonlocal current_net
        names = set(n for n in net if isinstance(n, str))
        assert len(names) <= 1

        if len(names) == 0:
            name = 'NET' + str(current_net)
            current_net += 1
            return name
        else:
            return names.pop()

    def get_net_nodes(net):
        return tuple(n for n in net if not isinstance(n, str))
           
    components = {}

    if components_map is not None:
        for component, path in board_components.items():
            if path in components_map:
                ref = components_map[path]
                components[component] = (ref, path)
                taken.append(ref)

    for component, path in board_components.items():
        if (components_map is None) or (path not in components_map):
            components[component] = (get_ref(component), path)


    kicad_netlist = []
    for net in nets:
        name = get_net_name(net)
        nodes = get_net_nodes(net)
        kicad_netlist.append(_Net(name, nodes))

    netlist_template = jinja2.Template(dedent("""
        (export (version "E")
          (design
            (source "thefile")
            (date "date")
            (tool "pypcb")
          )
          (components
            {% for component, (ref, hierarchy) in components.items() %}
            (comp (ref "{{ref}}")
              (value "{{component.value}}")
              (footprint "{{component.footprint}}")
              (hierarchy "{{hierarchy}}")
            )
            {% endfor %}
          )
          (nets
            {% for net in nets %}
            (net (code "{{loop.index}}") (name "{{net.name}}")
              {% for node in net %}
              (node (ref "{{components[node._owner][0]}}") (pin "{{node.pin}}") (pinfunction "{{node.name}}") (pintype "passive"))
              {% endfor %}
            )
            {% endfor %}
          )
        )

        """
    ),  trim_blocks=True,  lstrip_blocks=True)
    return netlist_template.render(components=components, nets=kicad_netlist)
