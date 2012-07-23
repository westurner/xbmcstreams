try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import os
__VERSION__="0.0.2"

def read_readme():
    README=open(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'README.rst')).read()

REQUIRES=(
    'mechanize',
    'BeautifulSoup',
)

setup(
    author='Wes Turner',
    author_email='wes@wrd.nu',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Multimedia :: Sound/Audio :: Players',
    ],
    description='A commandline interface to the XBMC RPC API',
    license='GPLv2',
    long_description=read_readme(),
    name='xbmcstreams',
    provides=['xbmcstreams'],
    py_modules=['xbmcstreams'],
    install_requires=REQUIRES,
    url='http://bitbucket.org/westurner/xbmcstreams',
    version=__VERSION__,
    entry_points={
        'console_scripts':[
            'xbmcstreams = xbmcstreams:main',
        ]
    }
)
