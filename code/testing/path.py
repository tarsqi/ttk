
import os
import sys

# make sure we are in the main tarsqi directory
script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)
os.chdir('..')
sys.path.insert(0, os.getcwd())
