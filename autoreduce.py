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
                         11: 'alsedt',
                      }

externalProgramDict = {'daophot': ['daophot', True], # {functionName : [computerFunctionName, exists?]}
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

def checkFunctionsExist():
    '''Loop through function dictionary to check if all functions are callable'''
    print '\nChecking function dictionary to make sure all functions are callable before we start reduction...'
    problem = False
    for programKey in externalProgramDict:
        exists = HelperFunctions.which(externalProgramDict[programKey][0])
        if not exists:
            externalProgramDict[programKey][1] = False
            problem = True
            print "Cannot execute program " + programKey + " called as '" + externalProgramDict[programKey][0] +"'"
    if problem:
        print '\nThe function(s) listed above are not callable. You should fix this before proceeding.'
    else:
        print '\nAll functions are callable.'
    return None

def optionFilesExist( frameDirectory ):
  '''Returns true if all options files are in place. Should be called before each function is executed'''
  print '\nChecking to see if option files exist...\n'
  import OptionFiles

  for file in OptionFiles.optionFileDict:
      if not os.path.exists(frameDirectory + file):
          print 'Option file ' + file + ' does not exist.'
          createFile = raw_input('Do you want to create this file from a template? (y/n): ')
          while createFile not in ['Y', 'y', 'N', 'n']:
              print 'Invalid response'
              createFile = raw_input('Do you want to create this file from a template? (y/n): ')

          if createFile in ['Y', 'y']:



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
dataSetDirectory, currentFrame = getWorkingDirectories()

###
# Check to see if all of the files we are about to use exist
#   If they don't, ask the user to place them in the directory,
#   or offer to copy them from this program. Store them in another
#   file as heredoc strings to prevent strange formatting problems
###
optionFilesExist(dataSetDirectory + currentFrame + '/')
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
