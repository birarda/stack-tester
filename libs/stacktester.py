import os
import sys
import subprocess
import json
import pathlib
from functools import *

from libs.domainmanager import DomainManager
from libs.jsonstack import JSONStack
from libs.utils import *

CONFIG_FILENAME = 'config.json'
TEST_BASE_FILENAME = 'test-base.json'
TEST_FILENAME = 'test.json'
SERVERS_FILENAME = 'servers.json'
DOMAIN_SETTINGS_FILENAME = 'domain-settings.json'

class StackTester:
    """Automated Stack Testing Tool"""
    def __init__(self, root_dir, args):
        self.root_dir = root_dir
        self.args = args
        self.config_file = os.path.join(root_dir, CONFIG_FILENAME)
        self.tests = list(map(lambda x: os.path.join(root_dir, x), args.tests))

        self.test_stack = JSONStack()
        self.servers_stack = JSONStack()
        self.domain_settings_stack = JSONStack()

    def process_config_file(self):
        config_file_exists = os.path.isfile(self.config_file)
        config_object = {}
        if (config_file_exists):
            try:
                with open(self.config_file, "rt") as file:
                    config_object = json.loads(file.read())
                    file.close()
            except Exception as err:
                print("Failed to process config file: {}".format(err))
                sys.exit()


        if (self.args.domain_server_path):
            config_object['domain-server'] = self.args.domain_server_path
        if (self.args.assignment_client_path):
            config_object['assignment-client'] = self.args.assignment_client_path
        if (self.args.interface_path):
            config_object['interface'] = self.args.interface_path

        try:
            self.config = {
                "domain-server": config_object['domain-server'],
                "assignment-client": config_object['assignment-client'],
                "interface": config_object['interface']
            }
        except Exception as err:
            if config_file_exists:
                print("Config file missing some values: {}".format(err))
            else:
                print("Arguments missing some paths: {}".format(err))
            sys.exit()

        try:
            open_mode =  "wt" if config_file_exists else "xt"
            with open(self.config_file, open_mode) as file:
                file.write(json.dumps(config_object))
                file.close()
        except Exception as err:
            print("Failed to process config file: {}".format(err))
            sys.exit()

    def check_binaries(self):
        check_binary('domain-server', self.config['domain-server'], self.args.verbose)
        check_binary('assignment-client', self.config['assignment-client'], self.args.verbose)
        check_binary('Interface', self.config['interface'], self.args.verbose)

    def recurseTests(self, current_dir=None):
        if current_dir == None:
            current_dir = self.root_dir

        for dirpath, dirnames, filenames in os.walk(current_dir):

            test_base_file = os.path.join(dirpath, TEST_BASE_FILENAME)
            self.test_stack.push(getJSONFromFile(test_base_file))

            servers_file = os.path.join(dirpath, SERVERS_FILENAME)
            self.servers_stack.push(getJSONFromFile(servers_file))

            domain_settings_file = os.path.join(dirpath, DOMAIN_SETTINGS_FILENAME)
            self.domain_settings_stack.push(getJSONFromFile(domain_settings_file))

            test_file = os.path.join(dirpath, TEST_FILENAME)
            valid = not len(self.tests) or reduce((lambda x, y: x or y),
                    map(lambda x: pathlib.PosixPath(x) in list(pathlib.Path(test_file).parents), self.tests))

            if os.path.isfile(test_file) and valid:
                print("Runing: {}".format(os.path.relpath(current_dir, self.root_dir)))

                self.test_stack.push(getJSONFromFile(test_file))
                self.runTest(dirpath)
                self.test_stack.pop()


            for dir in dirnames:
                self.recurseTests(os.path.join(current_dir, dir))

            self.test_stack.pop();
            self.servers_stack.pop();
            self.domain_settings_stack.pop();

            break # We only want walk to recurse the top level directory

    def runTest(self, dirpath):
        test_object = self.test_stack.top()
        if 'title' not in test_object:
            failed('Test has no title')
            return

        domain = DomainManager(
            self.config,
            dirpath,
            self.servers_stack.top(),
            self.domain_settings_stack.top(),
            self.test_stack.top(),
            self.args.verbose
        )

        domain.buildDomainCommands()
        domain.runDomain()
