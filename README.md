# yamlcf
Plain YAML, plain CloudFormation command line client. Based on boto3.

## Comapres to tool xy
What is the difference to the existing ```aws cloudformation [...]``` tool?

 - YAML support. Plain cloudformation json is also supported since json is also valid yaml.
 - Optimized for commandline usage and continous integration tools like jenkins:
    - Easy to see progress: Live log output.
    - Easy to use in build scripts: Waits for success and fails on error.
 - Convention-over-configuration: If you name your cloudformation file ```mystack.cf.yaml``` then yamlcf uses by default
  ```mystack``` as stackname.


What is the difference to high-level abstractions e.g. terraform? yamlcf does not extend CloudFormation or introduce a custom DSL, it is just a tool for easier usage.
You can simply rely on the given cloudformation documentation of AWS (and the AWS support).

No tool dependency: Just convert your yaml back to json and use the AWS cloud-formation tools.

## Usage

You need python 3. Install yamlcf via pip:
```
sudo pip install yamlcf
```

AWS credentials are looked up in the usual sources (environment, local config file, instance profile, ...)

## Tools that fit to yamlcf

- [aws-keychain-util](https://github.com/zwily/aws-keychain-util) puts your aws credentials in the keychain

## Feedback, Questions, Comments
Open an [issue](https://github.com/komoot/yamlcf/issues) or [ask on stackoverflow](https://stackoverflow.com/questions/ask?tags=yamlcf). Relases are listed [on pypi](https://pypi.python.org/pypi/yamlcf/0.2)





