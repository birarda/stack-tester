import os
import sys
import subprocess
import re
import json

from termcolor import colored

def passed(message, prefix=""):
    print("{}{}   : {}".format(prefix, colored('PASS', 'green'), message))

def failed(message, prefix=""):
    print("{}{}  : {}".format(prefix, colored('FAIL!', 'red'), message))

def check_binary(binary_name, binary_path, verbose):
    try:
        output_re = '^{} [a-zA-Z0-9.]*$'

        arguments = [binary_path, '-v']
        if verbose:
            print("Checking binary {}: {}".format(binary_name, ' '.join(arguments)))
        output = subprocess.check_output(arguments, text=True)
        if not re.match(output_re.format(binary_name), output):
            print("Invalid binary output:\n{}".format(output))
            sys.exit()
    except Exception as err:
        print("Failed to check {} binary file: {}".format(binary_name, err))
        sys.exit()

def getJSONFromFile(file, default={}):
    if os.path.isfile(file):
        try:
            with open(file, 'rt') as f:
                file_json = json.loads(f.read())
                return file_json
        except Exception as err:
            print("Failed to read JSON file: {}, {}".format(err, file))
            sys.exit()
    else:
        return default
