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
#import csv
#import io
import os
#import subprocess
#import math
import HelperFunctions
#from pyraf import iraf as ir

# top level working directory, with trailing slash. Like
# '/data/n2158_phot/n2158/'
dataSetDirectory = ''
currentFrame = ''     # current frame. Like 'n21157'
frameFWHM = None   # will hold the FWHM later
optFilesSetup = False  # true if setup has been completed successfully

functionDictionary = {0: 'getWorkingDirectories',
                      1: 'getFWHM',
                      2: 'setupOptFiles',
                      3: 'psfFirstPass',
                      4: 'psfCandidateSelection',
                      5: 'psfErrorDeletion',
                      6: 'neighborStarSubtraction',
                      7: 'mkpsfScript',
                      8: 'badPSFSubtractionStarRemoval',
                      9: 'allstarScript',
                      10: 'makePlots',
                      # last function in 'Data Reduction'
                      11: 'alsedt'}

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
    setDirectory = raw_input(question1)

    while not os.path.isdir(setDirectory):
        print 'Invalid path, try again.'
        setDirectory = raw_input(question1)

    if setDirectory[-1] != '/':
        setDirectory += '/'

    question2 = 'Enter the frame you want to work on (ex: n21158): '
    frame = raw_input(question2)
    while not os.path.isdir(setDirectory + frame):
        print 'Invalid frame selection for ' + setDirectory + frame + ', try again.'
        frame = raw_input(question2)

    return setDirectory, frame


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


def optFilesExist(setDirectory, frame):
    '''Returns true if all options files are in place. Should be called before each function is executed'''
    import OptionFiles

    pathToFile = setDirectory + frame + '/'
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


def setupOptFiles(setDirectory, frame):
    '''Sets up the option files'''
    print '\nChecking to see if option files exist...\n'
    import OptionFiles

    opt = OptionFiles(frameFWHM, setDirectory, frame)

    for fileName in opt.optionFileDict:
        pathToFile = setDirectory + frame + '/' + fileName
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

    return


def getFWHM():

    return 3.01


def psfFirstPass():

    return


def psfCandidateSelection():

    return


###
# Ask the user for the directories they want to use
###
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
        frameFWHM = getFWHM()
        break


###
# Check to see if all of the files we are about to use exist
#   If they don't, ask the user to place them in the directory,
#   or offer to copy them from this program. Store them in another
#   file as heredoc strings to prevent strange formatting problems
###

optFilesSetup = optFilesExist(dataSetDirectory, currentFrame)
while True:
    if not optFilesSetup:
        user_selection = raw_input(
            "Option files don't seem to exist in this directory. Do you want to set them up?")
        if user_selection not in ['Y', 'y', 'N', 'n']:
            print 'Invalid response'
            continue
        else:
            if user_selection in ['n', 'N']:
                break
            else:
                setupOptFiles(dataSetDirectory, currentFrame)
                if not optFilesExist(dataSetDirectory, currentFrame):
                    print 'I tried setting them up, but they still don\'t appear to exist. Something is wrong.'
                    continue
                else:
                    break

while True:
    try:
        user_selection = raw_input('What do you want to do? ')
        int(user_selection)
    except ValueError:
        if user_selection == 'q' or user_selection == 'Q':
            print 'Goodbye.'
            break
        else:
            print 'Please enter a valid selection'
            continue

    user_selection = int(user_selection)
    print 'Integer entered. We can pick a function now'
    ###
    # Get the FWHM from the current frame.
    #   Try to see if I can get into the daophot window from this program
    #   and if so, can I find out when the user is done? If not, provide
    #   a single line of code they can
    ###
    getFWHM()

    ###
    # PSF Fitting, First Pass (2)
    ###
    psfFirstPass()

    ###
    # PSF Candidate Selection (3)
    ###
    psfCandidateSelection()

    ###
    #
