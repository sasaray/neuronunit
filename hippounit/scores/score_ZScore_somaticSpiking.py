from sciunit import Score
import numpy
from sciunit.utils import assert_dimensionless

class ZScore_somaticSpiking(Score):
    """
    Sum of Z scores. A float indicating the sum of standardized difference
    from reference means for somatic spiking features.
    """

    def __init__(self, score, related_data={}):

	    if not isinstance(score, Exception) and not isinstance(score, float):
	        raise InvalidScoreError("Score must be a float.")
	    else:
	        super(ZScore_somaticSpiking,self).__init__(score, related_data=related_data)

    @classmethod
    def compute(cls, observation, prediction):
        """Computes sum of z-scores from observation and prediction for somatic spiking features"""

        feature_error_means=numpy.array([])
        feature_error_stds=numpy.array([])
        features_names=(observation.keys())
        feature_results_dict={}

        for i in range (0, len(features_names)):
            p_value = prediction[features_names[i]]['feature mean']
            o_mean = float(observation[features_names[i]]['Mean'])
            o_std = float(observation[features_names[i]]['Std'])

            p_std = prediction[features_names[i]]['feature sd']


            try:
                feature_error = abs(p_value - o_mean)/o_std
                feature_error = assert_dimensionless(feature_error)
                feature_error_mean=numpy.mean(feature_error)
                feature_error_sd=numpy.std(feature_error)

            except (TypeError,AssertionError) as e:
                feature_error = e
            feature_error_means=numpy.append(feature_error_means,feature_error_mean)
            feature_result={features_names[i]:{'mean feature error':feature_error_mean,
                                            'feature error sd':feature_error_sd}}

            feature_results_dict.update(feature_result)


        score_sum=numpy.sum(feature_error_means)

        return score_sum, feature_results_dict, features_names

    def __str__(self):

		return 'Z_sum = %.2f' % self.score


class ZScore_trunk(Score):
    """
    A Z score. A float indicating standardized difference
    from a reference mean.
    """


    def __init__(self, score, related_data={}):

		self.score_k=[]
		self.score_v=[]

		for k,v in score.iteritems():
			self.score_k.append(k)
			self.score_v.append(v)
		print self.score_k
		for i in range(len(self.score_v)):
			if not isinstance(self.score_v[i], Exception) and not isinstance(self.score_v[i], float):
				raise InvalidScoreError("Score must be a float.")
	        else:
				super(ZScore_trunk,self).__init__(score, related_data=related_data)

    @classmethod
    def compute(self, observation, prediction):
        """Computes sum of z-scores from observation and prediction."""

        try:
    		if not math.isnan(prediction['model max spike dV/dt (synch., distributed)']):   # if no dendritic spike is generated, this is NaN
    			max_dV_dt_error_distr=abs(observation['mean_max_spike_deriv_distr'] - prediction['model max spike dV/dt (synch., distributed)'])/observation['max_spike_deriv_distr_std']
    			max_dV_dt_error_distr = assert_dimensionless(max_dV_dt_error_distr)
    		else:
    			max_dV_dt_error_distr=float('NaN')
    			print "no dendritic spike was generated for synchronous, distributed inputs"
        except (TypeError,AssertionError) as e:
    		max_dV_dt_error_distr = e

        try:
    	    if not math.isnan(prediction['model max spike dV/dt (synch., clustered)']):
    	        max_dV_dt_error_clust=abs(observation['mean_max_spike_deriv_clust'] - prediction['model max spike dV/dt (synch., clustered)'])/observation['max_spike_deriv_clust_std']
    	        max_dV_dt_error_clust = assert_dimensionless(max_dV_dt_error_clust)
    	    else:
    	        print "no dendritic spike was generated for synchronous, clustered inputs"
    	        max_dV_dt_error_clust=float('NaN')
        except (TypeError,AssertionError) as e:
                max_dV_dt_error_clust  = e

        try:
    	    if not math.isnan(prediction['model AP amplitude(synch., distributed)']):
    			ap_amp_error_distr=abs(observation['mean_AP_amp_distr'] - prediction['model AP amplitude(synch., distributed)'])/observation['AP_amp_distr_std']
    			ap_amp_error_distr = assert_dimensionless(ap_amp_error_distr)
    	    else:
    	        ap_amp_error_distr=float('NaN')
        except (TypeError,AssertionError) as e:
    		ap_amp_error_distr = e

        try:
    		if not math.isnan(prediction['model AP amplitude(synch., clustered)']):
    			ap_amp_error_clust=abs(observation['mean_AP_amp_clust'] - prediction['model AP amplitude(synch., clustered)'])/observation['AP_amp_clust_std']
    			ap_amp_error_clust=assert_dimensionless(ap_amp_error_clust)
    		else:
    			ap_amp_error_clust=float('NaN')
        except (TypeError,AssertionError) as e:
    		ap_amp_error_clust = e

        try:
    		async_clust_slope_error=abs(observation['mean_slope_clust'] - prediction['model slope (asynch., clustered)'])/observation['slope_clust_std']
    		async_clust_slope_error=assert_dimensionless(async_clust_slope_error)
        except (TypeError,AssertionError) as e:
    		async_clust_slope_error = e

        try:
    		async_distr_slope_error=abs(observation['mean_slope_distr'] - prediction['model slope (asynch., distributed)'])/observation['slope_distr_std']
    		async_distr_slope_error=assert_dimensionless(async_distr_slope_error)
        except (TypeError,AssertionError) as e:
    		async_distr_slope_error = e

        errors_dict= {'AP amplitude error (synch., clustered)': ap_amp_error_clust , 'AP amplitude error (synch., distributed)': ap_amp_error_distr,
    	 			'max spike dV/dt error (synch., clustered)': max_dV_dt_error_clust, 'max spike dV/dt error (synch., distributed)': max_dV_dt_error_distr,
    				'slope error (asynch., clustered)': async_clust_slope_error,'slope error (asynch., distributed)': async_distr_slope_error}
        return errors_dict


    def __str__(self):
		string=""
		for i in range(len(self.score_k)):
			string = string + '\n'+ self.score_k[i]+' = ' + str(self.score_v[i]) + ', '
		return string#'\nmax spike dV/dt error (synch., clustered)= %.2f, \nslope error (asynch., distributed)= %.2f, \nAP amplitude error (synch., clustered) = %.2f, \nmax spike dV/dt error(synch., distributed) = %.2f ,\nslope error (asynch., clustered) = %.2f, \nAP amplitude error (synch., distributed) = %.2f' % (score_v[0], score_v[1], score_v[2], score_v[3], score_v[4], score_v[4])
