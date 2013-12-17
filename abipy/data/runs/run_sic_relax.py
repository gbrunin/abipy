#!/usr/bin/env python
"""Structural relaxation for SiC."""
from __future__ import division, print_function

import sys
import os
import numpy as np

import abipy.abilab as abilab
import abipy.data as data

from abipy.data.runs import AbipyTest, MixinTest

class SicRelaxFlowTest(AbipyTest, MixinTest):
    """
    Unit test for the flow defined in this module.  
    Users who just want to learn how to use this flow can ignore this section.
    """
    def setUp(self):
        super(SicRelaxFlowTest, self).setUp()
        self.init_dirs()
        self.flow = build_flow()

def build_flow(options):
    # Working directory (default is the name of the script with '.py' removed and "run_" replaced by "flow_")
    workdir = options.workdir
    if not options.workdir 
        workdir = os.path.basename(__file__).replace(".py", "").replace("run_","flow_") 

    # Instantiate the TaskManager.
    manager = abilab.TaskManager.from_user_config() if not options.manager else options.manager

    flow = abilab.AbinitFlow(workdir, manager)

    pseudos = data.pseudos("14si.pspnc", "6c.pspnc")
    structure = data.structure_from_ucell("SiC")

    global_vars = dict(
        chksymbreak=0,
        ecut=20,
        paral_kgb=0,
    )

    ngkpt = [4,4,4]
    shiftk = [[0.5,0.5,0.5],
              [0.5,0.0,0.0],
              [0.0,0.5,0.0],
              [0.0,0.0,0.5]]


    inp = abilab.AbiInput(pseudos=pseudos, ndtset=2)
    inp.set_structure(structure)
    inp.set_variables(**global_vars)

    relax_inp, nscf_inp = inp[1:]

    relax_inp.set_kmesh(ngkpt=ngkpt, shiftk=shiftk)
    relax_inp.set_variables(
        toldff=1e-6,
        tolmxf=1e-5,
        strfact=100,
        ecutsm=0.5,
        dilatmx=1.15,
        ntime=100,
        ionmov=2,
        optcell=1,
    )

    nscf_inp.set_kpath(ndivsm=20)
    nscf_inp.tolwfr = 1e-22

    relax_inp, nscf_inp = inp.split_datasets()

    # Initialize the workflow.
    relax_task = flow.register_task(relax_inp, task_class=abilab.RelaxTask)

    #work = RelaxWorkflow(self, ion_input, ioncell_input, workdir=None, manager=None):

    nscf_task = flow.register_task(nscf_inp, deps={relax_task: "DEN"}, task_class=abilab.NscfTask)

    return flow.allocate()


@abilab.flow_main
def main(options):
    flow = build_flow(options)
    return flow.build_and_pickle_dump()


if __name__=="__main__":
    sys.exit(main())

