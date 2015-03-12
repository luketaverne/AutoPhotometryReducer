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

# top level working directory, with trailing slash. Like
# '/data/n2158_phot/n2158/'
workingDirectory = ''
currentFrame = ''     # current frame. Like 'n21157'
frameFWHM = None   # will hold the FWHM later
optFilesSetup = False  # true if setup has been completed successfully

functionDictionary = {0: 'setupDirectories',
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
                         11: 'alsedt',
                      }

externalProgramDict = {'daophot': ['daophot.e', True], # {functionName : [computerFunctionName, exists?]}
                       'compapcorr': ['compapcorrHDI.e', True],
                       'pyraf' : ['pyraf', True],
                       'ds9' : ['ds9', True],
                       'dao2iraf' : ['dao2iraf.e', True],
                       'sm' : ['sm', True],
                       'pstopdf' : ['pstopdf', True],
                       'alsedt' : ['alsedt.e', True],
                       'sigrejfit' : ['sigrejfit.e', True],
                       'poly' : ['poly.e', True],
                       'apply_apcorr' : ['apply_apcorrHDI.e', True]}


def setupDirectories():
  '''Set up the variables for the working folder and directories. Option 0.'''
  while True:
    try:
      workingDirectory = raw_input(
          'Enter the current working directory (ex: /data/n2158_phot/n2158/): ')
      subprocess.call('cd ' + workingDirectory, shell=True)
    except ValueError, OSError:  # This isn't catching the error
      print("Unable to cd into that directory. Try again")
      continue
    else:
      # input was okay,
      break

  while True:
    try:
      currentFrame = raw_input(
          'Enter the frame you want to work on (ex: n21158)')
      subprocess.call('cd ' + workingDirectory + currentFrame, shell=True)
    # This isn't catching the invalid directory error
    except ValueError, OSError:
      print("Unable to cd into that directory. Try again")
      continue
    else:
      # input was okay,
      break

  return

def checkFunctionsExist():
    for programKey in externalProgramDict:
        exists = HelperFunctions.which(externalProgramDict[programKey][0])
        if not exists:
            externalProgramDict[programKey][1] = False
            print "Cannot execute program " + programKey + " called as '" + externalProgramDict[programKey][0] +"'"

    return None

def optionFilesExist():
  '''Returns true if all options files are in place. Should be called before each function is executed'''

  return


def getFWHM():

  return


def setupOptFiles():

  return


def psfFirstPass():

  return


def psfCandidateSelection():

  return


###
# Ask the user for the directories they want to use
###
# setupDirectories()

###
# Check to see if all of the files we are about to use exist
#   If they don't, ask the user to place them in the directory,
#   or offer to copy them from this program. Store them in another
#   file as heredoc strings to prevent strange formatting problems
###
optionFilesExist()
checkFunctionsExist()
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
  print('Integer entered. We can pick a function now')
  ###
  # Get the FWHM from the current frame.
  #   Try to see if I can get into the daophot window from this program
  #   and if so, can I find out when the user is done? If not, provide
  #   a single line of code they can
  ###
  getFWHM()

  ###
  # Edit the option files: (1)
  #   I think it's actually a good idea to print them from heredocs
  #   stored in another file. Then I can avoid dealing with someone
  #   inserting incorrect spacings
  ###
  setupOptFiles()

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
