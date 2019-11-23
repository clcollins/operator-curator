from setuptools import setup

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='operator-curator',
    packages=['operatorcurator'],
    version='2.0',
    description='Curate operators for use with OpenShift Dedicated',
    author='OpenShift SD SRE',
    url='https://github.com/openshift/operator-curator',
    entry_points={
        'console_scripts': [
            'operator-curator=operatorcurator.cli:main'
        ],
    },
    keywords=['operator', 'curator'],
    install_requires=[
        'pyyaml',
        'requests'
    ],
    python_requires='>=3.6, <4',
    tests_require=['unittest','pylint'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    zip_safe=False
)
