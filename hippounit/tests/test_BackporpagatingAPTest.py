from quantities.quantity import Quantity
import sciunit
from sciunit import Test,Score,ObservationError
import hippounit.capabilities as cap
from sciunit.utils import assert_dimensionless# Converters.
from sciunit.scores import BooleanScore,ZScore # Scores.

try:
    import numpy
except:
    print("NumPy not loaded.")

import matplotlib.pyplot as plt
import matplotlib
#from neuron import h
import collections
import efel
import os
import multiprocessing
import multiprocessing.pool
import functools
import math
from scipy import stats

import json
from hippounit import plottools
import collections


try:
    import cPickle as pickle
except:
    import pickle
import gzip

try:
    import copy_reg
except:
    import copyreg

from types import MethodType

from quantities import mV, nA, ms, V, s

from hippounit import scores

def _pickle_method(method):
    func_name = method.im_func.__name__
    obj = method.im_self
    cls = method.im_class
    return _unpickle_method, (func_name, obj, cls)

def _unpickle_method(func_name, obj, cls):
    for cls in cls.mro():
        try:
            func = cls.__dict__[func_name]
        except KeyError:
            pass
        else:
            break
    return func.__get__(obj, cls)


try:
	copyreg.pickle(MethodType, _pickle_method, _unpickle_method)
except:
	copy_reg.pickle(MethodType, _pickle_method, _unpickle_method)


class BackpropagatingAPTest(Test):
    """Tests if the model enters depolarization block under current injection of increasing amplitudes."""

    def __init__(self, config = {},
                observation = {"mean_AP1_amp_at_50um" : None,
                 "std_AP1_amp_at_50um" : None,
                 "mean_AP1_amp_at_150um" : None,
                 "std_AP1_amp_at_150um" : None,
                 "mean_AP1_amp_at_250um" : None,
                 "std_AP1_amp_at_250um" : None,
                 "mean_AP1_amp_strong_propagating_at_350um" : None,
                 "std_AP1_amp_strong_propagating_at_350um" : None,
                 "mean_AP1_amp_weak_propagating_at_350um" : None,
                 "std_AP1_amp_weak_propagating_at_350um" : None,

                 "mean_APlast_amp_at_50um" : None,
                 "std_APlast_amp_at_50um" : None,
                 "mean_APlast_amp_at_150um" : None,
                 "std_APlast_amp_at_150um" : None,
                 "mean_APlast_amp_at_250um" : None,
                 "std_APlast_amp_at_250um" : None,
                 "mean_APlast_amp_at_350um" : None,
                 "std_APlast_amp_at_350um" : None},

                name="Back-propagating action potential test" ,
                force_run=False,
                force_run_FindCurrentStim=False,
                base_directory= '/home/osboxes/BBP_project/150904_neuronunit/neuronunit_MAGAMNAK/',
                show_plot=True):

        Test.__init__(self,observation,name)

        self.required_capabilities += (cap.ReceivesSquareCurrent_ProvidesResponse_MultipleLocations,
                                        cap.ProvidesRecordingLocationsOnTrunk, cap.ReceivesSquareCurrent_ProvidesResponse,)

        self.force_run = force_run
        self.force_run_FindCurrentStim = force_run_FindCurrentStim
        self.directory = base_directory + 'temp_data/'
        self.directory_results = base_directory + 'results/'
        self.directory_figs = base_directory + 'figs/'

        self.show_plot = show_plot

        self.path_temp_data = None #added later, because model name is needed
        self.path_figs = None
        self.path_results = None

        self.npool = 4

        self.config = config


        description = "Tests the mode and efficacy of back-propagating action potentials on the apical trunk."

    score_type = scores.ZScore_backpropagatingAP

    def spikecount(self, delay, duration, soma_trace):

        trace = {}
        traces=[]
        trace['T'] = soma_trace[0]
        trace['V'] = soma_trace[1]
        trace['stim_start'] = [delay]
        trace['stim_end'] = [delay + duration]
        traces.append(trace)

        traces_results = efel.getFeatureValues(traces, ['Spikecount'])

        spikecount = traces_results[0]['Spikecount']

        return spikecount

    def binsearch(self, model, stim_range, delay, dur, section_stim, loc_stim, section_rec, loc_rec):
        c_minmax = stim_range
        c_step_start = 0.01
        c_step_stop= 0.002

        found = False
        spikecounts = []
        amplitudes = []

        while c_step_start >= c_step_stop and not found:

            c_stim = numpy.arange(c_minmax[0], c_minmax[1], c_step_start)

            first = 0
            last = numpy.size(c_stim, axis=0)-1

            while first <= last and not found:

                midpoint = (first + last)//2
                amplitude = c_stim[midpoint]

                result=[]

                pool = multiprocessing.Pool(1, maxtasksperchild = 1)	# I use multiprocessing to keep every NEURON related task in independent processes

                traces= pool.apply(self.run_cclamp_on_soma, args = (model, amplitude, delay, dur, section_stim, loc_stim, section_rec, loc_rec))
                pool.terminate()
                pool.join()
                del pool

                spikecount = self.spikecount(delay, dur, traces)

                amplitudes.append(amplitude)
                spikecounts.append(spikecount)

                #if spikecount >= 10 and spikecount <=20:
                if spikecount == 15:
                    found = True
                else:
                    #if spikecount > 20:
                    if spikecount > 15:
                        last = midpoint-1
                    #elif spikecount < 10:
                    elif spikecount < 15:
                        first = midpoint+1
            c_step_start=c_step_start/2

        if not found:
            amp_index = min(range(len(spikecounts)), key=lambda i: abs(spikecounts[i]-15.0)) # we choose the one that is nearest to 15
            print amp_index
            amplitude = amplitudes[amp_index]


        binsearch_result=[found, amplitude, spikecount]
        #print binsearch_result

        return binsearch_result

    def run_cclamp_on_soma(self, model, amp, delay, dur, section_stim, loc_stim, section_rec, loc_rec):

        self.path_temp_data = self.directory + model.name + '/backpropagating_AP/'

        try:
            if not os.path.exists(self.path_temp_data):
                os.makedirs(self.path_temp_data)
        except OSError, e:
            if e.errno != 17:
                raise
            pass

        file_name = self.path_temp_data + 'soma_traces' + str(amp) + '_nA.p'


        if self.force_run_FindCurrentStim or (os.path.isfile(file_name) is False):
            t, v = model.get_vm(amp, delay, dur, section_stim, loc_stim, section_rec, loc_rec)

            pickle.dump([t, v], gzip.GzipFile(file_name, "wb"))


        else:
            [t, v] = pickle.load(gzip.GzipFile(file_name, "rb"))

        return [t, v]


    def find_current_amp(self, model, delay, dur, section_stim, loc_stim, section_rec, loc_rec):

        print 'Finding appropriate current step amplitude...'

        amps = numpy.arange(0.0, 1.1, 0.1)
        #amps= [0.0, 0.2, 0.8]
        #amps=[0.0,0.3,0.8]
        #amps=[0.0,0.2, 0.9]

        pool = multiprocessing.Pool(self.npool, maxtasksperchild=1)


        run_cclamp_on_soma_ = functools.partial(self.run_cclamp_on_soma, model, delay=delay, dur=dur, section_stim=section_stim, loc_stim=loc_stim, section_rec=section_rec, loc_rec=loc_rec)
        traces = pool.map(run_cclamp_on_soma_, amps, chunksize=1)

        pool.terminate()
        pool.join()
        del pool

        spikecounts = []
        _spikecounts = []
        amplitudes = []
        amplitude = None
        spikecount = None

        for i in range(len(traces)):
            spikecounts.append(self.spikecount(delay, dur, traces[i]))


        if amps[0] == 0.0 and  spikecounts[0] > 0:
            print 'Spontaneous firing'
            amplitude = None
            """TODO: stop the whole thing"""

        elif max(spikecounts) < 10:
            print 'The model fired at ' + str(max(spikecounts)[0]) + ' Hz to ' + str(amps[-1]) + ' nA current step, and did not reach 10 Hz firing rate as supposed (according to Bianchi et al 2012 Fig. 1 B eg.)'
            amplitude = None

        else:
            for i in range(len(spikecounts)):

                if i != len(spikecounts)-1:
                    if spikecounts[i] >= 10 and spikecounts[i] <= 20 and (spikecounts[i-1] <= spikecounts[i] and spikecounts[i+1] >= spikecounts[i]):
                        amplitudes.append(amps[i])
                        _spikecounts.append(spikecounts[i])
                    elif spikecounts[i] < 10 and spikecounts[i+1] > 20 and (spikecounts[i-1] <= spikecounts[i] and spikecounts[i+1] >= spikecounts[i]):
                        binsearch_result = self.binsearch(model, [amps[i], amps[i+1]], delay, dur, section_stim, loc_stim, section_rec, loc_rec)
                        amplitude = binsearch_result[1]
                        spikecount = binsearch_result[2]
                else: # there is no spikecounts[i+1] in this case
                    if spikecounts[i] >= 10 and spikecounts[i] <= 20 and spikecounts[i-1] <= spikecounts[i]:
                        amplitudes.append(amps[i])
                        _spikecounts.append(spikecounts[i])
        if len(amplitudes) > 1:
            amp_index = min(range(len(_spikecounts)), key=lambda i: abs(_spikecounts[i]-15.0)) # we choose the one that is nearest to 15
            amplitude = amplitudes[amp_index]
            spikecount = _spikecounts[amp_index]

        elif len(amplitudes) == 1:
            amplitude = amplitudes[0]
            spikecount = _spikecounts[0]
        # if len(amplitudes) remained 0, binsearch found an amplitude

        plt.figure()
        plt.plot(amps, spikecounts, 'o')
        if amplitude is not None and spikecount is not None:
            plt.plot(amplitude, spikecount, 'o')
        plt.ylabel('Spikecount')
        plt.xlabel('current amplitude (nA)')

        return amplitude


    def cclamp(self, model, amp, delay, dur, section_stim, loc_stim, dend_locations):

        self.path_temp_data = self.directory + model.name + '/backpropagating_AP/'

        try:
            if not os.path.exists(self.path_temp_data):
                os.makedirs(self.path_temp_data)
        except OSError, e:
            if e.errno != 17:
                raise
            pass

        file_name = self.path_temp_data + 'cclamp_' + str(amp) + '.p'

        traces = {}

        if self.force_run or (os.path.isfile(file_name) is False):
            t, v_stim, v = model.get_multiple_vm(amp, delay, dur, section_stim, loc_stim, dend_locations)

            traces['T'] = t
            traces['v_stim'] = v_stim
            traces['v_rec'] = v #dictionary key: distance, value : corresponding V trace of each recording locations

            pickle.dump(traces, gzip.GzipFile(file_name, "wb"))

        else:
            traces = pickle.load(gzip.GzipFile(file_name, "rb"))

        return traces

    def extract_somatic_spiking_features(self, traces, delay, duration):

        # soma
        trace = {}
        traces_for_efel=[]
        trace['T'] = traces['T']
        trace['V'] = traces['v_stim']
        trace['stim_start'] = [delay]
        trace['stim_end'] = [delay + duration]
        traces_for_efel.append(trace)

        # trunk locations
        '''
        for key in traces['v_rec']:
            for k in traces['v_rec'][key]:
                trace = {}
                trace['T'] = traces['T']
                trace['V'] = traces['v_rec'][key][k]
                trace['stim_start'] = [delay]
                trace['stim_end'] = [delay + duration]
                traces_for_efel.append(trace)
        '''

        efel.setDoubleSetting('interp_step', 0.025)
        efel.setDoubleSetting('DerivativeThreshold', 40.0)

        traces_results = efel.getFeatureValues(traces_for_efel, ['inv_first_ISI','AP_begin_time', 'doublet_ISI'])

        return traces_results

    def extract_amplitudes(self, traces, traces_results, actual_distances):

        #soma_AP_begin_indices = traces_results[0]['AP_begin_indices']

        soma_AP_begin_time = traces_results[0]['AP_begin_time']
        #soma_inv_first_ISI = traces_results[0]['inv_first_ISI']
        soma_first_ISI = traces_results[0]['doublet_ISI'][0]
        #print soma_AP_begin_time[0], soma_AP_begin_time[0]-1
        #print traces_results[0]['inv_first_ISI'], soma_first_ISI
        s_indices_AP1 = numpy.where(traces['T'] >= (soma_AP_begin_time[0]-1.0))
        if 10 < soma_first_ISI:
            plus = 10
        else:
            plus = soma_first_ISI-3
        e_indices_AP1 = numpy.where(traces['T'] >= (soma_AP_begin_time[0]+plus))
        start_index_AP1 = s_indices_AP1[0][0]
        end_index_AP1 = e_indices_AP1[0][0]
        #print start_index_AP1
        #print end_index_AP1

        s_indices_APlast = numpy.where(traces['T'] >= soma_AP_begin_time[-1]-1.0)
        e_indices_APlast = numpy.where(traces['T'] >= soma_AP_begin_time[-1]+10)
        start_index_APlast = s_indices_APlast[0][0]
        end_index_APlast = e_indices_APlast[0][0]

        features = collections.OrderedDict()

        for key, value in traces['v_rec'].iteritems():
            features[key] = collections.OrderedDict()
            for k, v in traces['v_rec'][key].iteritems():
                features[key][k] = collections.OrderedDict()

                features[key][k]['AP1_amp']= float(numpy.amax(traces['v_rec'][key][k][start_index_AP1:end_index_AP1]) - traces['v_rec'][key][k][start_index_AP1])*mV
                features[key][k]['APlast_amp']= float(numpy.amax(traces['v_rec'][key][k][start_index_APlast:end_index_APlast]) - traces['v_rec'][key][k][start_index_APlast])*mV
                features[key][k]['actual_distance'] = actual_distances[k]
        '''
        plt.figure()
        plt.plot(traces['T'],traces['v_stim'], 'r', label = 'soma')
        plt.plot(traces['T'][start_index_AP1],traces['v_stim'][start_index_AP1], 'o', label = 'soma')
        plt.plot(traces['T'][end_index_AP1],traces['v_stim'][end_index_AP1], 'o', label = 'soma')
        plt.plot(traces['T'][start_index_APlast],traces['v_stim'][start_index_APlast], 'o', label = 'soma')
        '''
        # zoom to fist AP
        plt.figure()
        plt.plot(traces['T'],traces['v_stim'], 'r', label = 'soma')
        for key, value in traces['v_rec'].iteritems():
            for k, v in traces['v_rec'][key].iteritems():
                #plt.plot(traces['T'],traces['v_rec'][i], label = dend_locations[i][0]+'('+str(dend_locations[i][1])+') at '+str(self.config['recording']['distances'][i])+' um')
                #plt.plot(traces['T'],traces['v_rec'][key], label = dend_locations[key][0]+'('+str(dend_locations[key][1])+') at '+str(key)+' um')
                plt.plot(traces['T'],traces['v_rec'][key][k], label = k[0]+'('+str(k[1])+') at '+str(actual_distances[k])+' um')

        plt.xlabel('time (ms)')
        plt.ylabel('membrane potential (mV)')
        plt.title('First AP')
        plt.xlim(traces['T'][start_index_AP1], traces['T'][end_index_AP1])
        lgd=plt.legend(bbox_to_anchor=(1.0, 1.0), loc = 'upper left')
        plt.savefig(self.path_figs + 'AP1_traces', dpi=600, bbox_extra_artists=(lgd,), bbox_inches='tight')

        # zom to last AP
        plt.figure()
        plt.plot(traces['T'],traces['v_stim'], 'r', label = 'soma')
        for key, value in traces['v_rec'].iteritems():
            for k, v in traces['v_rec'][key].iteritems():
                #plt.plot(traces['T'],traces['v_rec'][i], label = dend_locations[i][0]+'('+str(dend_locations[i][1])+') at '+str(self.config['recording']['distances'][i])+' um')
                #plt.plot(traces['T'],traces['v_rec'][key], label = dend_locations[key][0]+'('+str(dend_locations[key][1])+') at '+str(key)+' um')
                plt.plot(traces['T'],traces['v_rec'][key][k], label = k[0]+'('+str(k[1])+') at '+str(actual_distances[k])+' um')
        plt.xlabel('time (ms)')
        plt.ylabel('membrane potential (mV)')
        plt.title('Last AP')
        plt.xlim(traces['T'][start_index_APlast], traces['T'][end_index_APlast])
        lgd=plt.legend(bbox_to_anchor=(1.0, 1.0), loc = 'upper left')
        plt.savefig(self.path_figs + 'APlast_traces', dpi=600, bbox_extra_artists=(lgd,), bbox_inches='tight')

        return features


    def plot_traces(self, model, traces, dend_locations, actual_distances):

        self.path_figs = self.directory_figs + 'backpropagating_AP/' + model.name + '/'

        try:
            if not os.path.exists(self.path_figs):
                os.makedirs(self.path_figs)
        except OSError, e:
            if e.errno != 17:
                raise
            pass

        print "The figures are saved in the directory: ", self.path_figs

        plt.figure()
        plt.plot(traces['T'],traces['v_stim'], 'r', label = 'soma')
        for key, value in traces['v_rec'].iteritems():
            for k, v in traces['v_rec'][key].iteritems():
                #plt.plot(traces['T'],traces['v_rec'][i], label = dend_locations[i][0]+'('+str(dend_locations[i][1])+') at '+str(self.config['recording']['distances'][i])+' um')
                #plt.plot(traces['T'],traces['v_rec'][key], label = dend_locations[key][0]+'('+str(dend_locations[key][1])+') at '+str(key)+' um')
                plt.plot(traces['T'],traces['v_rec'][key][k], label = k[0]+'('+str(k[1])+') at '+str(actual_distances[k])+' um')

        plt.xlabel('time (ms)')
        plt.ylabel('membrane potential (mV)')
        lgd=plt.legend(bbox_to_anchor=(1.0, 1.0), loc = 'upper left')
        plt.savefig(self.path_figs + 'traces', dpi=600, bbox_extra_artists=(lgd,), bbox_inches='tight')


    def plot_features(self, model, features, actual_distances):

        self.path_figs = self.directory_figs + 'backpropagating_AP/' + model_name_bAP + '/'

        observation = self.observation

        try:
            if not os.path.exists(self.path_figs):
                os.makedirs(self.path_figs)
        except OSError, e:
            if e.errno != 17:
                raise
            pass

        model_AP1_amps = numpy.array([])
        model_APlast_amps = numpy.array([])
        exp_mean_AP1_amps_StrongProp = numpy.array([])
        exp_mean_AP1_amps_WeakProp = numpy.array([])
        exp_mean_APlast_amps = numpy.array([])
        exp_std_AP1_amps_StrongProp = numpy.array([])
        exp_std_AP1_amps_WeakProp = numpy.array([])
        exp_std_APlast_amps = numpy.array([])

        distances = []
        dists = numpy.array(self.config['recording']['distances'])
        location_labels = []

        for key, value in features.iteritems():

            if 'mean_AP1_amp_strong_propagating_at_'+str(key)+'um' in observation.keys() or 'mean_AP1_amp_weak_propagating_at_'+str(key)+'um' in observation.keys():
                exp_mean_AP1_amps_StrongProp = numpy.append(exp_mean_AP1_amps_StrongProp, observation['mean_AP1_amp_strong_propagating_at_'+str(key)+'um'])
                exp_std_AP1_amps_StrongProp = numpy.append(exp_std_AP1_amps_StrongProp, observation['std_AP1_amp_strong_propagating_at_'+str(key)+'um'])

                exp_mean_AP1_amps_WeakProp = numpy.append(exp_mean_AP1_amps_WeakProp, observation['mean_AP1_amp_weak_propagating_at_'+str(key)+'um'])
                exp_std_AP1_amps_WeakProp = numpy.append(exp_std_AP1_amps_WeakProp, observation['std_AP1_amp_weak_propagating_at_'+str(key)+'um'])

            else:
                exp_mean_AP1_amps_WeakProp = numpy.append(exp_mean_AP1_amps_WeakProp, observation['mean_AP1_amp_at_'+str(key)+'um'])
                exp_std_AP1_amps_WeakProp = numpy.append(exp_std_AP1_amps_WeakProp, observation['std_AP1_amp_at_'+str(key)+'um'])
                exp_mean_AP1_amps_StrongProp = numpy.append(exp_mean_AP1_amps_StrongProp, observation['mean_AP1_amp_at_'+str(key)+'um'])
                exp_std_AP1_amps_StrongProp = numpy.append(exp_std_AP1_amps_StrongProp, observation['std_AP1_amp_at_'+str(key)+'um'])

            exp_mean_APlast_amps = numpy.append(exp_mean_APlast_amps, observation['mean_APlast_amp_at_'+str(key)+'um'])
            exp_std_APlast_amps = numpy.append(exp_std_APlast_amps, observation['std_APlast_amp_at_'+str(key)+'um'])

            for k, v in features[key].iteritems() :
                distances.append(actual_distances[k])
                model_AP1_amps = numpy.append(model_AP1_amps, features[key][k]['AP1_amp'])
                model_APlast_amps = numpy.append(model_APlast_amps, features[key][k]['APlast_amp'])
                location_labels.append(k[0]+'('+str(k[1])+')')

        plt.figure()
        for i in range(len(distances)):
            plt.plot(distances[i], model_AP1_amps[i], marker ='o', linestyle='none', label = location_labels[i])
        plt.errorbar(dists, exp_mean_AP1_amps_WeakProp, yerr = exp_std_AP1_amps_WeakProp, marker='o', linestyle='none', label = 'experiment - Weak propagating')
        plt.errorbar(dists, exp_mean_AP1_amps_StrongProp, yerr = exp_std_AP1_amps_StrongProp, marker='o', linestyle='none', label = 'experiment - Strong propagating')
        plt.xlabel('Distance from soma (um)')
        plt.ylabel('AP1_amp (mV)')
        lgd = plt.legend(bbox_to_anchor=(1.0, 1.0), loc = 'upper left')
        plt.savefig(self.path_figs + 'AP1_amps', dpi=600, bbox_extra_artists=(lgd,), bbox_inches='tight')

        plt.figure()
        for i in range(len(distances)):
            plt.plot(distances[i], model_APlast_amps[i], marker ='o', linestyle='none', label = location_labels[i])
        plt.errorbar(dists, exp_mean_APlast_amps, yerr = exp_std_APlast_amps, marker='o', linestyle='none', label = 'experiment')
        plt.xlabel('Distance from soma (um)')
        plt.ylabel('APlast_amp (mV)')
        lgd = plt.legend(bbox_to_anchor=(1.0, 1.0), loc = 'upper left')
        plt.savefig(self.path_figs + 'APlast_amps', dpi=600, bbox_extra_artists=(lgd,), bbox_inches='tight')

    def plot_results(self, observation, prediction, errors, model_name_bAP):

        self.path_figs = self.directory_figs + 'backpropagating_AP/' + model_name_bAP + '/'

        try:
            if not os.path.exists(self.path_figs):
                os.makedirs(self.path_figs)
        except OSError, e:
            if e.errno != 17:
                raise
            pass

        # Mean absolute feature values plot
        distances = numpy.array(self.config['recording']['distances'])

        model_mean_AP1_amps = numpy.array([])
        model_mean_APlast_amps = numpy.array([])
        model_std_AP1_amps = numpy.array([])
        model_std_APlast_amps = numpy.array([])
        exp_mean_AP1_amps_StrongProp = numpy.array([])
        exp_mean_AP1_amps_WeakProp = numpy.array([])
        exp_mean_APlast_amps = numpy.array([])
        exp_std_AP1_amps_StrongProp = numpy.array([])
        exp_std_AP1_amps_WeakProp = numpy.array([])
        exp_std_APlast_amps = numpy.array([])

        for i in range(len(distances)):
            model_mean_AP1_amps = numpy.append(model_mean_AP1_amps, prediction['model_AP1_amp_at_'+str(distances[i])+'um']['mean'])
            model_mean_APlast_amps = numpy.append(model_mean_APlast_amps, prediction['model_APlast_amp_at_'+str(distances[i])+'um']['mean'])
            model_std_AP1_amps = numpy.append(model_std_AP1_amps, prediction['model_AP1_amp_at_'+str(distances[i])+'um']['std'])
            model_std_APlast_amps = numpy.append(model_std_APlast_amps, prediction['model_APlast_amp_at_'+str(distances[i])+'um']['std'])

            if 'mean_AP1_amp_strong_propagating_at_'+str(distances[i])+'um' in observation.keys() or 'mean_AP1_amp_weak_propagating_at_'+str(distances[i])+'um' in observation.keys():
                exp_mean_AP1_amps_StrongProp = numpy.append(exp_mean_AP1_amps_StrongProp, observation['mean_AP1_amp_strong_propagating_at_'+str(distances[i])+'um'])
                exp_std_AP1_amps_StrongProp = numpy.append(exp_std_AP1_amps_StrongProp, observation['std_AP1_amp_strong_propagating_at_'+str(distances[i])+'um'])

                exp_mean_AP1_amps_WeakProp = numpy.append(exp_mean_AP1_amps_WeakProp, observation['mean_AP1_amp_weak_propagating_at_'+str(distances[i])+'um'])
                exp_std_AP1_amps_WeakProp = numpy.append(exp_std_AP1_amps_WeakProp, observation['std_AP1_amp_weak_propagating_at_'+str(distances[i])+'um'])

            else:
                exp_mean_AP1_amps_WeakProp = numpy.append(exp_mean_AP1_amps_WeakProp, observation['mean_AP1_amp_at_'+str(distances[i])+'um'])
                exp_std_AP1_amps_WeakProp = numpy.append(exp_std_AP1_amps_WeakProp, observation['std_AP1_amp_at_'+str(distances[i])+'um'])
                exp_mean_AP1_amps_StrongProp = numpy.append(exp_mean_AP1_amps_StrongProp, observation['mean_AP1_amp_at_'+str(distances[i])+'um'])
                exp_std_AP1_amps_StrongProp = numpy.append(exp_std_AP1_amps_StrongProp, observation['std_AP1_amp_at_'+str(distances[i])+'um'])

            exp_mean_APlast_amps = numpy.append(exp_mean_APlast_amps, observation['mean_APlast_amp_at_'+str(distances[i])+'um'])
            exp_std_APlast_amps = numpy.append(exp_std_APlast_amps, observation['std_APlast_amp_at_'+str(distances[i])+'um'])

        plt.figure()
        plt.errorbar(distances, model_mean_AP1_amps, yerr = model_std_AP1_amps, marker ='o', linestyle='none', label = model_name_bAP)
        plt.errorbar(distances, exp_mean_AP1_amps_WeakProp, yerr = exp_std_AP1_amps_WeakProp, marker='o', linestyle='none', label = 'experiment - Weak propagating')
        plt.errorbar(distances, exp_mean_AP1_amps_StrongProp, yerr = exp_std_AP1_amps_StrongProp, marker='o', linestyle='none', label = 'experiment - Strong propagating')
        plt.xlabel('Distance from soma (um)')
        plt.ylabel('AP1_amp (mV)')
        plt.legend(loc=0)
        plt.savefig(self.path_figs + 'AP1_amp_means', dpi=600,)

        plt.figure()
        plt.errorbar(distances, model_mean_APlast_amps, yerr = model_std_APlast_amps, marker ='o', linestyle='none', label = model_name_bAP)
        plt.errorbar(distances, exp_mean_APlast_amps, yerr = exp_std_APlast_amps, marker='o', linestyle='none', label = 'experiment')
        plt.xlabel('Distance from soma (um)')
        plt.ylabel('APlast_amp (mV)')
        plt.legend(loc=0)
        plt.savefig(self.path_figs + 'APlast_amp_means', dpi=600,)


        # Plot of errors

        keys = []
        values = []

        #fig, ax = plt.subplots()
        plt.figure()
        for key, value in errors.iteritems():
            keys.append(key)
            values.append(value)
        y=range(len(keys))
        y.reverse()
        #ax.set_yticks(y)
        #print keys
        #print values
        plt.plot(values, y, 'o')
        plt.yticks(y, keys)
        plt.savefig(self.path_figs + 'bAP_errors', bbox_inches='tight')

    def validate_observation(self, observation):

        for key, value in observation.iteritems():
            try:
                assert type(observation[key]) is Quantity
            except Exception as e:
                raise ObservationError(("Observation must be of the form "
                                        "{'mean':float*mV,'std':float*mV}"))

    def generate_prediction(self, model, verbose=False):
        """Implementation of sciunit.Test.generate_prediction."""

        global model_name_bAP
        model_name_bAP = model.name

        distances = self.config['recording']['distances']

        dend_locations, actual_distances = model.find_trunk_locations_multiproc(distances)
        #print dend_locations, actual_distances

        traces={}
        delay = self.config['stimulus']['delay']
        duration = self.config['stimulus']['duration']
        #amplitude = self.config['stimulus']['amplitude']

        prediction = collections.OrderedDict()

        #plt.close('all') #needed to avoid overlapping of saved images when the test is run on multiple models in a for loop
        plt.close('all') #needed to avoid overlapping of saved images when the test is run on multiple models

        amplitude = self.find_current_amp(model, delay, duration, "soma", 0.5, "soma", 0.5)

        pool = multiprocessing.Pool(1, maxtasksperchild = 1)
        traces = pool.apply(self.cclamp, args = (model, amplitude, delay, duration, "soma", 0.5, dend_locations))


        #plt.close('all') #needed to avoid overlapping of saved images when the test is run on multiple models

        self.plot_traces(model, traces, dend_locations, actual_distances)

        traces_results = self.extract_somatic_spiking_features(traces, delay, duration)


        features = self.extract_amplitudes(traces, traces_results, actual_distances)

        features_json = collections.OrderedDict()
        for key in features:
            features_json[key] = collections.OrderedDict()
            for ke in features[key]:
                features_json[key][str(ke)] = collections.OrderedDict()
                for k, value in features[key][ke].iteritems():
                    features_json[key][str(ke)][k] = str(value)


        # generating prediction
        for key in features:
            AP1_amps = numpy.array([])
            APlast_amps = numpy.array([])

            for k in features[key]:
                AP1_amps = numpy.append(AP1_amps, features[key][k]['AP1_amp'] )
            prediction['model_AP1_amp_at_'+str(key)+'um'] = {}
            prediction['model_AP1_amp_at_'+str(key)+'um']['mean'] = float(numpy.mean(AP1_amps))*mV
            prediction['model_AP1_amp_at_'+str(key)+'um']['std'] = float(numpy.std(AP1_amps))*mV

        for key in features:
            AP1_amps = numpy.array([])
            APlast_amps = numpy.array([])
            for k in features[key]:
                APlast_amps = numpy.append(APlast_amps, features[key][k]['APlast_amp'] )
            prediction['model_APlast_amp_at_'+str(key)+'um'] = {}
            prediction['model_APlast_amp_at_'+str(key)+'um']['mean'] = float(numpy.mean(APlast_amps))*mV
            prediction['model_APlast_amp_at_'+str(key)+'um']['std'] = float(numpy.std(APlast_amps))*mV

        prediction_json = collections.OrderedDict()
        for key in prediction:
            prediction_json[key] = collections.OrderedDict()
            for k, value in prediction[key].iteritems():
                prediction_json[key][k]=str(value)

        self.path_results = self.directory_results + model.name + '/'

        try:
            if not os.path.exists(self.path_results):
                os.makedirs(self.path_results)
        except OSError, e:
            if e.errno != 17:
                raise
            pass

        file_name_json = self.path_results + 'bAP_model_features_means.json'
        json.dump(prediction_json, open(file_name_json, "wb"), indent=4)
        file_name_features_json = self.path_results + 'bAP_model_features.json'
        json.dump(features_json, open(file_name_features_json, "wb"), indent=4)

        file_name_pickle = self.path_results + 'bAP_model_features.p'

        pickle.dump(features, gzip.GzipFile(file_name_pickle, "wb"))

        file_name_pickle = self.path_results + 'bAP_model_features_means.p'

        pickle.dump(prediction, gzip.GzipFile(file_name_pickle, "wb"))

        self.plot_features(model, features, actual_distances)

        return prediction

    def compute_score(self, observation, prediction, verbose=False):
        """Implementation of sciunit.Test.score_prediction."""

        distances = numpy.array(self.config['recording']['distances'])
        #score_sum_StrongProp, score_sum_WeakProp  = scores.ZScore_backpropagatingAP.compute(observation,prediction, [50, 150, 250])
        score_sums, errors= scores.ZScore_backpropagatingAP.compute(observation,prediction, distances)

        scores_dict = {}
        scores_dict['Z_score_strong_propagating'] = score_sums[0]
        scores_dict['Z_score_weak_propagating'] = score_sums[1]

        self.path_results = self.directory_results + model_name_bAP + '/'

        try:
            if not os.path.exists(self.path_results):
                os.makedirs(self.path_results)
        except OSError, e:
            if e.errno != 17:
                raise
            pass

        file_name=self.path_results+'bAP_errors.json'

        json.dump(errors, open(file_name, "wb"), indent=4)

        file_name_s=self.path_results+'bAP_scores.json'

        json.dump(scores_dict, open(file_name_s, "wb"), indent=4)

        self.plot_results(observation, prediction, errors, model_name_bAP)

        if self.show_plot:
            plt.show()

        score=scores.ZScore_backpropagatingAP(score_sums)
        return score
    '''
    def bind_score(self, score, model, observation, prediction):

        score.related_data["figures"] = [self.path_figs + 'Ith.pdf', self.path_figs + 'Veq.pdf', self.path_figs + 'number_of_APs.pdf', self.path_figs + 'num_of_APs_at_Ith.pdf', self.path_figs + 'somatic_resp_at_depol_block.pdf', self.path_figs + 'somatic_resp_at_Ith.pdf']
        score.related_data["results"] = [self.path_results + 'depol_block_model_errors.json', self.path_results + 'depol_block_model_features.json']
        return score
    '''
