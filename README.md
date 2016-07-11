# yamlcf
Plain YAML, plain CloudFormation command line client. Based on boto3.

What is the difference to the existing ```aws cloudformation [...]``` tool?

 - YAML support. Json is also supported of course.
 - Optimized for commandline usage and coontinous integration tools like jenkins:
    - Easy to see progress: Live log output.
    - Easy to script: Waits for success or fails on error.
 - Convention-over-configuration: If you name your cloudformation file ```mystack.cf.yaml``` then yamlcf uses by default
  ```mystack``` as stackname.


What is the difference to e.g. terraform? yamlcf does not extend CloudFormation, it is just a tool for easier usage.
There is no additional syntax.

## Usage

You need python 3 and install via pip:
```
sudo pip install yamlcf
```

## Feedback, Questions, Comments
Open an [issue](https://github.com/komoot/yamlcf/issues) or [ask on stackoverflow](https://stackoverflow.com/questions/ask?tags=yamlcf). Relases are listed [on pypi](https://pypi.python.org/pypi/yamlcf/0.2)





