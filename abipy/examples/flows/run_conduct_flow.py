#!/usr/bin/env python
from __future__ import print_function, division, unicode_literals, absolute_import

import os
import sys
import abipy.data as abidata
import abipy.abilab as abilab
import copy
from abipy import flowtk
import pymatgen.io.abinit as pmgFlow


def make_scf_input(structure, pseudos, ngkpt=(2,2,2), shiftk=(0,0,0),
                   **variables):
    """Build and return SCF input given the structure and pseudopotentials"""

    scf_inp = abilab.AbinitInput(structure, pseudos=pseudos)

    # Global variables
    scf_inp.set_vars(**variables)

    # Dataset 1 (GS run)
    scf_inp.set_kmesh(ngkpt=ngkpt, shiftk=shiftk)
    #scf_inp.set_vars(toldfe=1e-10)

    return scf_inp

def make_nscf_input(structure, pseudos, ngkpt=(2,2,2), shiftk=(0,0,0),
                    **variables):
    """Build and return NSCF input given the structure and pseudopotentials"""

    scf_inp = abilab.AbinitInput(structure, pseudos=pseudos)

    # Global variables
    scf_inp.set_vars(**variables)

    # Dataset 1 (GS run)
    scf_inp.set_kmesh(ngkpt=ngkpt, shiftk=shiftk)
    scf_inp.set_vars(iscf=-2)

    return scf_inp




def build_flow(options):
    # Working directory (default is the name of the script with '.py' removed and "run_" replaced by "flow_")
    if not options.workdir:
        options.workdir = os.path.basename(__file__).replace(".py", "").replace("run_", "flow_")
    
    # Get structure and pseudos from the abipy database
    structure = abidata.structure_from_ucell("Al")
    pseudos = abidata.pseudos("13al.pspnc")                                                                                                   

    
    variables = dict(
            ecut = 20,
            tsmear = 0.05,
            nband = 12,
            nbdbuf = 2,
            occopt = 3,
            iomode = 1,
            nstep = 20,
            paral_kgb=1,
        )

    ngkpt = [4, 4, 4]
    ngkpt_fine = [12,12,12]
    shiftk = [0.0, 0.0, 0.0]

    ngqpt = [2,2,2]
    ngqpt_fine = [4,4,4]
    tmesh=[0, 30, 11]
    
    # Nom de mon flow
    flow = flowtk.Flow(workdir=options.workdir)

    #flow.show_inputs()
    
    # Create inputs Object
    scf_input = make_scf_input(structure, pseudos,
                               tolvrs=1e-12,
                               ngkpt=ngkpt,
                               shiftk=shiftk,
                               **variables)

    nscf_input = make_nscf_input(structure, pseudos,
                                 tolwfr=1e-18,
                                 ngkpt=ngkpt_fine,
                                 shiftk=shiftk,
                                 **variables)

    # Create multi which contains inputs for the 4 tasks: SCF, NSCF, Interpolation DVDB, Conductivity
    multi = abilab.make_conduc_work_input(
        scf_input, nscf_input,
        tmesh=tmesh,
        ddb_ngqpt=ngqpt,
        eph_ngqpt_fine=ngqpt_fine)
    

    # Create Work Object

    # Work 0 : Calcul SCF
    gs_work = flowtk.Work()
    gs_work.register_scf_task(scf_input)

    # Work 1 : Calcul DDB et DVDB 
    ph_work = flowtk.PhononWork.from_scf_task(gs_work[0],
                                              qpoints=ngqpt, is_ngqpt=True,
                                              tolerance = {"tolvrs": 1e-8})

    # Work 2 : Conduc Work
    conduc_work = flowtk.ConducWork.from_phwork_and_scf_nscf_inp(
        phwork=ph_work, multi=multi, nbr_procs=4, flow = flow)
   
    # Register Work
    flow.register_work(gs_work)
    flow.register_work(ph_work)
    flow.register_work(conduc_work)
 
    return flow.allocate(use_smartio=True)


@flowtk.flow_main
def main(options):
    """
    This is our main function that will be invoked by the script.
    flow_main is a decorator implementing the command line interface.
    Command line args are stored in `options`.
    """
    return build_flow(options)


if __name__ == "__main__":
    sys.exit(main())

############################################
