"""SciUnit capability classes for NeuronUnit.
The goal is to enumerate all possible capabilities of a model
that would be tested using NeuronUnit.
These capabilities exchange 'neo' objects."""

import numpy as np

import sciunit
from sciunit import Capability
import multiprocessing

class ReceivesSquareCurrent(sciunit.Capability):
	"""Indicates that current can be injected into the model as
    a square pulse. """

	def inject_current(self, amp, delay, dur, section_stim, loc_stim, section_rec, loc_rec):
		""" Must return numpy arrays containing the time and voltage values"""
		raise NotImplementedError()

	def get_vm(self, amp, delay, dur, section_stim, loc_stim, section_rec, loc_rec):

		t, v = self.inject_current(amp, delay, dur, section_stim, loc_stim, section_rec, loc_rec)
		return t, v

class ProvidesGoodObliques(sciunit.Capability):
	""" Indicates that the model provides a list of oblique dendrites and locations to be tested"""

	def find_good_obliques(self):
		""" Must provide a list of oblique dendrites
		that meet the criteria of the experimental protocol (Losonczy, Magee 2006),
		and also proximal and distal locations on them.
		Criteria: originate from the trunk, have no child, close to the soma (at most 120 microns)
		The form must be: dend_loc = [['name_of_dend1',prox_location],['name_of_dend1',dist_location],['name_of_dend2',prox_location] ['name_of_dend2',dist_location]]
		E.g. : [['CCell[0].apic[47]', 0.5], ['CCell[0].apic[47]', 0.8333333333333333]] """

		raise NotImplementedError()

	def find_obliques_multiproc(self):
		""" Used to keep all NEURON related tasks in independent processes, to avoid errors like 'template can not be redefined'"""
		pool_obl = multiprocessing.Pool(1, maxtasksperchild = 1)
		self.dend_loc = pool_obl.apply(self.find_good_obliques)  # this way model.dend_loc gets the values
		pool_obl.terminate()
		pool_obl.join()
		del pool_obl

class ReceivesSynapse(sciunit.Capability):
	"""Indicates that the model receives synapse"""

	def run_syn(self, dend_loc, interval, number, AMPA_weight):
		""" Must return numpy arrays containing the time and voltage values (at the soma and at the synaptic location )"""
		raise NotImplementedError()

	def run_synapse_get_vm(self, dend_loc, interval, number, AMPA_weight):

		t, v, v_dend = self.run_syn(dend_loc, interval, number, AMPA_weight)

		return t, v, v_dend
