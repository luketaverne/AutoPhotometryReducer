#!/usr/bin/env python
"""Program:     AutoPhotoReducer
    Author:      Luke T. Taverne
      Date:        2/8/15

Description: The purpose of this program is to reduce the amount of time spent typing
              things into the terminal windows during photometric data reduction and
              subsequent aperture correction. Users should go through the process manually
              a few times so they understand what this program is doing. This will help
              inexperienced users avoid making mistakes.

Usage:       This program will ask for a step number to execute, corresponding to the
              numbers I placed in the manual. The function corresponding to that step in
              the manual will be executed, and the user will be asked for further input as
              needed. At the completion of the task, the results will need to be checked
              by the user, either in terminal output from this program, or in a file saved
              in the working directory.
"""
import csv
import io
import os
import subprocess
import math
import HelperFunctions
from pyraf import iraf as ir
from string import Template

# top level working directory, with trailing slash. Like
# '/data/n2158_phot/n2158/'
dataSetDirectory = ''
currentFrame = ''     # current frame. Like 'n21157'
frameFWHM = None   # will hold the FWHM later
optFilesSetup = False  # true if setup has been completed successfully

testing = True

externalProgramDict = {'daophot': ['daophot', True],  # {functionName : [computerFunctionName, exists?]}
                       'compapcorr': ['compapcorrHDI.e', True],
                       'pyraf': ['pyraf', True],
                       'ds9': ['ds9', True],
                       'dao2iraf': ['dao2iraf.e', True],
                       'sm': ['sm', True],
                       'pstopdf': ['pstopdf', True],
                       'alsedt': ['alsedt.e', True],
                       'sigrejfit': ['sigrejfit.e', True],
                       'poly': ['poly.e', True],
                       'apply_apcorr': ['apply_apcorrHDI.e', True],
                       'sublst': ['sublst.e', True],
                       'magChiRoundPlotscr' : ['magChiRoundPlot.scr', True]}


def getWorkingDirectories():
    '''Set up the variables for the working folder and directories. Option 0.'''
    question1 = 'Enter the current working directory (ex: /data/n2158_phot/n2158/): '
    dataSetDirectory = raw_input(question1)

    while not os.path.isdir(dataSetDirectory):
        print 'Invalid path, try again.'
        dataSetDirectory = raw_input(question1)

    if dataSetDirectory[-1] != '/':
        dataSetDirectory += '/'

    question2 = 'Enter the frame you want to work on (ex: n21158): '
    currentFrame = raw_input(question2)
    while not os.path.isdir(dataSetDirectory + currentFrame):
        print 'Invalid frame selection for ' + dataSetDirectory + currentFrame + ', try again.'
        currentFrame = raw_input(question2)

    return dataSetDirectory, currentFrame

def startDS9():
    '''if ds9 is not running, we will start it. Right now I'm going to use a messy subprocess and false killall method.
     if we ever get the intel mac working with the fortran stuff, you should change this to use the "psutil" python
     package instead. I can't very easily install it on the PPC mac.'''
    FNULL = open(os.devnull, 'w')
    testCall = subprocess.call(['/usr/bin/killall', '-d', 'ds9'], stdout=FNULL)

    # opening ds9 with a subprocess will cause it to die when this program is closed. Open it manually in another
    # window with 'ds9 &' if you want to avoid this. Or figure out how to create a persistent subprocess within python
    if testCall == 1:
        # ds9 is not runnning
        print 'ds9 doesn\'t appear to be running, starting it. Make sure the window comes up before you try to use ds9 things. I won\'t check again.\n'
        subprocess.Popen(['ds9'])
    elif testCall == 0:
        print 'ds9 is already running'

    return

def checkFunctionsExist():
    '''Loop through function dictionary to check if all functions are callable'''
    print '\nChecking function dictionary to make sure all functions are callable before we start reduction...'
    problem = False
    for programKey in externalProgramDict:
        exists = HelperFunctions.which(externalProgramDict[programKey][0])
        if not exists:
            externalProgramDict[programKey][1] = False
            problem = True
            print "Cannot execute program " + programKey + " called as '" + externalProgramDict[programKey][0] + "'"
    if problem:
        print '\nThe function(s) listed above are not callable. You should fix this before proceeding.\n'
    else:
        print '\nAll functions are callable.\n'
    return None


def optFilesExist():
    '''Returns true if all options files are in place. Should be called before each function is executed'''
    import OptionFiles

    pathToFile = dataSetDirectory + currentFrame + '/'
    #badFiles = []
    filesExist = True

    for fileName in OptionFiles.optionFileDict:
        if os.path.exists(pathToFile + fileName):
            continue
        else:
            filesExist = False
            # badFiles.append(file)
            continue

    if filesExist:
        return True
    else:
        return False


def setupOptFiles():
    '''Sets up the option files'''
    print '\nChecking to see if option files exist...\n'
    import OptionFiles

    opt = OptionFiles.OptionFiles(frameFWHM, dataSetDirectory, currentFrame)

    for fileName in opt.optionFileDict:
        pathToFile = dataSetDirectory + currentFrame + '/' + fileName
        if not os.path.exists(pathToFile):
            print 'Option file ' + fileName + ' does not exist.'
            createFile = raw_input(
                'Do you want to create this file from a template? (y/n): ')
            while createFile not in ['Y', 'y', 'N', 'n']:
                print 'Invalid response'
                createFile = raw_input(
                    'Do you want to create this file from a template? (y/n): ')

            if createFile in ['Y', 'y']:
                fileHandle = open(pathToFile, 'w')
                fileHandle.write(opt.optionFileDict[fileName])
                fileHandle.close()
            else:
                continue

    print '\nDone dealing with option files\n'
    return


def getFWHM():
    '''Gets FWHM, returns the value'''
    print '\nStarting FWHM\n'
    print 'Opening '+currentFrame+'.imh in DS9. Hover over a star and press \'a\' to see details. The FWHM is under the \'ENCLOSED\' heading.'

    try:
        ir.display(dataSetDirectory + currentFrame + '/' + currentFrame + '.imh', 1)
        ir.imexam()
    except:
        print 'There was a problem using the iraf package. Try opening \'ds9 &\' in another window'
        return

    while True:
        userIn = raw_input('Please enter the FWHM: ')
        try:
            float(userIn)
        except ValueError:
            print 'Invalid input, cannot cast to float'
            continue
        frameFWHM = float(userIn)
        break

    print '\nFinished with FWHM\n'
    return


def psfFirstPass():
    '''First time through the PSF'''
    '''I'm going to write this in the old way, by creating a list of input commands in a text file,
    saving it, then running that into daophot. This isn't really optimal. I'd like to use pexpect, or something
    like it, but it might be a dead-end trying to build that from source on the PPC mac pro. This is something
    you may look into once we get to the intel macs, or if you run out of data to reduce (ha).'''
    print '\nStarting PSF First pass\n'
    psfFirstFile = open(dataSetDirectory + currentFrame + '/' + 'psfFirstPass.in', 'w')
    psfFirstFile.truncate() # make sure it's blank before we start this.
    try:
        #getting rid of the files we'll generate in this step before we start
        os.remove(dataSetDirectory + currentFrame + '/' + currentFrame + '.coo')
        os.remove(dataSetDirectory + currentFrame + '/' + currentFrame + '.ap')
    except OSError:
        #python gives an error if the file doesn't exist. We don't care.
        pass

    psfCommands = Template('''at ${current_frame}.imh
nomon
fi
1 1
${current_frame}.coo
y
ph


${current_frame}.coo
${current_frame}.ap
''')

    '''NOTEEEEEE: I am using relative names. I lost ssh access so I can't test this with daophot directly.
    You might need to change this to explicit paths from the root directory. I think this will be fine, since
    I am writing the file explcitly to the directory we want, and running it from that directory (maybe the call on the
    next line needs to give an explicit path?). Just a note on a potential sticking point.'''

    psfFirstFile.write(psfCommands.substitute(current_frame=currentFrame))
    psfFirstFile.close()

    if not testing:
        subprocess.call([externalProgramDict['daophot'][0], '<', 'psfFirstPass.in', '>>', currentFrame + '.log'])

    '''I'm not including the optional step from the manual. You really only need to do that if there are problems'''

    print '\nCheck the log, record the number of stars and the estimated magnitude limit'
    print '\nFinished with PSF First pass\n'
    return


def psfCandidateSelection():
    '''Picking candidate stars'''
    print '\nStarting PSF Candidate Selection\n'
    while True:
        psfCandidate = open(dataSetDirectory + currentFrame + '/' + 'psfCandidate.in', 'w')
        psfCandidate.truncate() #make sure it's blank before we start this.
        try:
            #getting rid of the files we'll generate in this step before we start
            os.remove(dataSetDirectory + currentFrame + '/' + currentFrame + '.lst')
        except OSError:
            #python gives an error if the file doesn't exist. We don't care.
            pass

        numStars = 0
        magLimit = 0

        while True:
            try:
                numStars = int(raw_input('Number of stars? '))
                magLimit = float(raw_input('Magnitude limit? '))
            except ValueError:
                print 'Invalid input, try again.'
                continue
            break

        psfCommands = Template('''at ${current_frame}.imh
nomon
pi
${current_frame}.ap
${num_stars} ${mag_limit}
${current_frame}.lst
''')


        psfCandidate.write(psfCommands.substitute(current_frame=currentFrame,num_stars=numStars,mag_limit=magLimit))
        psfCandidate.close()

        if not testing:
            subprocess.call([externalProgramDict['daophot'][0], '<', 'psfCandidate.in', '>>', currentFrame + '.log'])

        # we could probably read in the file and use a regexp to find the number of stars
        # and display it right here. Keep in mind, the log will contain multiple of these
        # patterns, you want the last one. Either find all of them and get the last occurance
        # (messy way), or figure out how to do a reverse direction regexp search (right to left).
        # php has this function, I'm not sure if python does though.
        userHappy = raw_input('Check the log. Are you okay with the number of stars? (y/n) ')
        if userHappy in ['y','Y']:
            break
        else:
            print 'Starting over'

    print '\nCheck the log, record the number of stars.'
    print 'IF THIS IS A LONG EXPOSURE: go edit ' + currentFrame + '.lst so that it has 100-200 stars, as described in the manual'
    print '\nFinished with PSF Candidate Selection\n'
    return

def psfErrorDeletion():
    '''Removing errored stars'''
    print '\nStarting PSF Error Star Deletion\n'
    redoPsf = True
    while redoPsf:
        print 'Creating ' + currentFrame + '.psf\n'
        psfCandidate = open(dataSetDirectory + currentFrame + '/' + 'psfErrorDeletion.in', 'w')
        psfCandidate.truncate() #make sure it's blank before we start this.
        try:
            #getting rid of the files we'll generate in this step before we start
            os.remove(dataSetDirectory + currentFrame + '/' + currentFrame + '.psf')
        except OSError:
            #python gives an error if the file doesn't exist. We don't care.
            pass

        psfCommands = Template('''at ${current_frame}.imh
nomon
ps
${current_frame}.ap
${current_frame}.lst
${current_frame}.psf
''')

        psfCandidate.write(psfCommands.substitute(current_frame=currentFrame))
        psfCandidate.close()

        if not testing:
            subprocess.call([externalProgramDict['daophot'][0], '<', 'psfErrorDeletion.in', '>>', currentFrame + '.log'])

        while True:
            badStars = raw_input('Check the log. Were there any stars with errors? (y/n) ')
            if badStars in ['y','Y']:
                # stars with errors, run again
                redoPsf = True # I know this is redundant, leaving in for clarity.
                break
            elif badStars in ['n', 'N']:
                # no more errors, move on.
                redoPsf = False
                break
            else:
                print 'Invalid input, try again'
                continue

    #now we can delete the old .iraf file (if there is one), and make a new one
    try:
        #getting rid of the files we'll generate in this step before we start
        os.remove(dataSetDirectory + currentFrame + '/' + currentFrame + '.iraf')
    except OSError:
        #python gives an error if the file doesn't exist. We don't care.
        pass

    if not testing:
        subprocess.call([externalProgramDict['dao2iraf'][0],currentFrame+'.lst',currentFrame+'.iraf'])

    print '\nFinished with PSF Error Star Deletion\n'
    return

def neighborStarSubtraction():
    '''Neighbor Star Subtraction'''
    keepGoing = True
    while keepGoing:
        print '\nStarting Neighbor Star Subtraction\n'
        if not os.path.exists(dataSetDirectory + currentFrame + '/' + currentFrame + '.iraf'):
            print currentFrame + '.iraf doesn\'t appear to exist. Please go create it then run this step again.'
            return

        if not os.path.exists(dataSetDirectory + currentFrame + '/' + currentFrame + '.lst'):
            print currentFrame + '.lst doesn\'t appear to exist. Please go create it then run this step again.'
            return

        skipStarSelection = False
        if os.path.exists(dataSetDirectory + currentFrame + '/sub_nonei.lst'):
            while True:
                deleteNoneiList = raw_input('sub_nonei.lst exists. Do you want me to delete it? (y/n)')
                if deleteNoneiList in ['y','Y']:
                    try:
                        os.remove(dataSetDirectory + currentFrame + '/sub_nonei.lst')
                    except OSError:
                        print 'unable to delete sub_nonei.lst'

                    break
                elif deleteNoneiList in ['n','N']:
                    skipStarSelection = True
                    break
                else:
                    print 'Invalid selection, try again'
                    continue


        try:
            #getting rid of the files we'll generate in this step before we start
            os.remove(dataSetDirectory + currentFrame + '/' + currentFrame + '_nonei.lst')
        except OSError:
            #python gives an error if the file doesn't exist. We don't care.
            pass

        if not skipStarSelection:
            try:
                ir.display(dataSetDirectory + currentFrame + '/' + currentFrame + '.imh', 1)
                ir.tvmark(1,dataSetDirectory + currentFrame + '/' + currentFrame + '.iraf',number='no',mark='circle',radii=10,color=204)
                print 'In ds9, press \'a\' over all marked stars that have neighbors that are too close.'
                ir.tvmark(1,dataSetDirectory + currentFrame + '/sub_nonei.lst', interactive='yes',number='no',mark='circle',radii=10,color=205)
            except:
                print 'There was a problem using the iraf package. Try opening \'ds9 &\' in another window and run this step again.'
                return

        # running sublst.e
        if not os.path.exists(dataSetDirectory + currentFrame + '/sub_nonei.lst'):
            print 'sub_nonei.lst doesn\'t appear to exist. Please go create it then run this step again.'
            return

        # below may need explicit paths, depending on where you run the application from
        sublst1 = Template('''${current_frame}.lst
sub_nonei.lst
${current_frame}_nonei.lst
5 5
''')
        sublstFile = open(dataSetDirectory + currentFrame + '/' + 'sublst1.in', 'w')
        sublstFile.truncate() #make sure it's blank before we start this.
        sublstFile.write(sublst1.substitute(current_frame=currentFrame))
        sublstFile.close()

        if not testing:
            subprocess.call([externalProgramDict['sublst'][0],'<','sublst1.in'])

        #running daophot one more time
        psfCandidate = open(dataSetDirectory + currentFrame + '/' + 'psfNeighborStars.in', 'w')
        psfCandidate.truncate() #make sure it's blank before we start this.

        psfCommands = Template('''at ${current_frame}.imh
nomon
ps
${current_frame}.ap
${current_frame}_nonei.lst
${current_frame}_nonei.psf
''')

        psfCandidate.write(psfCommands.substitute(current_frame=currentFrame))
        psfCandidate.close()

        if not testing:
            # there might be a hang here if it finds bad stars. Could just insert a bunch of 'y' lines into the
            # template above if you need to
            subprocess.call([externalProgramDict['daophot'][0], '<', 'psfNeighborStars.in', '>>', currentFrame + '.log'])

        while True:
            userHappy = raw_input('Go get the chi squared value from the log. Is this okay? (y/n)')
            if userHappy in ['y','Y']:
                keepGoing = False
                break
            elif userHappy in ['n', 'N']:
                keepGoing = True
                break
            else:
                print 'Invalid selection, try again'
                continue

    print '\nFinished with Neighbor Star Subtraction\n'
    return

def mkpsfScript():
    print '\nStarting mkpsf Script\n'
    #this could hang, since scripts might not actually exit and return something when they're done.
    # user `subprocess.Popen()`` instead of `subprocess.call()` here if that happens
    subprocess.call('./mkpsf.scr')
    while not os.path.exists(dataSetDirectory + currentFrame + '/' + currentFrame + '3s.imh'):
        #mkpsf is not done
        continue

    print '\nFinished mkpsf Script\n'
    return

def badPSFSubtractionStarRemoval():
    keepGoing = True
    while keepGoing:
        print '\nStarting bad PSF subtraction removal\n'
        if not os.path.exists(dataSetDirectory + currentFrame + '/' + currentFrame + '.iraf'):
            print currentFrame + '.iraf doesn\'t appear to exist. Please go create it then run this step again.'
            return

        if not os.path.exists(dataSetDirectory + currentFrame + '/' + currentFrame + '.lst'):
            print currentFrame + '.lst doesn\'t appear to exist. Please go create it then run this step again.'
            return

        skipStarSelection = False
        if os.path.exists(dataSetDirectory + currentFrame + '/sub.lst'):
            while True:
                deleteSubList = raw_input('sub.lst exists. Do you want me to delete it? (y/n)')
                if deleteSubList in ['y','Y']:
                    try:
                        os.remove(dataSetDirectory + currentFrame + '/sub.lst')
                    except OSError:
                        print 'unable to delete sub.lst'

                    break
                elif deleteSubList in ['n','N']:
                    skipStarSelection = True
                    break
                else:
                    print 'Invalid selection, try again'
                    continue


        try:
            #getting rid of the files we'll generate in this step before we start
            os.remove(dataSetDirectory + currentFrame + '/' + currentFrame + '_2.lst')
            os.remove(dataSetDirectory + currentFrame + '/' + currentFrame + '3s.psf')
        except OSError:
            #python gives an error if the file doesn't exist. We don't care.
            pass

        if not skipStarSelection:
            try:
                ir.display(dataSetDirectory + currentFrame + '/' + currentFrame + '.imh', 2)
                ir.tvmark(2,dataSetDirectory + currentFrame + '/' + currentFrame + '.iraf',number='no',mark='circle',radii=10,color=204)
                print 'In ds9, press \'a\' over all stars with subtraction errors.'
                ir.tvmark(2,dataSetDirectory + currentFrame + '/sub.lst', interactive='yes',number='no',mark='circle',radii=10,color=205)
            except:
                print 'There was a problem using the iraf package. Try opening \'ds9 &\' in another window and run this step again.'
                return

        # running sublst.e
        if not os.path.exists(dataSetDirectory + currentFrame + '/sub.lst'):
            print 'sub.lst doesn\'t appear to exist. Please go create it then run this step again.'
            return

        # below may need explicit paths, depending on where you run the application from
        sublst2 = Template('''${current_frame}.lst
sub.lst
${current_frame}_2.lst
5 5
''')
        sublstFile = open(dataSetDirectory + currentFrame + '/' + 'sublst2.in', 'w')
        sublstFile.truncate() #make sure it's blank before we start this.
        sublstFile.write(sublst2.substitute(current_frame=currentFrame))
        sublstFile.close()

        if not testing:
            subprocess.call([externalProgramDict['sublst'][0],'<','sublst2.in'])

        #running daophot one more time
        if not os.path.exists(dataSetDirectory + currentFrame + '/' + currentFrame + '3s.imh'):
            print currentFrame + '3s.imh doesn\'t appear to exist. Please go create it then run this step again.'
            return

        psfCandidate = open(dataSetDirectory + currentFrame + '/' + 'psfSubErrorStars.in', 'w')
        psfCandidate.truncate() #make sure it's blank before we start this.

        psfCommands = Template('''at ${current_frame}3s.imh
nomon
ps
${current_frame}.ap
${current_frame}_2.lst
${current_frame}3s.psf
''')

        psfCandidate.write(psfCommands.substitute(current_frame=currentFrame))
        psfCandidate.close()

        if not testing:
            # there might be a hang here if it finds bad stars. Could just insert a bunch of 'y' lines into the
            # template above if you need to
            subprocess.call([externalProgramDict['daophot'][0], '<', 'psfSubErrorStars.in', '>>', currentFrame + '.log'])

        while True:
            userHappy = raw_input('Go get the chi squared value from the log. Is this okay? (y/n)')
            if userHappy in ['y','Y']:
                keepGoing = False
                break
            elif userHappy in ['n', 'N']:
                keepGoing = True
                break
            else:
                print 'Invalid selection, try again'
                continue

    print '\nFinished with bad PSF subtraction removal\n'
    return

def allstarScript():
    '''I'm not cleaning up after this script. You'll have to delete the output files from it
    manually if something goes wrong. Feel free to automate this as I've done in the other
    functions above if you want.'''
    print '\nStarting allstar Script\n'
    #this could hang, since scripts might not actually exit and return something when they're done
    # user `subprocess.Popen()`` instead of `subprocess.call()` here if that happens
    subprocess.call('./allstarHDI.scr')
    while not os.path.exists(dataSetDirectory + currentFrame + '/' + currentFrame + 'sub2.imh'):
        #mkpsf is not done
        continue

    try:
        ir.display(dataSetDirectory + currentFrame + '/' + currentFrame + 'sub2.imh', 3)
    except:
        print 'There was a problem displaying ' + currentFrame + 'sub2.imh with iraf. Try it in another window.'

    while True:
        userHappy = raw_input('Does the image in frame 3 look okay? (y/n) ')
        if userHappy in ['y','Y']:
            break
        elif userHappy in ['n', 'N']:
            print 'Okay. You should cleanup the output files and run this step again.'
            return
        else:
            print 'Invalid selection, try again.'
            continue

    if not testing:
        subprocess.call([externalProgramDict['dao2iraf'][0],currentFrame+'.als2','als.iraf'])

    print '\nFinished with allstar Script\n'
    return

def makePlots():
    print '\nStarting to make plots\n'
    subprocess.call([externalProgramDict['magChiRoundPlotscr'][0]])
    print '\nFinished making plots\n'
    return

def alsedt():
    print '\nStarting alsedt\n'
    if not os.path.exists(dataSetDirectory + currentFrame + '/' + currentFrame + '.als2'):
        print currentFrame + '.als2 doesn\'t appear to exist. Please go create it then run this step again.'
        return

    psfCandidate = open(dataSetDirectory + currentFrame + '/' + 'alsedt.in', 'w')
    psfCandidate.truncate() #make sure it's blank before we start this.

    #string below assumes you're not using a nonlinear mag cut. Add another
    # variable if this becomes a thing you need often.
    psfCommands = Template('''${current_frame}.als2
edt${current_frame}.als2
2
0.1
0
2
0.2
''')

    psfCandidate.write(psfCommands.substitute(current_frame=currentFrame))
    psfCandidate.close()

    if not testing:
        subprocess.call([externalProgramDict['alsedt'][0], '<', 'alsedt.in', '>>', currentFrame + '.log'])

    if not os.path.exists(dataSetDirectory + currentFrame + '/' + currentFrame + '.als2'):
        print 'Something went wrong. ' + currentFrame + '.als2 doesn\'t appear to exist.'
        return

    if not testing:
        subprocess.call([externalProgramDict['dao2iraf'][0],'edt' + currentFrame+'.als2','edt.iraf'])

    if not os.path.exists(dataSetDirectory + currentFrame + '/' + 'edt.iraf'):
        print 'Something went wrong. edt.iraf doesn\'t appear to exist.'
        return

    try:
        ir.display(dataSetDirectory + currentFrame + '/' + currentFrame + '.imh', 1)
        ir.tvmark(1,dataSetDirectory + currentFrame + '/edt.iraf',number='no',mark='point',pointsize=2,color=204)
    except:
        print 'There was a problem using the iraf package. Try opening \'ds9 &\' in another window and run this step again.'
        return

    print 'There should be a mark on every non-saturated star in frame 1.'
    print '\nFinished with alsedt\n'
    return

functionDictionary = {0: getWorkingDirectories,
                         1: getFWHM,
                         2: setupOptFiles,
                         3: psfFirstPass,
                         4: psfCandidateSelection,
                         5: psfErrorDeletion,
                         6: neighborStarSubtraction,
                         7: mkpsfScript,
                         8: badPSFSubtractionStarRemoval,
                         9: allstarScript,
                         10: makePlots,
                         # last function in 'Data Reduction'
                         11: alsedt,
                      }

###
# Ask the user for the directories they want to use
###
startDS9()
dataSetDirectory, currentFrame = getWorkingDirectories()
checkFunctionsExist()


###
# Get the FWHM from the user
###
while True:

    fwhmQ = raw_input(
        "Do you know the FWHM of this frame? If not, we can go get it together. ")
    if fwhmQ not in ['y', 'Y', 'n', 'N']:
        print 'Invalid response'
        continue

    elif fwhmQ in ['y', 'Y']:
        fwhm = raw_input("What is the FWHM? ")
        try:
            float(fwhm)
        except ValueError:
            print 'Unable to cast FWHM to float, try again.'
            continue
        frameFWHM = float(fwhm)
        break

    elif fwhmQ in ['n', 'N']:
        getFWHM()
        break

###
# Check to see if all of the files we are about to use exist
#   If they don't, ask the user to place them in the directory,
#   or offer to copy them from this program. Store them in another
#   file as heredoc strings to prevent strange formatting problems
###

optFilesSetup = optFilesExist()
while True:
    if not optFilesSetup:
        user_selection = raw_input(
            "\nOption files don't seem to exist in this directory. Do you want to set them up?")
        if user_selection not in ['Y', 'y', 'N', 'n']:
            print 'Invalid response'
            continue
        else:
            if user_selection in ['n', 'N']:
                break
            else:
                setupOptFiles()
                if not optFilesExist():
                    print 'I tried setting them up, but they still don\'t appear to exist. Something is wrong.'
                    continue
                else:
                    break
    else:
        print '\nOption files appear to exist in this directory, moving on...\n'
        break

'''Going to make this the master log file. I'm only going to add to it, never delete it,
so if you want it deleted at some point, just rm it and this will recreate it blank'''
if not os.path.exists(dataSetDirectory + currentFrame + '/' + currentFrame + '.log'):
    # create the file, close it. This is so we can always use >> in our scripts
    fileGuy = open(dataSetDirectory + currentFrame + '/' + currentFrame + '.log', 'w').close()

###
#
# Main program loop. Option files exist, we have the fwhm. Can reduce now.
#
###


while True:
    try:
        user_selection = raw_input('What do you want to do? (enter function number or \'h\' for help)  ')
        int(user_selection)
    except ValueError:
        if user_selection == 'q' or user_selection == 'Q':
            # quit
            print 'Goodbye.'
            break
        if user_selection == 'h' or user_selection == 'H':
            # print help menu
            for (number, name) in functionDictionary.items():
                print str(number) + ':\t' + name.__name__

            print '\n'
            continue
        else:
            # invalid thing entered, try again
            print 'Please enter a valid selection'
            continue

    user_selection = int(user_selection)
    try:
        functionDictionary[user_selection]()
    except KeyError:
        print 'Invalid function number, try again.'
        continue
