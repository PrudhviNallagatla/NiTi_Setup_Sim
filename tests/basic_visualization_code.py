import numpy as np
from ase import Atom, Atoms
from ase.lattice.cubic import SimpleCubicFactory
from ase.io import write, read
from ase.neighborlist import NeighborList
from ase.visualize import view

xyz_path = "/home/rimuru/workspace/data/atomic_models/simulated_models/Ni49.0-Ti51.0/10.0nm/initial.xyz"
atoms = read(xyz_path)

# # View the loaded nanoparticle
view(atoms)
