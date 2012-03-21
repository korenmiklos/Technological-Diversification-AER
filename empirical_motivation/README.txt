==================================
Replication programs for Section I
==================================
Replication data for Koren, Miklós and Silvana Tenreyro. 2012. "Technological Diversification." American Economic Review. 

Please cite the above paper when using these programs.

table1.do
---------
This Stata (version 10) do-file reproduces Table 1 in the paper. 

Only uses publicly available data, which, for your convenience, we have made available in the ``data`` folder. 

Requires ``outreg2``, which you can install with:: 

     ssc install outreg2

table2.do
---------
This Stata (version 10) do-file reproduces Table 2 in the paper. 

Uses firm-level data from Standard&Poor's *Compustat North America* database, 2010. This is proprietary data which we cannot make available, but can be purchased from a number of vendors. You need the *Business Segments* datafile to replicate our results. Once you have the datafile in Stata format, the code should run with minimal adjustments.

Also requires ``outreg2``.

