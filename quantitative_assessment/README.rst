===================================
Replication program for Section III
===================================
Replication code for Section III of Koren, Miklós and Silvana Tenreyro. 2012. "Technological Diversification." American Economic Review. Please cite the above paper when using this program.

Prerequisites
-------------
- Python 2.7 with standard numerical libraries:
    - numpy
    - matplotlib
    - scipy
    - random
    - csv
    - pickle
    - copy
- The program uses the services PiCloud.com for parallel processing. If you would like to run it on your local computer instead, use the "multiprocessing" library. However, this would make the code *much* slower (see below).
 
Running the program
-------------------
Setting parameters
~~~~~~~~~~~~~~~~~~
In settings.py,

1. set the default parameter values, by assigning them in ``DEFAULT``,
2. set a list of alternative parameter values in ``ALTERNATIVES``,
3. pick which parameter you are going to alter by setting ``PARAMETER`` (for example, ``PARAMETER='gamma'``),
4. choose how many repetitions to use, for example, ``HOW_MANY=1000``.

Submitting jobs for computation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On your command line::

    python GDP_simulate.py
    
This creates the simulation jobs and submits them to PiCloud for processing. 

Each simulation takes about 5 seconds to run, so simulating 64 countries 1,000 times would take about 88 hours on a single processor. To speed up calculations, each job can run in parallel. To keep simulation times manageable, we have rented 160 to 640 processors from PiCloud. 

Retrieving job results
~~~~~~~~~~~~~~~~~~~~~~
On your command line::

    python GDP_harvest.py
    
This retrieves the finished jobs from PiCloud and prints the mean and standard deviation of each saved parameter. To save these results::

    python GDP_harvest.py > results.txt

We then manually formatted these results into Table 3.

