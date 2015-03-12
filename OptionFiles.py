#!/usr/bin/env python
from string import Template
'''testtt = Template("""This is
an $example""")
print testtt.substitute(example="example2")
'''

class OptionFiles:
    """Contains all of the option files and scripts needed to reduce HDI photometry. Files are stored
    as string Templates formatted with multiline strings (so Fortran doesn't choke on spaces, as it
    often does). String substitutions can be generated using string.substitute(key="value"). Alternatively
    you can use safe_substitute, although this will cause you to miss a KeyValue excepton if you forget to
    substitute in the value for a key

    DO NOT RUN THIS FILE THROUGH ATOM BEAUTIFY: it will ruin the formatting of the multiline strings.
    """

    allStarOpt = Template("""fi=$fwhm
wa=0
is=33
os=36""")

    apCorrOpt = Template("""A1 = 4
A2 = 7
A3 = 10
A4 = 13
A5 = 16
A6 = 18
A7 = 21
A8 = 24
A9 = 27
AA = 30
AB = 33
AC = 36
IS = 36
OS = 38""")

    daoPhotOpt = Template("""RE=9
GA=1.3
LO=10
FW=$fwhm
FI=$fwhm
WA=0
VA=2
HI=55000
TH=7
PS=15
LR=-2
HR=2
LS=0
HS=2
AN=3
EX=5""")

    photoOpt = Template("""A1 = $fwhm
A2 = 0
A3 = 7
A4 = 8
A5 = 10
A6 = 12
A7 = 14
A8 = 16
A9 = 18
AA = 20
AB = 22
AC = 24
IS = 27
OS = 34 """)

    ####
    #
    # Scripts are located below
    #
    ####

    allStarHDIscr = Template("""#!/bin/sh
#
# Shell script to run ALLSTAR and FIND, PHOT, and ALLSTAR again
#
cd ${workingDirectory}${currentFrame}
#
echo ' ' > inpfile1
echo '${currentFrame}' >> inpfile1
echo '${currentFrame}3s.psf' >> inpfile1
echo '${currentFrame}.ap' >> inpfile1
echo '${currentFrame}.als' >> inpfile1
echo '${currentFrame}sub' >> inpfile1
#
# run ALLSTAR to execute the previous commands.
#
allstar8192 < inpfile1 > allstar.log
#
echo 'at ${currentFrame}sub' > inpfile2
echo 'nomon' >> inpfile2
echo 'opt' >> inpfile2
echo ' ' >> inpfile2
echo 'lo=100' >> inpfile2
echo ' ' >> inpfile2
echo 'fi' >> inpfile2
echo '1 1' >> inpfile2
echo '${currentFrame}sub.coo' >> inpfile2
echo 'y' >> inpfile2
#
echo 'phot' >> inpfile2
echo 'photo.opt' >> inpfile2
echo ' ' >> inpfile2
echo '${currentFrame}sub.coo' >> inpfile2
echo '${currentFrame}sub.ap' >> inpfile2
#
# run DAOPHOT
#
daophot < inpfile2 >> allstar.log
#
echo '${currentFrame}sub.ap' > inpfile3
echo '${currentFrame}sub.apals' >> inpfile3
#
# run AP2ALS
#
ap2als.e < inpfile3 >> allstar.log
#
echo 'nomon' > inpfile4
echo 'append' >> inpfile4
echo '${currentFrame}.als' >> inpfile4
echo '${currentFrame}sub.apals' >> inpfile4
echo '${currentFrame}.ap2' >> inpfile4
echo 'sort' >> inpfile4
echo '3' >> inpfile4
echo '${currentFrame}.ap2' >> inpfile4
echo '${currentFrame}.ap2' >> inpfile4
echo ' ' >> inpfile4
echo 'y' >> inpfile4
#
# now run DAOPHOT to execute the previous commands.
#
daophot < inpfile4 >> allstar.log
#
rm ${currentFrame}sub.imh
rm ${currentFrame}sub.pix
#
echo ' ' > inpfile5
echo '${currentFrame}' >> inpfile5
echo '${currentFrame}3s.psf' >> inpfile5
echo '${currentFrame}.ap2' >> inpfile5
echo '${currentFrame}.als2' >> inpfile5
echo '${currentFrame}sub2' >> inpfile5
#
# run ALLSTAR to execute the previous commands.
#
allstar8192 < inpfile5 >> allstar.log
#
""")

    apCorrHDIscr = Template("""#!/bin/sh
#
# Shell script
#
rm inpfile?
#
echo 'sort' > inpfile1
echo '4' >> inpfile1
echo 'edt${currentFrame}.als2' >> inpfile1
echo 'apcorr.coo' >> inpfile1
echo 'no' >> inpfile1
echo 'exit' >> inpfile1
#
# run sort in daophot
#
daophot < inpfile1 > apcorr.log
#
# Pause to edit LOWBAD in apcorr.coo
#
aquamacs apcorr.coo
echo 'Please change LOWBAD to -9.4 if it is greater than -9.4 in apcorr.coo. Save and quit. Enter anything to continue.'
read nothing
#
#
#
echo 'apcorr.coo' > inpfile2
echo 'apcorr.coo2' >> inpfile2
echo '2' >> inpfile2
echo '0.07 10' >> inpfile2
#
# run erredit.e
#
erredit.e < inpfile2 >> apcorr.log
mv apcorr.coo2 apcorr.coo
#
#
#
echo 'apcorr.coo' > inpfile3
echo 'apcorr.coo2' >> inpfile3
echo '25' >> inpfile3
#
# run selstar.e
#
selstar.e < inpfile3 >> apcorr.log
mv apcorr.coo2 apcorr.coo
#
# Pause to edit apcorr.coo. remove faint stars, leaving at least 100 bright stars.
#
aquamacs apcorr.coo
echo 'Please remove faint stars from apcorr.coo, leaving at least 100 bright stars.  Magnitude 13 is often a good cutoff point.  Enter anything to continue.'
read nothing
#
#
#
echo 'edt${currentFrame}.als2' > inpfile4
echo 'apcorr.coo' >> inpfile4
echo 'apcorr.als' >> inpfile4
echo '0.5 0.5' >> inpfile4
#
# run apstar.e
#
apstar.e < inpfile4 >> apcorr.log
#
#
#
echo 'at ${currentFrame}.imh' > inpfile5
echo 'mon' >> inpfile5
echo 'sub' >> inpfile5
echo '${currentFrame}3s.psf' >> inpfile5
echo 'apcorr.als' >> inpfile5
echo 'no' >> inpfile5
echo 'apcorr' >> inpfile5
echo 'at apcorr.imh' >> inpfile5
echo 'nomon' >> inpfile5
echo 'ph' >> inpfile5
echo 'apcorr.opt' >> inpfile5
echo ' ' >> inpfile5
echo ' ' >> inpfile5
echo ' ' >> inpfile5
echo 'exit' >> inpfile5
#
# run sub in daophot
#
daophot < inpfile5 >> apcorr.log
#
# Pause to display apcorr.imh and edit apcorr.ap.
#
cp apcorr.ap apcorr.apfull
aquamacs apcorr.ap
echo 'apcorr.imh  AND apcorr.ap HAVE BEEN MADE.  CHECK THAT apcorr.imh LOOKS RIGHT AND CHECK THAT apcorr.ap HAS THE 20 BRIGHTEST ERROR-FREE STARS.  Enter anything to continue.'
read nothing2
#
#
#
#
echo 'apcorr.ap' > inpfile6
echo 'ap_plot.out' >> inpfile6
echo '12' >> inpfile6
echo 'apcorr.opt' >> inpfile6
#
# run ap_plot.e
#
ap_plot.e < inpfile6 >> apcorr.log
#
#
#
#
echo 'macro read macro1.sm' > inpfile7
echo 'dev postlandfile apcorrplot.ps' >> inpfile7
echo 'apcorrplot' >> inpfile7
echo '${currentFrame}' >> inpfile7
echo '-0.4' >> inpfile7
echo '-0.1' >> inpfile7
echo 'end' >> inpfile7
#
# make apcorrplot in sm
#
sm < inpfile7 >> apcorr.log
#
pstopdf apcorrplot.ps
open apcorrplot.pdf
rm apcorrplot.ps
#
# Pause to edit apcorr.opt
#
aquamacs apcorr.opt
echo 'Determine the apcorr radius from apcorrplot.pdf and edit apcorr.opt.  Save and quit apcorr.opt.  Enter enything to continue.'
read nothing3
#
#
echo 'at apcorr.imh' > inpfile8
echo 'ph' >> inpfile8
echo 'apcorr.opt' >> inpfile8
echo ' ' >> inpfile8
echo ' ' >> inpfile8
echo ' ' >> inpfile8
echo ' ' >> inpfile8
echo 'exit' >> inpfile8
#
# run daophot ph
#
daophot < inpfile8 >> apcorr.log
#
echo 'apcorr.ap' > inpfile9
echo 'apcorr.apals' >> inpfile9
#
# run ap2als.e
#
ap2als.e < inpfile9 >> apcorr.log
#
aquamacs apcorr.log
#
# Pause to check if everything went well
#
echo 'Check that apcorr.log looks right.  Enter anything to continue on to compapcorr.scr.  Hit Cntrl-C to continue manually.'
read nothing4
#
rm inpfile?
chmod +x compapcorrHDI.scr
./compapcorrHDI.scr ${currentFrame} 1
""")

    compApCorrHDIscr = Template("""#!/bin/sh
#
# Shell script to make spatial dependency plots starting from sigrejfit.e
# Change directory and plot iteration (i.e. xplot1 vs xplot2)
#
# first argument is image name, i.e. "v21"
# second argument is iteration, i.e. "1"
#
#
#
rm apcorr.out
rm fit.dat
rm poly.dat
rm poly?$2.dat
rm ?fitpts$2
rm *.log
rm inpfile?
#
#
echo 'Enter filename of PSF photometry.'
read apcorr
#
echo "$apcorr" > inpfile3
echo "apcorr.apals" >> inpfile3
echo "apcorr.out" >> inpfile3
#
# Run compapcorrHDI.e
#
compapcorrHDI.e < inpfile3 > compapcorr.log
rm inpfile3
#
echo "fit.dat" > inpfile0
echo "0" >> inpfile0
echo "6" >> inpfile0
echo "1 6" >> inpfile0
echo "0 0" >> inpfile0
echo "-10 10 -10 10" >> inpfile0
echo "2" >> inpfile0
echo "0" >> inpfile0
echo "1" >> inpfile0
echo "rfitpts$2" >> inpfile0
#
# Run sigrejfit.e
#
sigrejfit.e < inpfile0 > r.log
echo "Created rfitpts$2"
open SPATIALD
open r.log
rm inpfile0
#
#
echo "fit.dat" > inpfile0
echo "0" >> inpfile0
echo "6" >> inpfile0
echo "4 6" >> inpfile0
echo "0 0" >> inpfile0
echo "-10 10 -10 10" >> inpfile0
echo "2" >> inpfile0
echo "0" >> inpfile0
echo "1" >> inpfile0
echo "xfitpts$2" >> inpfile0
#
# Run sigrejfit.e
#
sigrejfit.e < inpfile0 > x.log
echo "Created xfitpts$2"
open x.log
rm inpfile0
#
#
echo "fit.dat" > inpfile0
echo "0" >> inpfile0
echo "6" >> inpfile0
echo "5 6" >> inpfile0
echo "0 0" >> inpfile0
echo "-10 10 -10 10" >> inpfile0
echo "2" >> inpfile0
echo "0" >> inpfile0
echo "1" >> inpfile0
echo "yfitpts$2" >> inpfile0
#
# Run sigrejfit.e
#
sigrejfit.e < inpfile0 > y.log
echo "Created yfitpts$2"
open y.log
rm inpfile0
#
#
#
# PROMPTS USER TO PROVIDE COEFFICIENTS FOR POLY.E
#
echo "Enter the r zero order term coefficient from r.log"
read rzeroorder
echo "Enter the r first order term coefficient from r.log"
read rfirstorder
#
echo "poly.dat" >> inpfile2
echo "$rzeroorder $rfirstorder 0 0 0" >> inpfile2
echo "-10 10 100 0" >> inpfile2
#
poly.e < inpfile2 >> compapcorr.log
mv poly.dat polyr$2.dat
rm inpfile2
#
echo "Enter the x zero order term coefficient from x.log"
read xzeroorder
echo "Enter the x first order term coefficient from x.log"
read xfirstorder
#
echo "poly.dat" >> inpfile2
echo "$xzeroorder $xfirstorder 0 0 0" >> inpfile2
echo "-10 10 100 0" >> inpfile2
#
poly.e < inpfile2 >> compapcorr.log
mv poly.dat polyx$2.dat
rm inpfile2
#
echo "Enter the y zero order term coefficient from y.log"
read yzeroorder
echo "Enter the y first order term coefficient from y.log"
read yfirstorder
#
echo "poly.dat" >> inpfile2
echo "$yzeroorder $yfirstorder 0 0 0" >> inpfile2
echo "-10 10 100 0" >> inpfile2
#
poly.e < inpfile2 >> compapcorr.log
mv poly.dat polyy$2.dat
rm inpfile2
#
#
echo "macro read macro1.sm" >> inpfile1
echo "dev postlandfile rplot$2.ps" >> inpfile1
echo "rplot$2" >> inpfile1
echo "$1" >> inpfile1
echo "dev postlandfile xplot$2.ps" >> inpfile1
echo "xplot$2" >> inpfile1
echo "$1" >> inpfile1
echo "dev postlandfile yplot$2.ps" >> inpfile1
echo "yplot$2" >> inpfile1
echo "$1" >> inpfile1
echo "end" >> inpfile1
#
# run sm to execute the previous commands.
#
sm < inpfile1 >> compapcorr.log
rm inpfile1
#
open compapcor.log
#
# Make PDFs of the plots
#
pstopdf rplot$2.ps
open rplot$2.pdf
rm rplot$2.ps
pstopdf xplot$2.ps
open xplot$2.pdf
rm xplot$2.ps
pstopdf yplot$2.ps
open yplot$2.pdf
rm yplot$2.ps
#
# Clean up
#
rm inpfile?
echo 'You are now ready to apply your aperture correcion.'
""")

    mkpsfHDIscr = Template("""#!/bin/sh
#
# Shell script to run PSF, ALLSTAR, and SUBSTAR to generate a PSF.
#
cd ${workingDirectory}${currentFrame}
#
# First generate the PSF for all PSF stars so that neigbors can be subtracted
#
echo 'at ${currentFrame}' > inpfile0
echo 'nomon' >> inpfile0
echo 'ps' >> inpfile0
echo '${currentFrame}.ap' >> inpfile0
echo '${currentFrame}.lst' >> inpfile0
echo '${currentFrame}.psf' >> inpfile0
echo ' ' >> inpfile0
echo ' ' >> inpfile0
#
# run DAOPHOT
#
daophot < inpfile0 > mkpsf.log
#
# Now fit the 'rough' PSF made from the uncrowded stars to stars in the neigbors file
#
echo 're=0 ' > inpfile1
echo ' ' >> inpfile1
echo '${currentFrame}' >> inpfile1
echo '${currentFrame}_nonei.psf' >> inpfile1
echo '${currentFrame}.nei' >> inpfile1
echo '${currentFrame}psf.als' >> inpfile1
echo '${currentFrame}1s' >> inpfile1
#
# run ALLSTAR to execute the previous commands.
#
allstar8192 < inpfile1 >> mkpsf.log
#
# Run FIND on the resultant frame
#
echo 'at ${currentFrame}1s' > inpfile2
echo 'nomon' >> inpfile2
echo 'opt' >> inpfile2
echo ' ' >> inpfile2
echo 'th=2' >> inpfile2
echo ' ' >> inpfile2
echo 'fi' >> inpfile2
echo '1 1' >> inpfile2
echo '${currentFrame}1s.coo' >> inpfile2
echo 'y' >> inpfile2
#
# run DAOPHOT
#
daophot < inpfile2 >> mkpsf.log
#
# Now merge the previous neighbors file and the new .coo file from FIND
#
echo '${currentFrame}.lst' > inpfile3
echo '${currentFrame}.nei' >> inpfile3
echo '${currentFrame}1s.coo' >> inpfile3
echo '${currentFrame}.neinew1' >> inpfile3
echo '20' >> inpfile3
#
# run MERGE to execute the previous commands
#
merge.e < inpfile3  >> mkpsf.log
rm ${currentFrame}1s.imh
rm ${currentFrame}1s.pix
#
# Now fit the PSF to stars in the new neighbors file
#
echo ' ' > inpfile4
echo '${currentFrame}' >> inpfile4
echo '${currentFrame}_nonei.psf' >> inpfile4
echo '${currentFrame}.neinew1' >> inpfile4
echo '${currentFrame}1s.als' >> inpfile4
echo '${currentFrame}2s' >> inpfile4
#
# run ALLSTAR to execute the previous commands.
#
allstar8192 < inpfile4 >> mkpsf.log
#
# Run FIND on the resultant frame
#
echo 'at ${currentFrame}2s' > inpfile5
echo 'nomon' >> inpfile5
echo 'opt' >> inpfile5
echo ' ' >> inpfile5
echo 'th=2' >> inpfile5
echo ' ' >> inpfile5
echo 'fi' >> inpfile5
echo '1 1' >> inpfile5
echo '${currentFrame}2s.coo' >> inpfile5
echo 'y' >> inpfile5
#
# run DAOPHOT
#
daophot < inpfile5 >> mkpsf.log
#
# Now merge the previous neighbors file and the new .coo file from FIND
#
echo '${currentFrame}.lst' > inpfile6
echo '${currentFrame}1s.als' >> inpfile6
echo '${currentFrame}2s.coo' >> inpfile6
echo '${currentFrame}.neinew2' >> inpfile6
echo '20' >> inpfile6
#
# run MERGE to execute the previous commands
#
merge.e < inpfile6  >> mkpsf.log
rm ${currentFrame}2s.imh
rm ${currentFrame}2s.pix
#
# Use ALLSTAR to keep the neighbors that are real stars
#
echo ' ' > inpfile7
echo '${currentFrame}' >> inpfile7
echo '${currentFrame}_nonei.psf' >> inpfile7
echo '${currentFrame}.neinew2' >> inpfile7
echo '${currentFrame}2s.als' >> inpfile7
echo '${currentFrame}3s' >> inpfile7
#
# run ALLSTAR to execute the previous commands.
#
allstar8192 < inpfile7 >> mkpsf.log
#
# Subtract away all neigbors except the PSF stars.
#
echo 'at ${currentFrame}' > inpfile8
echo 'nomon' >> inpfile8
echo 'sub' >> inpfile8
echo '${currentFrame}_nonei.psf' >> inpfile8
echo '${currentFrame}2s.als' >> inpfile8
echo 'y' >> inpfile8
echo '${currentFrame}.lst' >> inpfile8
echo '${currentFrame}3s' >> inpfile8
#
# Run DAOPHOT to execute the previous commands.
#
daophot < inpfile8 >> mkpsf.log
""")

    fixMkpsfscr = """#!/bin/tcsh

echo "What is the name of the image? eg 'v01' (no extension) "
set im = $<

echo ""
echo "Before:"
echo ""

ls
echo ""

rm inpfile*
rm mkpsf.log
rm "$im"1*""
rm "$im"2*""
rm "$im"3*""
rm "$im"psf.als""
rm "$im".neinew*""
rm "$im".psf""
rm "$im".nei""

echo ""
echo "After:"
echo ""

ls
echo ""
"""

    macro1scr = """#!/bin/sh
#
# Shell script to make spatial dependency plots
# Change directory and plot iteration (i.e. xplot1 vs xplot2)
#
# first argument is image name, i.e. "v21"
# second argument is iteration.
#
cd /data/n2158_phot/n2158/$1
rm inpfile
#
echo ' ' > inpfile
echo 'macro read macro1.sm' >> inpfile
echo "dev postlandfile xplot$2.ps" >> inpfile
echo "xplot$2" >> inpfile
echo "$1" >> inpfile
echo "dev postlandfile yplot$2.ps" >> inpfile
echo "yplot$2" >> inpfile
echo "$1" >> inpfile
echo "dev postlandfile rplot$2.ps" >> inpfile
echo "rplot$2" >> inpfile
echo "$1" >> inpfile
echo 'end' >> inpfile
#
# run sm to execute the previous commands.
#
sm < inpfile > macro1.log
#
# make pdf files
#
pstopdf xplot$2.ps
pstopdf yplot$2.ps
pstopdf rplot$2.ps
#
# open pdf files
#
open xplot$2.pdf
open yplot$2.pdf
open rplot$2.pdf
#
# clean up
#
rm inpfile
#rm macro1.log
rm xplot$2.ps
rm yplot$2.ps
rm rplot$2.ps
#
"""
