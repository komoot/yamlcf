from setuptools import setup

setup(
    name='yamlcf',      # This is the name of your PyPI-package.
    version='0.3.2',      # Update the version number for new releases
    scripts=['yamlcf.py'],  # The name of your script, and also the command you'll be using for calling it
    url='https://github.com/komoot/yamlcf',
    author='Jan Heuer',
    author_email='jan@komoot.de',
    install_requires=[
        'pyyaml',
        'botocore'
    ]
)
