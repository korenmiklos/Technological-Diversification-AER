/*
Read firm-level data from Compustat and run regressions to replicate Table 2 of

	Koren, Miklós and Silvana Tenreyro. 2012. "Technological Diversification". American Economic Review.

Please cite the above paper when using this program.
*/

clear all
set mem 160m

* filename to save to
local whereto "table2.xls"

* common formatting to use with outreg
local format "label bracket ctitle("Log(Var. of sales growth)") bdec(3)"

/*
Read data from Compustat here. 
We are using the business segments dataset from Compustat US 2010.
*/
use ../../data/firmlevel/segments

keep if !missing(sale)
/* 0.5% of the sample has missing sales */

egen rank = rank(-srcyr), by(gvk sid year)
keep if rank==1
drop rank
/* Some firms report data multiple times, keep data with lates source year.
   srcyr: year of reporting
   gvk: unique identifier of firm
   sid: identifier of business segment */

keep gvkey year sid sale emp

/* Add up all business segments for Table 2. */
collapse (sum) sale emp (count) N=sale, by(gvk year)

tsset gvk year

gen growth = log(sale)-log(L.sale)
gen period = int(year/5)*5
gen logsale = ln(sale)
gen logemp = ln(emp)

collapse (sd) vol = growth (mean) growth sale emp logsale logemp (max) N, by(gvk period)

tsset gvk period
gen logvol = ln(vol)
gen logN = ln(N)

label var logvol "Log(Var. of sales growth)"
label var logsale "Log(Mean Sales)"
label var logemp "Log(Mean Employees)"
label var logN "Log(Number of business segments)"

local after "i.period, cluster(gvk)"

tsset gvkey period

/* Regressions for Table 2 */
* Column 1
reg logvol logemp `after'
outreg2 using `whereto', `format' replace
* Column 2
areg logvol logemp `after' a(gvk)
outreg2 using `whereto', `format' append
* Column 3
reg logvol logsale `after'
outreg2 using `whereto', `format' append
* Column 4
areg logvol logsale `after' a(gvk)
outreg2 using `whereto', `format' append

