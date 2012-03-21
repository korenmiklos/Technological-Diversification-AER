'''
Parameter settings for the simulation.
'''

# If TEST is True, then fewer repetitions are run. To replicate results
TEST = False
# Enter your PiCloud.com credentials here.
KEY_ID = YOUR_KEY_ID_HERE
SECRET_KEY = 'YOUR_OWN_SECRET_KEY HERE'

# Calibrate initial N to USA GDP per capita and variance.
USA_VAR = 0.001534
USA_GDP = 2444.644

# These statistics are going to be saved.
STATNAMES = ['cross section beta','time series beta','early dispersion','late dispersion','average skewness']

# Default parameter values, if not overwritten by ALTERNATIVES below.
DEFAULT = {'gamma':0.10, 'theta_N':0.03, 'theta_m0':0.03, 'epsilon':3, 
             'eta':0.1, 'businesses_per_capita':0.0161}
# List of alternatives to try.
ALTERNATIVES = {'gamma': [0.05, 0.1, 0.15, 0.2], 'eta': [0.05, 0.1, 0.15, 0.2],'epsilon': [2.1, 3, 5], 'dummy': [True]} 

# Which parameter to loop over.
PARAMETER = 'gamma'
# How many repetitions?
HOW_MANY = 1000

