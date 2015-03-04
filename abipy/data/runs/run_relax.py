#!/usr/bin/env python
"""
This script shows how to perform a structural relaxation in two steps:

    1) Relaxation of atomic positions with unit cell parameters fixed.

    2) Full relaxation (atoms + cell) with the initial configuration read from step 1)
"""
from __future__ import division, print_function, unicode_literals

import sys
import os
import abipy.data as abidata  
import abipy.abilab as abilab


def make_ion_ioncell_inputs(paral_kgb=1):
    pseudos = abidata.pseudos("14si.pspnc")
    structure = abilab.Structure.from_file(abidata.cif_file("si.cif"))

    # Perturb the structure (random perturbation of 0.1 Angstrom)
    # then compress the volume to trigger dilatmx.
    structure.perturb(distance=0.1)
    structure.scale_lattice(structure.volume * 0.6)

    global_vars = dict(
        ecut=4,  
        ngkpt=[4,4,4], 
        shiftk=[0,0,0],
        nshiftk=1,
        chksymbreak=0,
        paral_kgb=paral_kgb,
    )

    inp = abilab.AbiInput(pseudos=pseudos, ndtset=2)
    inp.set_structure(structure)

    # Global variables
    inp.set_vars(**global_vars)

    # Dataset 1 (Atom Relaxation)
    inp[1].set_vars(
        optcell=0,
        ionmov=2,
        tolrff=0.02,
        tolmxf=5.0e-5,
        #ntime=50,
        ntime=5,  #To test the restart
        #dilatmx=1.1, # FIXME: abinit crashes if I don't use this
    )

    # Dataset 2 (Atom + Cell Relaxation)
    inp[2].set_vars(
        optcell=1,
        ionmov=2,
        ecutsm=0.5,
        dilatmx=1.02,
        tolrff=0.02,
        tolmxf=5.0e-5,
        strfact=100,
        #ntime=50,
        ntime=5,  # To test the restart
        )

    ion_inp, ioncell_inp = inp.split_datasets()
    return ion_inp, ioncell_inp


def build_flow(options):
    # Working directory (default is the name of the script with '.py' removed and "run_" replaced by "flow_")
    workdir = options.workdir
    if not options.workdir:
        workdir = os.path.basename(__file__).replace(".py", "").replace("run_","flow_") 

    # Instantiate the TaskManager.
    manager = abilab.TaskManager.from_user_config() if not options.manager else \
              abilab.TaskManager.from_file(options.manager)

    # Create the flow
    flow = abilab.Flow(workdir, manager=manager)

    # Create a relaxation work and add it to the flow.
    ion_inp, ioncell_inp = make_ion_ioncell_inputs()

    relax_work = abilab.RelaxWork(ion_inp, ioncell_inp)
    flow.register_work(relax_work)

    #bands_work = abilab.BandStructureWork(scf_input, nscf_input)
    bands_work = abilab.Work()
    deps = {relax_work[-1]: "@structure"}
    bands_work.register_relax_task(ioncell_inp, deps=deps)
    #bands_work.add_deps({relax_work[-1]: "DEN"})
    #bands_work.add_deps({relax_work[-1]: "WFK"})
    #bands_work.add_deps(
    flow.register_work(bands_work)

    return flow.allocate()


@abilab.flow_main
def main(options):
    flow = build_flow(options)
    flow.build_and_pickle_dump()
    return flow


if __name__ == "__main__":
    sys.exit(main())

