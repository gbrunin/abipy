"""Tests for boltztrap module."""
from __future__ import print_function, division, unicode_literals, absolute_import

import os
import collections
import numpy as np
import abipy.data as abidata

from abipy.core.testing import AbipyTest
from abipy.boltztrap.boltztrap import AbipyBoltztrap, BoltztrapResult
from abipy import abilab


class AbipyBoltztrapTest(AbipyTest):

    # TODO: Need new files with IBZ.
    def test_sigeph_boltztrap(self):
        """Test boltztrap interpolation"""
        sigeph = abilab.abiopen(abidata.ref_file("diamond_444q_full_SIGEPH.nc"))
        
        bt = AbipyBoltztrap.from_sigeph(sigeph)

        # get equivalences
        assert bt.rmesh == (5,5,5)
        assert bt.nequivalences == 5
        
        # get coefficients
        assert bt.ncoefficients == 53

        #get boltztrap results
        btr = bt.run()
        btr.pickle('diamond.npy') 

        fig = btr.plot('vvdos',with_tau=True,show=False)
        fig = btr.plot('powerfactor',itemp_list=[3],with_tau=True,show=False)

