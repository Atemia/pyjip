from distribute_setup import use_setuptools
use_setuptools()
from setuptools import setup, Extension


with open('README.rst') as rf:
    readme = rf.read()

dispatcher_ext = Extension('jip.dispatcher',
                           ['jip/dispatcher/jip_binding.c',
                            'jip/dispatcher/jip_dispatcher.c'])

setup(
    name='pyjip',
    version="0.3",
    description='JIP pipeline library',
    author_email='thasso.griebel@gmail.com',
    url='',
    license="BSD",
    long_description=readme,
    packages=['jip', 'jip.cli', 'jip.vendor', 'jip.scripts'],
    package_data={
        'jip.scripts': ['*.jip']
    },
    install_requires=["sqlalchemy==0.8.2",
                      "jinja2==2.7",
                      "argparse"
                      ],
    ext_modules=[dispatcher_ext],
    entry_points={
        "console_scripts": [
            'jip = jip.cli.jip_main:main'
        ]
    }
)
