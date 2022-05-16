# PYPCB

![lint](https://github.com/andresdemski/pypcb/actions/workflows/lint.yml/badge.svg)

The Hardware design workflow has many issues like:
* Collaboration
* Version control
* Reusability
* Scalability
* Testing

pypcb is trying to resolve those problems. Pypcb is a python framework inspired by
[Amaranth](https://github.com/amaranth-lang/amaranth) that can be used to design printed circuit boards (PCB)
with a "software" approach. The main idea behind pypcb is to introduce some good practices of the software
workflow into the hardware design world like unit testing, version control, CI/CD, etc.

## Installation

```
pip install git+https://github.com/andresdemski/pypcb.git
```

## Roadmap

* [x] python to kicad netlist 
* [x] Cache components references from existing netlist (able to modify an existing layout)
* [ ] Add attributes to elements: power, impedance, values, part, etc
* [ ] Generate BOM
* [ ] Generate kicad project
* [ ] ngspice backend to simulate (unit tests)
* [ ] Footprint as code
* [ ] Placer
* [ ] Router
