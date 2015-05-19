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
                       'apply_apcorr': ['apply_apcorrHDI.e', True]}


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
    ir.display(dataSetDirectory + currentFrame + '/' + currentFrame + '.imh', 1)
    ir.imexam()
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
        os.remove(dataSetDirectory + currentFrame + '/' + currentFrame + '.coo')
        os.remove(dataSetDirectory + currentFrame + '/' + currentFrame + '.ap')
    except OSError:
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
            os.remove(dataSetDirectory + currentFrame + '/' + currentFrame + '.lst')
        except OSError:
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
    print '\nFinished with PSF Error Star Deletion\n'
    return

def neighborStarSubtraction():
    '''Neighbor Star Subtraction'''
    print '\nStarting Neighbor Star Subtraction\n'
    print '\nFinished with Neighbor Star Subtraction\n'
    return

def mkpsfScript():
    print '\nStarting mkpsf Script\n'
    print '\nFinished mkpsf Script\n'
    return

def badPSFSubtractionStarRemoval():
    print '\nStarting bad PSF subtraction removal\n'
    print '\nFinished with bad PSF subtraction removal\n'
    return

def allstarScript():
    print '\nStarting allstar Script\n'
    print '\nFinished with allstar Script\n'
    return

def makePlots():
    print '\nStarting to make plots\n'
    print '\nFinished making plots\n'
    return

def alsedt():
    print '\nStarting alsedt\n'
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

print 'done with FWHM stuff'

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
    ###
    # Get the FWHM from the current frame.
    #   Try to see if I can get into the daophot window from this program
    #   and if so, can I find out when the user is done? If not, provide
    #   a single line of code they can
    ###
    #getFWHM()

    ###
    # PSF Fitting, First Pass (2)
    ###
    #psfFirstPass()

    ###
    # PSF Candidate Selection (3)
    ###
    #psfCandidateSelection()

    ###
    #
