## Description

The stack tester lets you use JSON to specify a config for the High Fidelity stack to use for your tests.


## Install

- Install python 3
- Install the necessary dependencies: `pip3 install termcolor jsonmerge`


## Usage

You need to pass the following arguments at least once, so the tools knows where to find the following binaries:
  - `domain-server`
  - `assignment-client`
  - `interface`

```
./stack-test.py --ds <ds-path> --ac <ac-path> --interface <interface-path>
```

To run all tests:
```
./stack-test.py
```

To run a group of tests:
```
./stack-test.py tests-directory
```

To run a specific tests:
```
./stack-test.py path/to/test path/to/another/test
```

Pro-tip:
`-v`, `-vv`, `-vvv`, `-vvvv` will give you increasing level of information bout the running tests


## Adding your own tests

Create a new directory for your tests where appropriate.
Test folders can be anywhere in the folder hierarchy.

- Create a `servers.json` file in that directory to specify your stack setup:
```json
{
  "domain": {
    "args": "--get-temp-name"
  },
  "assignment-types": [0, 1, 4]
}
```

- Create a `domain-settings.json` file that will be passed to the DS as its settings file.

- Create a `test.json` file that will specify what your test will do:
```json
{
  "title": "Simple Agent Script",
  "agents": ["agent-script.js", "agent-script-2.js"],
  "interfaces": [
    {
      "script": "interface-script.js",
      "args": "--url localhost"
    },
    {
      "script": "interface-script-2.js",
      "args": "--url hifi://dev-playa"
    }
  ]
}
```

- Don't forget to add your scripts to the folder as well


In that example, we would have:
```
.
+-- my-test
|   +-- servers.json
|   +-- domain-setting.json
|   +-- test.json
|   +-- agent-script.js
|   +-- agent-script-2.js
|   +-- interface-script.js
|   +-- interface-script-2.js
```

The stack tester will automatically merge `servers.json`, `domain-settings.json`, `test.json` with similar files found higher in the hierarchy (resp. `servers.json`, `domain-settings.json` and `test_base.json`)
This lets you create global configs for a suite of tests that you can then slightly tweak on a per test basis.
