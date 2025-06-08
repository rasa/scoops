"""
Copied from: rasa/dotfiles/.github/scripts/debug-vars.py
EDIT THE ABOVE FILE, NOT THIS COPY, OR YOUR CHANGES WILL BE LOST!
"""

import os
import pprint
import sys
print("os.name=", os.name)
print("sys.executable=", sys.executable)
print("sys.argv=")
pprint.pprint(sys.argv)
print("sys.version=", sys.version)
print("sys.platform=", sys.platform)
print("os.environ=")
pprint.pprint(dict(os.environ), width=4096)
sys.exit(0)
