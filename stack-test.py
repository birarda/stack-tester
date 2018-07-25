#!/usr/bin/env python3

import os
import sys
import argparse

from libs.stacktester import StackTester

def process_arguments():
    parser = argparse.ArgumentParser(description='High Fidelity\'s Automated Stack Testing Tool.')
    parser.add_argument('--verbose', '-v', action='count', help='Prints a verbose output')
    parser.add_argument('--ds', metavar='<path>', help='Path to DS binary', dest='domain_server_path')
    parser.add_argument('--ac', metavar='<path>', help='Path to AC binary', dest='assignment_client_path')
    parser.add_argument('--interface', metavar='<path>', help='Path to Interface binary', dest='interface_path')
    parser.add_argument('tests', metavar='test', nargs='*', help='Test(s) path.')
    return parser.parse_args()

def main():
    if sys.version_info[0] < 3:
        raise Exception("Must be using Python 3")

    # Process arguments
    args = process_arguments()
    if (args.verbose):
        print("Passed args: {}".format(args))
    else:
        args.verbose = 0

    # Get root directory path
    root_dir = os.path.abspath(os.getcwd())
    if (args.verbose):
        print("Root dir = {}".format(root_dir))

    # Setup Stack Tester
    stackTester = StackTester(root_dir, args)
    stackTester.process_config_file()
    stackTester.check_binaries()

    if args.interface_path or args.domain_server_path or args.assignment_client_path:
        print("stack-test was successfully configured")
        return

    # Run tests
    stackTester.recurseTests()

if __name__ == "__main__":
    main()
