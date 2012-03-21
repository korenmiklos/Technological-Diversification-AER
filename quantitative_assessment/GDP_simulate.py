'''
Replication code for results in Section III. "Volatility and Development: A Quantitative Assessment" of

    Koren, Miklós and Silvana Tenreyro. 2012. "Technological Diversification." American Economic Review.
    
Please cite the above paper when using this program.

Define methods for simulation and submit simulation jobs to PiCloud.com for parallel processing. The code can be simply modified to use the "multiprocessing" library of Python instead of PiCloud.
'''
import numpy as np
from numpy import log
import matplotlib.pyplot as plt
from scipy.stats import poisson, logser, norm
from scipy.optimize import bisect
import random

'''
Change this to import multiprocessing and use 
pool.map, pool.iresult to submit and retrieve jobs
'''
import cloud

import csv
import pickle
import copy
from settings import *

''' Helper functions to calculate cross-sectional and time-series
decadal regressions. '''
cross_section_demean = lambda mat: mat - mat.mean(axis=1).repeat(mat.shape[1],axis=1)
time_series_demean = lambda mat: mat - mat.mean(axis=0).repeat(mat.shape[0],axis=0)
cross_section_stacker = lambda mat: cross_section_demean(mat).flatten().T.copy()
time_series_stacker = lambda mat: time_series_demean(mat).flatten().T.copy()

def regress(Y,X):
    '''
    Simple OLS regression.
    '''
    beta = (X.T*X).I*X.T*Y
    return beta

def logarithmic_theta_from_mean(mean):
    '''Return a theta that leads to a given logarithmic mean.'''
    # set lower and upper bounds to limit the search process
    lower = 0.01
    upper = 0.99999
    if mean<logser.mean(lower):
        return lower
    elif mean>logser.mean(upper):
        return upper
    else: 
        return bisect(lambda nu: logser.mean(nu)-mean,lower,upper)

def logarithmic_concentration(nu):
    '''Return the techdiv index on an FSD corresponding to logser(nu)'''
    return 2*(1-1/nu)*np.log(1-nu)-(1-1/nu**2)*np.log(1-nu**2)

def logarithmic_theta_from_concentration(concentration):
    '''Return a theta that leads to a given logarithmic concentration.'''
    return bisect(lambda nu: logarithmic_concentration(nu)-concentration,0.01,0.9999)


def read_data(filename):
    '''
    Read a numpy array from a .csv file.
    '''
    data = np.genfromtxt(filename,delimiter=',')
    return np.nan_to_num(data[1,1:])

def get_list_of_countries():
    return np.nonzero(read_data('../data/maddison/gdp1870.csv'))[0]

def read_population():
    data = read_data('../data/maddison/population1870.csv')
    return data[get_list_of_countries()].tolist()

def read_gdp():
    data = read_data('../data/maddison/gdp1870.csv')
    return data[get_list_of_countries()].tolist()


def simulate_an_economy(economy,T):
    '''
    Simulate an economy for T years.
    '''
    return np.mat(economy.get_GDP_series(T)).T.copy()


def get_beta(GDP,T1,T2,cross_section = True):
    ''' Return a list of cross-section or time-series betas.'''
    growth = np.diff(log(GDP),axis=0)
    meangrowth = decade_mean*growth[T1:T2,:]
    meanlogGDP = decade_mean*log(GDP[T1:T2,:]) 
    decadalstdev = np.sqrt(decade_mean*np.power(growth[T1:T2,:]-meangrowth,2))
    if cross_section:
        beta = regress(cross_section_stacker(log(decadalstdev)),cross_section_stacker(meanlogGDP))
    else:
        beta = regress(time_series_stacker(log(decadalstdev)),time_series_stacker(meanlogGDP))
    return beta

def get_skew(GDP,T1,T2):
    ''' Return a skewness.'''
    growth = np.diff(log(GDP),axis=0)
    meangrowth = decade_mean*growth[T1:T2,:]
    decadalstdev = np.sqrt(decade_mean*np.power(growth[T1:T2,:]-meangrowth,2))
    decadalskew = decade_mean*np.power((growth[T1:T2,:]-meangrowth)/decadalstdev,3)
    return decadalskew.mean()

def get_dispersion(GDP,T1,T2,early = True):
    ''' Return a list of cross sectional dispersions of log GDP per capita.'''
    meanlogGDP = decade_mean*log(GDP[T1:T2,:]) 
    if early:
        t = T1
    else:
        t = T2-1
    return np.std(meanlogGDP[t-T1,:],axis=1)



def get_stats(scenario):
    '''
    A simple wrapper function that calls the .create_alternative_worlds of a scenario.
    '''
    scenario.init()
    job = scenario.create_alternative_worlds()
    return job


def simulate_all_worlds(scenario,K):
    '''
    Simulate a given parameter scenario K times.
    '''
    print 'Simulating %d worlds.' % K
    # create K copies of the scenario
    scenarios = []
    for k in xrange(K):
        scenarios.append(copy.copy(scenario))
    jobs = cloud.map(get_stats,scenarios,_label='%d worlds' % K,_type='c2')
    return jobs

def GDP_collector(jobs,T,T1,T2):
    '''
    Retrieve the results of jobs, and calculate statistics based on the time period 
    between T1 and T2.
    '''
    I = len(jobs)
    world_GDP = np.mat(np.zeros((T,I)))
    i = 0
    for gdp in cloud.iresult(jobs,num_in_parallel=0):
        world_GDP[:,i] = gdp.copy()
        i += 1

    # fill in statistics
    stats = dict()
    stats['cross section beta'] = get_beta(world_GDP,T1,T2).T.copy()
    stats['time series beta'] = get_beta(world_GDP,T1,T2,cross_section=False).T.copy()
    stats['early dispersion'] = get_dispersion(world_GDP,T1,T2,early=True).T.copy()
    stats['late dispersion'] = get_dispersion(world_GDP,T1,T2,early=False).T.copy()
    stats['average skewness'] = get_skew(world_GDP,T1,T2)
    return stats


class Scenario(object):
    '''Represents a set of parameters to initialize the economies and run the simulations. 
    This is where data are saved.'''


    def __init__(self,GDP_list,population_list,dt=1,how_long=142,**kwargs):
        self.parameters = parameters
        for (key,value) in kwargs.iteritems():
            # save all parameters 
            setattr(self,key,value)
        self.parameters['lambdadt'] = kwargs['Lambda']*dt
        self.parameters['gammadt'] = kwargs['gamma']*dt
        self.parameters['etadt'] = kwargs['eta']*dt

        self.GDP_list = GDP_list
        self.population_list = population_list

        self.I = len(GDP_list)
        self.T = how_long
        self.dt = dt

    def init(self):
        '''
        Create an economy from the given parameters.
        '''
        kwargs = self.parameters

        self.economies = []
        for GDP, population in zip(self.GDP_list,self.population_list):
            kwargs['initial_gdp'] = GDP
            kwargs['population'] = population
            # set initial parameters for this economy
            self.economies.append(Economy(parameters=kwargs))


    def create_alternative_worlds(self):
        ''' 
        Simulate each of the economies. 
        '''
        T = self.T
        I = self.I

        print 'Simulating a world with %d countries.' % I

        # these are the individual simulation jobs
        jobs = cloud.map(simulate_an_economy,self.economies,[T]*I,_label='A world with %d countries.' % I,_type='c2')
        # this is a harvester job, collecting the results of each individual simulation
        return cloud.call(GDP_collector, jobs, T, T1, T2,_depends_on=jobs,_label='Collecting GDP results.')


class Economy(object):
    '''
    Represents an economy with parameters saved as properties and
    methods to simulate the evolution of GDP.
    '''
    def __init__(self,parameters,initial_distribution=None):
        for (key,value) in parameters.iteritems():
            setattr(self,key,value)
        if initial_distribution is None:
            # initialize distribution from given parameters
            nbar = self.get_n()
            M = self.get_M()
            self.distribution = np.mat(logser.pmf(1+np.arange(self.Ncap),logarithmic_theta_from_mean(nbar))).T*M
        else:
            self.distribution = initial_distribution
        if self.theta_m0 > 0:
            self.zeta = ((2-self.epsilon)/(self.epsilon-1)+self.theta_N)/self.theta_m0
        else:
            self.zeta = None

    def get_n(self):
        '''
        Average number of varieties per firm.
        '''
        return self.initial_gdp/self.epsilonpibar/self.get_M()

    def get_M(self):
        '''
        Initial mass of firms.
        '''
        return 1

    def GDP(self,distribution):
        '''Calculate GDP as the sum over Mk'''  
        return np.flipud(distribution).cumsum().sum()*self.epsilonpibar

    def support(self):
        '''Support of the distribution.'''
        return self.distribution.shape[0]

    def successful_entrants(self,distribution):
        '''
        Find the measure of entrants that jump from n=0 to n=1.
        '''
        if self.theta_m0 > 0:
            logm0 = -np.log(self.epsilonpibar)/self.theta_m0 + self.zeta*np.log(self.GDP(distribution)/self.epsilonpibar)
            return (1-np.exp(-self.etadt))*max(0,np.exp(logm0))
        else:
            return 0


    def transition_matrix(self):
        '''
        Return transition matrix that reflects a proportion lambda*n*dt firms stepping up.
        '''
        N = self.support()
        TM = np.mat(np.zeros((N,N)))
        
        for n in range(N):
            tempvec = poisson.pmf(np.mat(np.arange(0.,N-n)).T,(np.exp(self.lambdadt)-1)*(n+1));
            tempvec = tempvec/tempvec.sum();
            TM[n:N,n]= tempvec;
        
        return TM

    def draw_shocks(self):
        '''
        Draw a list of shocked varieties at random. 
        '''
        # first determine how many shocks to generate
        N = self.support()
        numshocks = np.random.binomial(N,1-np.exp(-self.gammadt))
        shocks = []
        maxshock = N
        for n in xrange(numshocks):
            # then draw each at random
            shocks.append(random.choice(xrange(maxshock)))
            maxshock -= 1
        return shocks

    def get_GDP_series(self,how_long):
        '''
        Return a GDP series, starting from initial distribution, running until 
        how_long periods. 
        '''
        # initialize the loop
        Ncap = self.support()
        TM = self.transition_matrix()
        # each call should get a new copy from the distribution
        distribution = self.distribution.copy()

        GDPs = []

        for time in xrange(how_long):
            GDPs.append(self.GDP(distribution))
            # some firms move up
            distribution = TM*distribution
            # add new entrants
            distribution[0] += self.successful_entrants(distribution)
            # some firms move down
            for shock in self.draw_shocks():
                if shock>0:
                    lower = distribution[0:shock-1]
                    collapse = distribution[shock-1]+distribution[shock]
                    upper = distribution[shock+1:Ncap]
                else:
                    lower = np.mat([]).T
                    collapse = np.mat([]).T
                    upper = distribution[shock+1:Ncap]
                nulla = np.mat([0])
                distribution = np.bmat('lower;collapse;upper;nulla').copy()
        return GDPs
                    
    



if __name__ == "__main__":
    if TEST:
        Ncap = 900
        simulate = True
        how_many = 10
        countries = 4
    else:
        Ncap = 900
        simulate = False
        how_many = HOW_MANY
        countries = None


    if TEST:
        fname = 'jobs_test.%s.pickle' % PARAMETER
    else:
        fname = 'jobs.%s.pickle' % PARAMETER

    try:
        # if we already have some jobs submitted, load their IDs
        jobs = pickle.load(open(fname,'r'))
    except:
        jobs = dict()
        jobs[PARAMETER] = dict()
    print jobs
  
    # connect to PiCloud
    cloud.setkey(KEY_ID,SECRET_KEY)

    # read list of countries
    GDP_list = read_gdp()[0:countries]
    population_list = read_population()[0:countries]

    # Year 90 is 1870+90 = 1960
    # Year 140 is 1870+140 = 2010
    T1 = 90
    T2 = 140
    # annual simulation
    dt = 1
    # helper matrix to calcuate decade means
    decade_mean = np.mat(np.kron(np.eye((T2-T1+1)/10*dt),np.ones((10/dt,10/dt))/10*dt))

    # walk through each alternative
    for value in ALTERNATIVES[PARAMETER]:
        # use default parameter values from settings.py
        parameters = DEFAULT.copy()
        # except for PARAMETER, for which we are doing the loop
        parameters[PARAMETER] = value
        # two percent expected growth rate
        parameters['Lambda'] = parameters['gamma']+0.02
        # USA variance should match data
        theta_USA = logarithmic_theta_from_concentration(USA_VAR/parameters['gamma'])
        nbar_USA = logser.mean(theta_USA)
        print 'USA has theta=%f and n=%f' % (theta_USA, nbar_USA)

        parameters['epsilonpibar'] = USA_GDP/nbar_USA
        parameters['Ncap'] = Ncap

        # test assumptions
        assert 1/(parameters['epsilon']-1) + parameters['theta_N'] <= 1+parameters['theta_m0']
        
        # create a scenario to be simulated with the parameters
        scenario = Scenario(
                GDP_list,population_list,dt=dt,how_long=142,
                T1=T1,T2=T2,**parameters)

        # size of scenario object. crucial if sending to picloud over network
        print len(pickle.dumps(scenario))

        # submit jobs and save their IDs
        jids = simulate_all_worlds(scenario,how_many)
        try:
            previous_ids = list(jobs[PARAMETER][value])
        except:
            previous_ids = []
        previous_ids.extend(jids)
        jobs[PARAMETER][value] = previous_ids

    print jobs
    # write job ids to a file
    if not TEST:
        pickle.dump(jobs,open('jobs.%s.pickle' % PARAMETER,'w'))
    else:
        pickle.dump(jobs,open('jobs_test.%s.pickle' % PARAMETER,'w'))

    
