/*
Read data from WDI and PWT and run regressions to replicate Table 1 of

	Koren, Miklós and Silvana Tenreyro. 2012. "Technological Diversification". American Economic Review.

Please cite the above paper when using this program.
*/

clear 
set mem 100m
set more off
label drop _all

* common formatting to use with outreg
local format "label bracket bdec(3)"

* expression to define the sample
local sample "year>=1960 & year<=2007"

* filename to save to
local whereto "table1.xls"

tempfile wdi


/***************** Read WDI data ************/
clear
insheet using ../data/wdi/wdioctober2010.csv
    reshape long y_, i(countrycode indicatorc) j(year)
    ren indicatorc seriescode
    keep if `sample'

    ren y_ var_
    gen str15 categ=""
    replace categ="inflation" if seriescode=="FP.CPI.TOTL.ZG"
    replace categ="exchangerate" if seriescode=="PA.NUS.FCRF"
    replace categ="reffeexchangerate" if seriescode=="PX.REX.REER"
    replace categ="tot" if seriescode=="TT.PRI.MRCH.XD.WD"
    replace categ="gdpwdippp" if seriescode=="NY.GDP.PCAP.PP.KD"
    replace categ="gdpwdi" if seriescode==   "NY.GDP.PCAP.KD"
    replace categ="popwdi" if seriescode==   "SP.POP.TOTL"
    replace categ="gshare" if seriescode=="NE.CON.GOVT.ZS"
    replace categ="privcred" if seriescode=="FS.AST.PRVT.GD.ZS"
    replace categ="trade" if seriescode=="NE.TRD.GNFS.ZS"

    /* Definitions from WDI
    GDP per capita.PPP (constant 2005 international $)	NY.GDP.PCAP.PP.KD
    GDP per capita (constant 2000 US$)	NY.GDP.PCAP.KD
    Population.total	SP.POP.TOTL
    Inflation.consumer prices (annual %)	FP.CPI.TOTL.ZG
    Official exchange rate (LCU per US$.period average)	PA.NUS.FCRF
    Real effective exchange rate index (2005 = 100)	PX.REX.REER
    Net barter terms of trade index (2000 = 100)	TT.PRI.MRCH.XD.WD
    General government final consumption expenditure (% of GDP)	NE.CON.GOVT.ZS
    Trade (% of GDP)	NE.TRD.GNFS.ZS
    Domestic credit to private sector (% of GDP)	FS.AST.PRVT.GD.ZS*/

    drop series*
    drop indicator*
    drop if categ==""

    reshape wide var_, i(countrycode year) j(categ) string
    foreach X of any inflation  tot gdpwdippp gdpwdi popwdi gshare trade privcred ref exc {
	    ren var_`X' `X'
    }

    replace inflation=inflation/100
    replace trade=trade/100
    replace gshare=gshare/100
    ren countrycode uncode

    egen cc = group(uncode)
    tsset cc year

    * define growth rates
    foreach X of any tot gdpwdippp gdpwdi {
        gen `X'growth=log(`X')-log(L.`X')
    }

    foreach X of var gdpwdippp gdpwdi popwdi {
        gen log`X' = log(`X')
    }

    keep if `sample'
    gen byte decade = int((year-1900)/10)*10
    
    collapse (mean) loggdpwdi loggdpwdippp logpopwdi (count)numwdi=gdpwdigrowth  (sd) volwdippp=gdpwdipppgrowth volwdi=gdpwdigrowth, by(uncode decade)
save `wdi', replace



/***************** Read PWT data ************/
clear
insheet using ../data/pwt/pwtcomplete.csv
    ren countryisocode uncode

    egen cc = group(uncode)
    tsset cc year

    gen growth = log(rgdpch)-log(L.rgdpch)
    gen loggdppwt = log(rgdpch)
    gen logpoppwt = log(pop)

    keep if `sample'
    gen byte decade = int((year-1900)/10)*10

    collapse (mean) loggdppwt logpoppwt (count) numpwt=growth (sd) volpwt=growth, by(uncode decade)

    /* merge the two datasets */
    sort uncode decade
    merge uncode decade using `wdi', nokeep
    tab _merge
    drop _merge

    gen logvolpwt = log(volpwt)
    gen logvolwdi = log(volwdi)
    gen logvolwdippp = log(volwdippp)

    label var logvolpwt "Log volatility PWT rgdpch"
    label var loggdppwt "GDP per capita (log) PWT"
    label var logvolwdi "Log volatility GDP pc, WDI constant dollars"
    label var logvolwdippp "Log volatility GDP pc, WDI ppp"
    label var loggdpwdi "Log GDP pc, WDI constant dollars"
    label var loggdpwdippp "Log GDP pc, WDI ppp"
    label var logpopwdi "Population WDI (log)"
    label var logpoppwt "Population PWT (log)"

    * only look at decades with at least 5 years of data 
    keep if numwdi>=5

/* set panel dimensions */
egen cc = group(uncode)
tsset cc decade

/* regressions for Table 1 */
* Column 1
reg logvolpwt loggdppwt, cluster(cc)
outreg2 using `whereto', `format' replace

* Column 2
areg logvolpwt loggdppwt, a(cc) cluster(cc) 
outreg2 using `whereto', `format' append

* Column 3
reg logvolwdi loggdpwdi, cluster(cc)
outreg2 using `whereto', `format' append

* Column 4
areg logvolwdi loggdpwdi, a(cc) cluster(cc)
outreg2 using `whereto', `format' append


