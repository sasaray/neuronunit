import os
import numpy
import sciunit
from neuronunit.capabilities import ReceivesCurrent,ProducesMembranePotential
from quantities import ms,mV,Hz
from neuron import h

class Model(sciunit.Model,
                 ReceivesCurrent,
                 ProducesMembranePotential):

    def __init__(self, name="model"):
        """ Constructor. """

        """ This class should be used with Jupyter notebooks"""

        self.modelpath = None
        self.libpath = None
        self.hocpath = None
        self.template_name = None
        self.SomaSecList_name = None
        self.max_dist_from_soma = None

        self.name = name
        self.threshold = -20
        self.stim = None
        self.soma = None
        sciunit.Model.__init__(self, name=name)

        self.c_step_start = 0.00004
        self.c_step_stop = 0.000004
        self.c_minmax = numpy.array([0.00004, 0.004])

        self.ObliqueSecList_name = None
        self.TrunkSecList_name = None
        self.dend_loc = []  #self.dend_loc = [['dendrite[80]',0.27],['dendrite[80]',0.83],['dendrite[54]',0.16],['dendrite[54]',0.95],['dendrite[52]',0.38],['dendrite[52]',0.83],['dendrite[53]',0.17],['dendrite[53]',0.7],['dendrite[28]',0.35],['dendrite[28]',0.78]]
        self.NMDA_name = 'NMDA_JS'
        self.AMPA_NMDA_ratio = 0.4

        self.AMPA_tau1 = 0.1
        self.AMPA_tau2 = 2
        self.start=150

        self.ns = None
        self.ampa = None
        self.nmda = None
        self.ampa_nc = None
        self.nmda_nc = None

        self.ndend = None
        self.xloc = None

    def translate(self, sectiontype, distance=0):

        if "soma" in sectiontype:
            return self.soma
        else:
            return False

    def load_mod_files(self):
        if os.path.isfile(self.modelpath + self.libpath) is False:
            os.system("cd " + self.modelpath + "; nrnivmodl")

        h.nrn_load_dll(self.modelpath + self.libpath)

    def initialise(self):
        # load cell
        h.load_file("stdrun.hoc")
        h.load_file(self.hocpath)


        if self.template_name is not None and self.SomaSecList_name is not None:

            h('objref testcell')
            h('testcell = new ' + self.template_name)

            exec('soma = h.testcell.'+ self.SomaSecList_name)

            for s in soma :
                self.soma = h.secname()

        elif self.template_name is not None and self.SomaSecList_name is None:
            h('objref testcell')
            h('testcell = new ' + self.template_name)
            # in this case self.soma is set in the jupyter notebook
        elif self.template_name is None and self.SomaSecList_name is not None:
            exec('soma = h.' +  self.SomaSecList_name)
            for s in soma :
                self.soma = h.secname()
        # if both is None, the model is loaded, self.soma will be used

    def set_cclamp(self, amp):
        """Used in DepolarizationBlockTest"""

        exec("self.sect_loc=h." + str(self.soma)+"("+str(0.5)+")")

        self.stim = h.IClamp(self.sect_loc)

        self.stim.amp = amp
        self.stim.delay = 500
        self.stim.dur = 1000

    def run_cclamp(self):
        """Used in DepolarizationBlockTest"""

        #print "- running model", self.name, "stimulus at: ", str(self.soma), "(", str(0.5), ")"

        exec("self.sect_loc=h." + str(self.soma)+"("+str(0.5)+")")

        rec_t = h.Vector()
        rec_t.record(h._ref_t)

        rec_v = h.Vector()
        rec_v.record(self.sect_loc._ref_v)

        h.stdinit()

        dt = 0.025
        h.dt = dt
        h.steps_per_ms = 1 / dt
        h.v_init = -65

        h.celsius = 34
        h.init()
        h.tstop = 1600
        h.run()

        t = numpy.array(rec_t)
        v = numpy.array(rec_v)

        return t, v

    def find_good_obliques(self):
        """Used in ObliqueIntegrationTest"""

        good_obliques = h.SectionList()
        self.dend_loc=[]

        if self.template_name is not None:

            exec('oblique_dendrites=h.testcell.' + self.ObliqueSecList_name)   # so we can have the name of the section list as a string given by the user
            #exec('oblique_dendrites = h.' + oblique_seclist_name)
            exec('trunk=h.testcell.' + self.TrunkSecList_name)
        else:
            exec('oblique_dendrites=h.' + self.ObliqueSecList_name)   # so we can have the name of the section list as a string given by the user
            #exec('oblique_dendrites = h.' + oblique_seclist_name)
            exec('trunk=h.' + self.TrunkSecList_name)

        for sec in oblique_dendrites:
            h(self.soma + ' ' +'distance()') #set soma as the origin
            parent = h.SectionRef(sec).parent
            child_num = h.SectionRef(sec).nchild()
            dist = h.distance(0)
            #print 'SEC: ', sec.name()
            #print 'NCHILD: ', child_num
            #print 'PARENT: ', parent.name()
            #print 'DIST: ', h.distance(0)

            for trunk_sec in trunk:
                if h.issection(parent.name()) and dist < self.max_dist_from_soma and child_num == 0:   # true if string (parent.name()) is contained in the name of the currently accessed section.trunk_sec is the accessed section,
                    #print sec.name(), parent.name()
                    h('access ' + sec.name())         # only currently accessed section can be added to hoc SectionList
                    good_obliques.append(sec.name())


        for sec in good_obliques:

            dend_loc_prox=[]
            dend_loc_dist=[]
            seg_list_prox=[]
            seg_list_dist=[]

            h(sec.name() + ' ' +'distance()')  #set the 0 point of the section as the origin
            #print sec.name()


            for seg in sec:
                #print seg.x, h.distance(seg.x)
                if h.distance(seg.x) > 5 and h.distance(seg.x) < 50:
                    seg_list_prox.append(seg.x)
                if h.distance(seg.x) > 60 and h.distance(seg.x) < 126:
                    seg_list_dist.append(seg.x)

            #print seg_list_prox
            #print seg_list_dist

            if len(seg_list_prox) > 1:
                s = int(round(len(seg_list_prox)/2.0)-1)
                dend_loc_prox.append(sec.name())
                dend_loc_prox.append(seg_list_prox[s])
            else:
                dend_loc_prox.append(sec.name())
                dend_loc_prox.append(seg_list_prox[0])

            if len(seg_list_dist) > 1:
                s = int(round(len(seg_list_dist)/2.0)-1)
                dend_loc_dist.append(sec.name())
                dend_loc_dist.append(seg_list_dist[s])
            elif len(seg_list_dist) == 1:
                dend_loc_dist.append(sec.name())
                dend_loc_dist.append(seg_list_dist[0])
            elif len(seg_list_dist) == 0:                # if the dendrite is not long enough to meet the criteria, we stimulate its end
                dend_loc_dist.append(sec.name())
                dend_loc_dist.append(0.9)


            self.dend_loc.append(dend_loc_prox)
            self.dend_loc.append(dend_loc_dist)

        print 'Dendrites and locations to be tested: ', self.dend_loc

    def set_ampa_nmda(self, dend_loc0=[80,0.27]):
        """Used in ObliqueIntegrationTest"""

        ndend, xloc = dend_loc0

        exec("self.dendrite=h." + ndend)

        self.ampa = h.Exp2Syn(xloc, sec=self.dendrite)
        self.ampa.tau1 = self.AMPA_tau1
        self.ampa.tau2 = self.AMPA_tau2

        exec("self.nmda = h."+self.NMDA_name+"(xloc, sec=self.dendrite)")

        self.ndend = ndend
        self.xloc = xloc


    def set_netstim_netcon(self, interval):
        """Used in ObliqueIntegrationTest"""

        self.ns = h.NetStim()
        self.ns.interval = interval
        self.ns.number = 0
        self.ns.start = self.start

        self.ampa_nc = h.NetCon(self.ns, self.ampa, 0, 0, 0)
        self.nmda_nc = h.NetCon(self.ns, self.nmda, 0, 0, 0)


    def set_num_weight(self, number=1, AMPA_weight=0.0004):
        """Used in ObliqueIntegrationTest"""

        self.ns.number = number
        self.ampa_nc.weight[0] = AMPA_weight
        self.nmda_nc.weight[0] =AMPA_weight/self.AMPA_NMDA_ratio

    def run_syn(self):
        """Used in ObliqueIntegrationTest"""

        exec("self.sect_loc=h." + str(self.soma)+"("+str(0.5)+")")

        # initiate recording
        rec_t = h.Vector()
        rec_t.record(h._ref_t)

        rec_v = h.Vector()
        rec_v.record(self.sect_loc._ref_v)

        rec_v_dend = h.Vector()
        rec_v_dend.record(self.dendrite(self.xloc)._ref_v)

        #print "- running model", self.name
        # initialze and run
        #h.load_file("stdrun.hoc")
        h.stdinit()

        dt = 0.025
        h.dt = dt
        h.steps_per_ms = 1 / dt
        h.v_init = -65

        h.celsius = 34
        h.init()
        h.tstop = 300
        h.run()

        # get recordings
        t = numpy.array(rec_t)
        v = numpy.array(rec_v)
        v_dend = numpy.array(rec_v_dend)

        return t, v, v_dend

    def set_cclamp_somatic_feature(self, amp, delay, dur, section_stim, loc_stim):
        """Used in SomaticFeaturesTest"""

        exec("self.sect_loc=h." + str(section_stim)+"("+str(loc_stim)+")")


        self.stim = h.IClamp(self.sect_loc)
        self.stim.amp = amp
        self.stim.delay = delay
        self.stim.dur = dur

    def run_cclamp_somatic_feature(self, section_rec, loc_rec):

        """Used in SomaticFeaturesTest"""

        #print "- running model", self.name, "stimulus at: ", str(section_rec)+"("+str(loc_rec)+")"

        rec_t = h.Vector()
        rec_t.record(h._ref_t)

        rec_v = h.Vector()
        rec_v.record(self.sect_loc._ref_v)

        h.stdinit()

        dt = 0.025
        h.dt = dt
        h.steps_per_ms = 1 / dt
        h.v_init = -65

        h.celsius = 34
        h.init()
        h.tstop = 1600
        h.run()

        t = numpy.array(rec_t)
        v = numpy.array(rec_v)

        return t, v


class KaliFreund(sciunit.Model,
                 ReceivesCurrent,
                 ProducesMembranePotential):

    def __init__(self, name="Kali"):
        """ Constructor. """

        modelpath = "./hippounit/models/hoc_models/Kali_Freund_modell/scppinput/"
        libpath = "x86_64/.libs/libnrnmech.so.0"

        if os.path.isfile(modelpath + libpath) is False:
            os.system("cd " + modelpath + "; nrnivmodl")

        h.nrn_load_dll(modelpath + libpath)

        self.name = name
        self.threshold = -20
        self.stim = None
        self.soma = "soma"
        sciunit.Model.__init__(self, name=name)

        self.c_step_start = 0.00004
        self.c_step_stop = 0.000004
        self.c_minmax = numpy.array([0.00004, 0.004])
        self.dend_loc = [[80,0.27],[80,0.83],[54,0.16],[54,0.95],[52,0.38],[52,0.83],[53,0.17],[53,0.7],[28,0.35],[28,0.78]]

        self.AMPA_tau1 = 0.1
        self.AMPA_tau2 = 2
        self.start=150

        self.ns = None
        self.ampa = None
        self.nmda = None
        self.ampa_nc = None
        self.nmda_nc = None

        self.ndend = None
        self.xloc = None

    def translate(self, sectiontype, distance=0):

        if "soma" in sectiontype:
            return self.soma
        else:
            return False

    def initialise(self):
        # load cell
        h.load_file("./hippounit/models/hoc_models/Kali_Freund_modell/scppinput/ca1_syn.hoc")

    def set_cclamp(self, amp):

        self.stim = h.IClamp(h.soma(0.5))
        self.stim.amp = amp
        self.stim.delay = 500
        self.stim.dur = 1000

    def run_cclamp(self):

        print "- running model", self.name

        rec_t = h.Vector()
        rec_t.record(h._ref_t)

        rec_v = h.Vector()
        rec_v.record(h.soma(0.5)._ref_v)

        h.stdinit()

        dt = 0.025
        h.dt = dt
        h.steps_per_ms = 1 / dt
        h.v_init = -65

        h.celsius = 34
        h.init()
        h.tstop = 1600
        h.run()

        t = numpy.array(rec_t)
        v = numpy.array(rec_v)

        return t, v

    def set_ampa_nmda(self, dend_loc0=[80,0.27]):

        ndend, xloc = dend_loc0
        self.ampa = h.Exp2Syn(xloc, sec=h.dendrite[ndend])
        self.ampa.tau1 = self.AMPA_tau1
        self.ampa.tau2 = self.AMPA_tau2

        self.nmda = h.NMDA_JS(xloc, sec=h.dendrite[ndend])

        self.ndend = ndend
        self.xloc = xloc


    def set_netstim_netcon(self, interval):

        self.ns = h.NetStim()
        self.ns.interval = interval
        self.ns.number = 0
        self.ns.start = self.start

        self.ampa_nc = h.NetCon(self.ns, self.ampa, 0, 0, 0)
        self.nmda_nc = h.NetCon(self.ns, self.nmda, 0, 0, 0)


    def set_num_weight(self, number=1, AMPA_weight=0.0004):

        self.ns.number = number
        self.ampa_nc.weight[0] = AMPA_weight
        self.nmda_nc.weight[0] =AMPA_weight/0.2

    def run_syn(self):

        # initiate recording
        rec_t = h.Vector()
        rec_t.record(h._ref_t)

        rec_v = h.Vector()
        rec_v.record(h.soma(0.5)._ref_v)

        rec_v_dend = h.Vector()
        rec_v_dend.record(h.dendrite[self.ndend](self.xloc)._ref_v)

        print "- running model", self.name
        # initialze and run
        #h.load_file("stdrun.hoc")
        h.stdinit()

        dt = 0.025
        h.dt = dt
        h.steps_per_ms = 1 / dt
        h.v_init = -65

        h.celsius = 34
        h.init()
        h.tstop = 300
        h.run()

        # get recordings
        t = numpy.array(rec_t)
        v = numpy.array(rec_v)
        v_dend = numpy.array(rec_v_dend)

        return t, v, v_dend

    def set_cclamp_somatic_feature(self, amp, delay, dur, section_stim, loc_stim):

        exec("self.sect_loc=h." + str(section_stim)+"("+str(loc_stim)+")")


        self.stim = h.IClamp(self.sect_loc)
        self.stim.amp = amp
        self.stim.delay = delay
        self.stim.dur = dur

    def run_cclamp_somatic_feature(self, section_rec, loc_rec):

        exec("self.sect_loc=h." + str(section_rec)+"("+str(loc_rec)+")")

        print "- running model", self.name

        rec_t = h.Vector()
        rec_t.record(h._ref_t)

        rec_v = h.Vector()
        rec_v.record(self.sect_loc._ref_v)

        h.stdinit()

        dt = 0.025
        h.dt = dt
        h.steps_per_ms = 1 / dt
        h.v_init = -65

        h.celsius = 34
        h.init()
        h.tstop = 1600
        h.run()

        t = numpy.array(rec_t)
        v = numpy.array(rec_v)

        return t, v

class Migliore(sciunit.Model,
                 ReceivesCurrent,
                 ProducesMembranePotential):

    def __init__(self, name="Migliore"):
        """ Constructor. """

        modelpath = "./hippounit/models/hoc_models/Migliore_Schizophr/"
        libpath = "x86_64/.libs/libnrnmech.so.0"

        if os.path.isfile(modelpath + libpath) is False:
            os.system("cd " + modelpath + "; nrnivmodl")

        h.nrn_load_dll(modelpath + libpath)

        self.name = "Migliore"
        self.threshold = -20
        self.stim = None
        self.soma = "soma[0]"
        sciunit.Model.__init__(self, name=name)

        self.c_step_start = 0.00004
        self.c_step_stop = 0.000004
        self.c_minmax = numpy.array([0.00004, 0.004])
        self.dend_loc = [[17,0.3],[17,0.9],[24,0.3],[24,0.7],[22,0.3],[22,0.7],[25,0.2],[25,0.5],[30,0.1],[30,0.5]]
        self.trunk_dend_loc_distr=[[10,0.167], [10,0.5], [10,0.83], [11,0.5], [9,0.5], [8,0.5], [7,0.5]]
        self.trunk_dend_loc_clust=[10,0.167]

        self.AMPA_tau1 = 0.1
        self.AMPA_tau2 = 2
        self.start=150

        self.ns = None
        self.ampa = None
        self.nmda = None
        self.ampa_nc = None
        self.nmda_nc = None
        self.ndend = None
        self.xloc = None

    def translate(self, sectiontype, distance=0):

        if "soma" in sectiontype:
            return self.soma
        else:
            return False

    def initialise(self):
        # load cell
        h.load_file("./hippounit/models/hoc_models/Migliore_Schizophr/basic_sim_9068802-test.hoc")


    def set_cclamp(self, amp):

        self.stim = h.IClamp(h.soma[0](0.5))
        self.stim.amp = amp
        self.stim.delay = 500
        self.stim.dur = 1000

    def run_cclamp(self):

        print "- running model", self.name

        rec_t = h.Vector()
        rec_t.record(h._ref_t)

        rec_v = h.Vector()
        rec_v.record(h.soma[0](0.5)._ref_v)

        h.stdinit()

        dt = 0.025
        h.dt = dt
        h.steps_per_ms = 1 / dt
        h.v_init = -65

        h.celsius = 34
        h.init()
        h.tstop = 1600
        h.run()

        t = numpy.array(rec_t)
        v = numpy.array(rec_v)

        return t, v

    def set_ampa_nmda(self, dend_loc0=[17,0.3]):

        ndend, xloc = dend_loc0
        self.ampa = h.Exp2Syn(xloc, sec=h.apical_dendrite[ndend])
        self.ampa.tau1 = self.AMPA_tau1
        self.ampa.tau2 = self.AMPA_tau2

        self.nmda = h.NMDA_JS(xloc, sec=h.apical_dendrite[ndend])

        self.ndend = ndend
        self.xloc = xloc


    def set_netstim_netcon(self, interval):

        self.ns = h.NetStim()
        self.ns.interval = interval
        self.ns.number = 0
        self.ns.start = self.start

        self.ampa_nc = h.NetCon(self.ns, self.ampa, 0, 0, 0)
        self.nmda_nc = h.NetCon(self.ns, self.nmda, 0, 0, 0)


    def set_num_weight(self, number=1, AMPA_weight=0.0004):

        self.ns.number = number
        self.ampa_nc.weight[0] = AMPA_weight
        self.nmda_nc.weight[0] = AMPA_weight/0.2

    def run_syn(self):

        # initiate recording
        rec_t = h.Vector()
        rec_t.record(h._ref_t)

        rec_v = h.Vector()
        rec_v.record(h.soma[0](0.5)._ref_v)

        rec_v_dend = h.Vector()
        rec_v_dend.record(h.apical_dendrite[self.ndend](self.xloc)._ref_v)

        print "- running model", self.name
        # initialze and run
        #h.load_file("stdrun.hoc")
        h.stdinit()

        dt = 0.025
        h.dt = dt
        h.steps_per_ms = 1 / dt
        h.v_init = -65

        h.celsius = 34
        h.init()
        h.tstop = 300
        h.run()

        # get recordings
        t = numpy.array(rec_t)
        v = numpy.array(rec_v)
        v_dend = numpy.array(rec_v_dend)

        return t, v, v_dend

    def set_cclamp_somatic_feature(self, amp, delay, dur, section_stim, loc_stim):

        exec("self.sect_loc=h." + str(section_stim)+"("+str(loc_stim)+")")


        self.stim = h.IClamp(self.sect_loc)
        self.stim.amp = amp
        self.stim.delay = delay
        self.stim.dur = dur

    def run_cclamp_somatic_feature(self, section_rec, loc_rec):

        exec("self.sect_loc=h." + str(section_rec)+"("+str(loc_rec)+")")

        print "- running model", self.name

        rec_t = h.Vector()
        rec_t.record(h._ref_t)

        rec_v = h.Vector()
        rec_v.record(self.sect_loc._ref_v)

        h.stdinit()

        dt = 0.025
        h.dt = dt
        h.steps_per_ms = 1 / dt
        h.v_init = -65

        h.celsius = 34
        h.init()
        h.tstop = 1600
        h.run()

        t = numpy.array(rec_t)
        v = numpy.array(rec_v)

        return t, v

class Bianchi(sciunit.Model,
                 ReceivesCurrent,
                 ProducesMembranePotential):

    def __init__(self, name="Bianchi"):
        """ Constructor. """

        modelpath = "./hippounit/models/hoc_models/Ca1_Bianchi/experiment/"
        libpath = "x86_64/.libs/libnrnmech.so.0"

        if os.path.isfile(modelpath + libpath) is False:
            os.system("cd " + modelpath + "; nrnivmodl")

        h.nrn_load_dll(modelpath + libpath)

        self.name = "Bianchi"
        self.threshold = -20
        self.stim = None
        self.soma = "soma[0]"

        sciunit.Model.__init__(self, name=name)

        self.c_step_start = 0.00004
        self.c_step_stop = 0.000004
        self.c_minmax = numpy.array([0.00004, 0.004])
        self.dend_loc = [[112,0.375],[112,0.875],[118,0.167],[118,0.99],[30,0.167],[30,0.83],[107,0.25],[107,0.75],[114,0.01],[114,0.75]]
        self.trunk_dend_loc_distr=[[65,0.5], [69,0.5], [71,0.5], [64,0.5], [62,0.5], [60,0.5], [81,0.5]]
        self.trunk_dend_loc_clust=[65,0.5]

        self.AMPA_tau1 = 0.1
        self.AMPA_tau2 = 2
        self.start=150

        self.ns = None
        self.ampa = None
        self.nmda = None
        self.ampa_nc = None
        self.nmda_nc = None
        self.ndend = None
        self.xloc = None


    def translate(self, sectiontype, distance=0):

        if "soma" in sectiontype:
            return self.soma
        else:
            return False


    def initialise(self):
        # load cell
        h.load_file("./hippounit/models/hoc_models/Ca1_Bianchi/experiment/basic.hoc")


    def set_cclamp(self, amp):

        self.stim = h.IClamp(h.soma[0](0.5))
        self.stim.amp = amp
        self.stim.delay = 500
        self.stim.dur = 1000

    def run_cclamp(self):

        print "- running model", self.name

        rec_t = h.Vector()
        rec_t.record(h._ref_t)

        rec_v = h.Vector()
        rec_v.record(h.soma[0](0.5)._ref_v)

        h.stdinit()

        dt = 0.025
        h.dt = dt
        h.steps_per_ms = 1 / dt
        h.v_init = -65

        h.celsius = 34
        h.init()
        h.tstop = 1600
        h.run()

        t = numpy.array(rec_t)
        v = numpy.array(rec_v)

        return t, v

    def set_ampa_nmda(self, dend_loc0=[112,0.375]):

        ndend, xloc = dend_loc0
        self.ampa = h.Exp2Syn(xloc, sec=h.apical_dendrite[ndend])
        self.ampa.tau1 = self.AMPA_tau1
        self.ampa.tau2 = self.AMPA_tau2

        self.nmda = h.NMDA_JS(xloc, sec=h.apical_dendrite[ndend])

        self.ndend = ndend
        self.xloc = xloc


    def set_netstim_netcon(self, interval):

        self.ns = h.NetStim()
        self.ns.interval = interval
        self.ns.number = 0
        self.ns.start = self.start

        self.ampa_nc = h.NetCon(self.ns, self.ampa, 0, 0, 0)
        self.nmda_nc = h.NetCon(self.ns, self.nmda, 0, 0, 0)


    def set_num_weight(self, number=1, AMPA_weight=0.0004):

        self.ns.number = number
        self.ampa_nc.weight[0] = AMPA_weight
        self.nmda_nc.weight[0] = AMPA_weight/0.2

    def run_syn(self):

        # initiate recording
        rec_t = h.Vector()
        rec_t.record(h._ref_t)

        rec_v = h.Vector()
        rec_v.record(h.soma[0](0.5)._ref_v)

        rec_v_dend = h.Vector()
        rec_v_dend.record(h.apical_dendrite[self.ndend](self.xloc)._ref_v)

        print "- running model", self.name
        # initialze and run
        #h.load_file("stdrun.hoc")
        h.stdinit()

        dt = 0.025
        h.dt = dt
        h.steps_per_ms = 1 / dt
        h.v_init = -65

        h.celsius = 34
        h.init()
        h.tstop = 300
        h.run()

        # get recordings
        t = numpy.array(rec_t)
        v = numpy.array(rec_v)
        v_dend = numpy.array(rec_v_dend)

        return t, v, v_dend

    def set_cclamp_somatic_feature(self, amp, delay, dur, section_stim, loc_stim):

        exec("self.sect_loc=h." + str(section_stim)+"("+str(loc_stim)+")")


        self.stim = h.IClamp(self.sect_loc)
        self.stim.amp = amp
        self.stim.delay = delay
        self.stim.dur = dur

    def run_cclamp_somatic_feature(self, section_rec, loc_rec):

        exec("self.sect_loc=h." + str(section_rec)+"("+str(loc_rec)+")")

        print "- running model", self.name

        rec_t = h.Vector()
        rec_t.record(h._ref_t)

        rec_v = h.Vector()
        rec_v.record(self.sect_loc._ref_v)

        h.stdinit()

        dt = 0.025
        h.dt = dt
        h.steps_per_ms = 1 / dt
        h.v_init = -65

        h.celsius = 34
        h.init()
        h.tstop = 1600
        h.run()

        t = numpy.array(rec_t)
        v = numpy.array(rec_v)

        return t, v

class Golding(sciunit.Model,
                 ReceivesCurrent,
                 ProducesMembranePotential):

    def __init__(self, name="Golding"):
        """ Constructor. """

        modelpath = "./hippounit/models/hoc_models/Golding_dichotomy/fig08/"
        libpath = "x86_64/.libs/libnrnmech.so.0"

        if os.path.isfile(modelpath + libpath) is False:
            os.system("cd " + modelpath + "; nrnivmodl")

        h.nrn_load_dll(modelpath + libpath)

        #self.dendA5_01111111100 = h.Section(name='foo', cell=self)

        self.dendrite=None
        self.name = "Golding"
        self.threshold = -40
        self.stim = None
        self.soma = "somaA"

        sciunit.Model.__init__(self, name=name)

        self.c_step_start = 0.00004
        self.c_step_stop = 0.000004
        self.c_minmax = numpy.array([0.00004, 0.004])
        self.dend_loc = [["dendA5_00",0.275],["dendA5_00",0.925],["dendA5_01100",0.15],["dendA5_01100",0.76],["dendA5_0111100",0.115],["dendA5_0111100",0.96],["dendA5_01111100",0.38],["dendA5_01111100",0.98],["dendA5_0111101",0.06],["dendA5_0111101",0.937]]
        self.trunk_dend_loc_distr=[["dendA5_01111111111111",0.68], ["dendA5_01111111111111",0.136], ["dendA5_01111111111111",0.864], ["dendA5_011111111111111",0.5], ["dendA5_0111111111111111",0.5], ["dendA5_0111111111111",0.786], ["dendA5_0111111111111",0.5]]
        self.trunk_dend_loc_clust=["dendA5_01111111111111",0.68]

        self.AMPA_tau1 = 0.1
        self.AMPA_tau2 = 2
        self.start=150

        self.ns = None
        self.ampa = None
        self.nmda = None
        self.ampa_nc = None
        self.nmda_nc = None
        self.ndend = None
        self.xloc = None

    def translate(self, sectiontype, distance=0):

        if "soma" in sectiontype:
            return self.soma
        else:
            return False

    def initialise(self):
        # load cell
        h.load_file("./hippounit/models/hoc_models/Golding_dichotomy/fig08/run_basic.hoc")

    def set_cclamp(self, amp):

        self.stim = h.IClamp(h.somaA(0.5))
        self.stim.amp = amp
        self.stim.delay = 500
        self.stim.dur = 1000

    def run_cclamp(self):

        print "- running model", self.name

        rec_t = h.Vector()
        rec_t.record(h._ref_t)

        rec_v = h.Vector()
        rec_v.record(h.somaA(0.5)._ref_v)

        h.stdinit()

        dt = 0.025
        h.dt = dt
        h.steps_per_ms = 1 / dt
        h.v_init = -65

        h.celsius = 34
        h.init()
        h.tstop = 1600
        h.run()

        t = numpy.array(rec_t)
        v = numpy.array(rec_v)

        return t, v

    def set_ampa_nmda(self, dend_loc0=["dendA5_01111111100",0.375]):
        #self.dendrite=h.dendA5_01111111100

        ndend, xloc = dend_loc0

        exec("self.dendrite=h." + ndend)

        self.ampa = h.Exp2Syn(xloc, sec=self.dendrite)
        self.ampa.tau1 = self.AMPA_tau1
        self.ampa.tau2 = self.AMPA_tau2

        self.nmda = h.NMDA_JS(xloc, sec=self.dendrite)

        self.ndend = ndend
        self.xloc = xloc


    def set_netstim_netcon(self, interval):

        self.ns = h.NetStim()
        self.ns.interval = interval
        self.ns.number = 0
        self.ns.start = self.start

        self.ampa_nc = h.NetCon(self.ns, self.ampa, 0, 0, 0)
        self.nmda_nc = h.NetCon(self.ns, self.nmda, 0, 0, 0)


    def set_num_weight(self, number=1, AMPA_weight=0.0004):

        self.ns.number = number
        self.ampa_nc.weight[0] = AMPA_weight
        self.nmda_nc.weight[0] = AMPA_weight/0.2

    def run_syn(self):

        # initiate recording
        rec_t = h.Vector()
        rec_t.record(h._ref_t)

        rec_v = h.Vector()
        rec_v.record(h.somaA(0.5)._ref_v)

        rec_v_dend = h.Vector()
        rec_v_dend.record(self.dendrite(self.xloc)._ref_v)

        print "- running model", self.name
        # initialze and run
        #h.load_file("stdrun.hoc")
        h.stdinit()

        dt = 0.025
        h.dt = dt
        h.steps_per_ms = 1 / dt
        h.v_init = -65

        h.celsius = 34
        h.init()
        h.tstop = 300
        h.run()

        # get recordings
        t = numpy.array(rec_t)
        v = numpy.array(rec_v)
        v_dend = numpy.array(rec_v_dend)

        return t, v, v_dend

    def set_cclamp_somatic_feature(self, amp, delay, dur, section_stim, loc_stim):

        exec("self.sect_loc=h." + str(section_stim)+"("+str(loc_stim)+")")


        self.stim = h.IClamp(self.sect_loc)
        self.stim.amp = amp
        self.stim.delay = delay
        self.stim.dur = dur

    def run_cclamp_somatic_feature(self, section_rec, loc_rec):

        exec("self.sect_loc=h." + str(section_rec)+"("+str(loc_rec)+")")

        print "- running model", self.name

        rec_t = h.Vector()
        rec_t.record(h._ref_t)

        rec_v = h.Vector()
        rec_v.record(self.sect_loc._ref_v)

        h.stdinit()

        dt = 0.025
        h.dt = dt
        h.steps_per_ms = 1 / dt
        h.v_init = -65

        h.celsius = 34
        h.init()
        h.tstop = 1600
        h.run()

        t = numpy.array(rec_t)
        v = numpy.array(rec_v)

        return t, v
