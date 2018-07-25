import subprocess
import tempfile
import json
import re

from libs.utils import *

class DomainManager:
    """Runs and manage domain processes"""

    def __init__(self, config, dirpath, servers_config, domain_settings, test, verbose):
        self.config = config
        self.dirpath = dirpath
        self.servers_config = servers_config
        self.domain_settings = domain_settings
        self.test = test
        self.verbose = verbose

        self.domain_settings_file = None

        self.domain_command = None
        self.default_acs_commands = []
        self.test_acs_commands = []
        self.test_interfaces_commands = []

        self.domain = None
        self.default_acs = []
        self.test_acs = []
        self.test_interfaces = []

    def buildDomainCommands(self):
        scripts = self.domain_settings.setdefault("scripts", {}).setdefault("persistent_scripts", [])
        test_agents = self.test.get("agents", [])
        test_interfaces = self.test.get("interfaces", [])

        num_default_agents = len(scripts)
        num_test_agents = len(test_agents)

        for script in scripts:
            script["pool"] = "default-agent"

        # Generate DS Settings
        for scriptPath in test_agents:
            scripts.append({
                "num_instances": "1",
                "pool": "test-agent",
                "url": os.path.join(self.dirpath, scriptPath)
            })

        # Write DS Settings to a temp file
        self.domain_settings_file = tempfile.NamedTemporaryFile(mode='wt', prefix='domain-settings-')
        settings = json.dumps(self.domain_settings)
        self.domain_settings_file.write(settings)
        self.domain_settings_file.flush()

        # Build DS command
        self.domain_command = [
            self.config["domain-server"],
            "--user-config={}".format(self.domain_settings_file.name),
            "--parent-pid={}".format(os.getpid())
        ]
        domain_args = self.servers_config.get("domain", {}).get("args", "")
        self.domain_command += filter(None, domain_args.split(" ")) # Split args and remove empty ones

        # Build default ACs commands
        for ac_type in self.servers_config.get("assignment-types", []):
            self.default_acs_commands.append([
                self.config["assignment-client"],
                "-t{}".format(ac_type),
                "--parent-pid={}".format(os.getpid())
            ])

        # Build default agents commands
        for _ in range(num_default_agents):
            self.default_acs_commands.append([
                self.config["assignment-client"],
                "-t2",
                "--pool=default-agent",
                "--parent-pid={}".format(os.getpid())
            ])

        # Build test agents commands
        for _ in range(num_test_agents):
            self.test_acs_commands.append([
                self.config["assignment-client"],
                "-t2",
                "--pool=test-agent",
                "--parent-pid={}".format(os.getpid())
            ])

        # Build test interfaces commands
        for config in test_interfaces:
            command = [
                self.config["interface"],
                "--suppress-settings-reset",
                "--no-updater",
                "--allowMultipleInstances"
            ]
            if "script" in config:
                command += [
                    "--testScript",
                    os.path.join(self.dirpath, config["script"])
                ]
            if "args" in config:
                command += filter(None, config["args"].split(" "))
            self.test_interfaces_commands.append(command)


        if self.verbose >= 2:
            print("Domain command: {}".format(self.domain_command))
            print("Default ACs commands: {}".format(self.default_acs_commands))
            print("Test ACs commands: {}".format(self.test_acs_commands))
            print("Test Interfaces commands: {}".format(self.test_interfaces_commands))

    def runDomain(self):
        QT_LOGGING_RULES = "*=false;hifi.tools.stack-test=true"
        if self.verbose >= 3:
            QT_LOGGING_RULES = ""


        self.domain = subprocess.Popen(
            self.domain_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={"QT_LOGGING_RULES": QT_LOGGING_RULES},
            text=True
        )

        for command in self.default_acs_commands:
            self.default_acs.append(subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={"QT_LOGGING_RULES": QT_LOGGING_RULES},
                text=True
            ))

        for command in self.test_acs_commands:
            self.test_acs.append(subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={"QT_LOGGING_RULES": QT_LOGGING_RULES},
                text=True
            ))

        for command in self.test_interfaces_commands:
            self.test_interfaces.append(subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={"QT_LOGGING_RULES": QT_LOGGING_RULES},
                text=True
            ))


        pass_re = "^.*\[INFO\] \[hifi.tools.stack-test\](.*) PASS(.*)$"
        failed_re = "^.*\[INFO\] \[hifi.tools.stack-test\](.*) FAIL(.*)$"
        completed_re = "^.*\[INFO\] \[hifi.tools.stack-test\](.*) COMPLETE(.*)$"

        for proc in self.test_acs + self.test_interfaces:
            try:
                stdoutdata, stderrdata = proc.communicate(timeout=90)
                lines = stdoutdata.splitlines()

                if self.verbose >= 2:
                    print(stdoutdata)

                test_passed = False
                test_failed = False
                test_failed_message = ""
                test_completed = False
                test_completed_message = ""

                for line in lines:
                    pass_match = re.match(pass_re, line)
                    fail_match = re.match(failed_re, line)
                    complete_match = re.match(completed_re, line)

                    if pass_match:
                        test_passed = True
                        message = pass_match.group(2).strip()
                        if self.verbose:
                            passed(message, "  ")
                    elif fail_match:
                        test_failed = True
                        test_failed_message = fail_match.group(2).strip()
                        if self.verbose:
                            failed(test_failed_message, "  ")
                    elif complete_match:
                        test_completed = True
                        test_completed_message = complete_match.group(2).strip()


                if not test_completed:
                    if proc.returncode != 0:
                        failed("{} - Process crashed with exit code {}".format(self.test['title'], proc.returncode))
                    else:
                        failed("{} - Test did not complete".format(self.test['title']))
                elif test_failed:
                    failed("{} - {}".format(self.test['title'], test_failed_message))
                elif test_passed:
                    passed("{} - {}".format(self.test['title'], test_completed_message))
                else:
                    failed("{} - No PASS/FAIL messages".format(self.test['title']))


            except subprocess.TimeoutExpired:
                proc.kill()
                failed("{} - timeout".format(self.test['title']))
            except Exception as err:
                proc.kill()
                failed("{} - unknown exception {}".format(self.test['title'], err))

        self.domain.kill()
        if self.verbose >= 4:
            stdoutdata, stderrdata = self.domain.communicate()
            self.domain.wait()
            print(self.domain.args)
            print(stdoutdata)
        for proc in self.default_acs:
            proc.kill()
            if self.verbose >= 4:
                stdoutdata, stderrdata = proc.communicate()
                print(proc.args)
                print(stdoutdata)
