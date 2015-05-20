# AutoPhotometryReducer
Python program to handle reduction for SUNY Geneseo's photometric astronomy data.

v0.01

This program was written for the PowerPC Mac Pro in the astro research room. It likely
won't work as-is on Windows or Ubuntu (but you can try). If you are a new research student
it is in your best interest to not edit this program. I will keep a tarball of this program
as I last updated it on the RAID storage drive, so you may revert to that if something goes
really wrong.

GENERAL REMARKS:

All iraf and pyraf commands can be used from within python as long as the library has been imported. At this time,
daophot.e must be run using separate input files (subprocess.Popen and communicate only allow you to send data
once over the pipe before it closes. Silly, but that's how it works.).

INSTALLATION:
Put this program in a folder somewhere. Create an executable (call it `autoreduce` or something) and put it
somewhere in your path. The executable should call 'python /path/to/this/program/autoreduce.py'.

This (might) help alleviate trying to make *all* paths explicit within the program. I've
made them explicit where I could easily, and not messily, do that. Be aware that there may be problems
with some of the relative paths. Just follow the template I used on my explicit paths and you should
be fine. Everything is parceled up nicely into discrete sets of functions, so it shouldn't take too long
to fix problems with this.

USAGE:

1) Setup all of your data directories as we normally do. This program expects a top
level directory with the cluster name, or something like it, with folders underneath
representing each of the object frames. Inside those folders should be the images (.pix and .imh)
with the same name as their parent folder.

Example folder structure:
'''
-data
| -n2158_phot
|   -n21100
|     |n21100.imh
|     |n21100.pix
|   -n21101
|     |n21101.imh
|     |n21101.pix
|   .
|   .
|   .
'''

2) Once your folders are setup and the images are in them, run the program with ./autoreduce.py.
Although autoreduce will start ds9 if it is not running, you should start it with 'ds9 &' before
running autoreduce, as any programs called within autoreduce will close when the script is exited.

3) Enter the working directory as requested. Using the directory structure above, you would enter
'/data/n2158_phot/' at the first prompt and 'n21100' at the second prompt. The second will change
with the current frame you are working on.

4) Enter the FWHM. You can simply enter it if you already know it, or let the script open the image and
imexam for you.

5) Continue with reduction. Start with 1 and move on from there. You may go back and redo things at any time,
just make sure you clean up after yourself if you do start over (delete or backup files, as they may be overwritten)
