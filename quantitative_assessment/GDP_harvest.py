'''
Replication code for results in Section III. "Volatility and Development: A Quantitative Assessment" of

    Koren, Miklós and Silvana Tenreyro. 2012. "Technological Diversification." American Economic Review.
    
Please cite the above paper when using this program.

Harvest simulation results from PiCloud.com given a list of job IDs. Print them to the screen.
'''
import numpy as np
from numpy import log
import matplotlib.pyplot as plt
from scipy.stats import poisson, logser, norm
from scipy.optimize import bisect
import random
import cloud
import csv
import pickle
from settings_alternative import *

def done_jobs(jobs):
    '''
    Retrive the result of finished jobs from picloud.
    '''
    statuses = cloud.status(list(jobs))
    return list(cloud.iresult([y[0] for y in filter(lambda x: x[1]=='done',zip(list(jobs),statuses))]))

if __name__ == "__main__":
    
  
    # connect to PiCloud
    cloud.setkey(KEY_ID,SECRET_KEY)

    # read list of job ids
    if TEST:
        fp = open('jobs_test.%s.pickle' % PARAMETER,'r')
    else:
        fp = open('jobs.%s.pickle' % PARAMETER,'r')
    jobs = pickle.load(fp)


    stats = dict()
    stats[PARAMETER] = dict()

    # walk through all parameter values
    for value in ALTERNATIVES[PARAMETER]:
        stats[PARAMETER][value] = dict()
        for stat in STATNAMES:
            stats[PARAMETER][value][stat] = []
        # save only those jobs that have finished
        collector_jids = done_jobs(jobs[PARAMETER][value])
        results = done_jobs(collector_jids)
        print "Number of repetitions: %d" % len(results)

        # save statistics in a dictionary
        for result in results:
            for stat in STATNAMES:
                stats[PARAMETER][value][stat].append(np.mat(result[stat])[0,0])

    # save that dictionary to a file
    if not TEST:
        pickle.dump(stats,open('stats.%s.pickle' % PARAMETER,'w'))
    else:
        pickle.dump(stats,open('stats_test.%s.pickle' % PARAMETER,'w'))

    # print each statistic to screen
    for stat in STATNAMES:
        print stat
        for key in stats.keys():
            print key
            for value in stats[key].keys():
                A = np.mat(stats[key][value][stat])
                print value,
                print A.mean(),
                print A.std()
