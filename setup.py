import os
import shutil
import numpy as np
from os.path import join as pjoin

from distutils.core import setup, Command
from distutils.extension import Extension
from Cython.Distutils import build_ext

extensions = [
    Extension(
        "numpush.posix_io.iothread",
        ["numpush/posix_io/iothread.pyx"],
        include_dirs=[],
    ),
    Extension(
        "numpush.posix_io.splice",
        ["numpush/posix_io/splice.pyx"],
        include_dirs=[],
    ),
    Extension(
        "numpush.posix_io.sendfile",
        ["numpush/posix_io/sendfile.pyx"],
        include_dirs=[],
    ),
    Extension("numpush.moose_store.moose",
        ["numpush/moose_store/moose.pyx"],
        include_dirs=[],
    ),
]

def find_packages():
    packages = []
    for dir,subdirs,files in os.walk('numpush'):
        package = dir.replace(os.path.sep, '.')
        if '__init__.py' not in files:
            # not a package
            continue
        packages.append(package)
    return packages

# Adapted from the pyzmq setup.py realeased under the BSD.

class CleanCommand(Command):
    """Custom distutils command to clean the .so and .pyc files."""

    user_options = [ ]

    def initialize_options(self):
        self._clean_me = []
        self._clean_trees = []
        for root, dirs, files in list(os.walk('numpush')):
            for f in files:
                if os.path.splitext(f)[-1] in ('.pyc', '.so', '.o', '.pyd'):
                    self._clean_me.append(pjoin(root, f))
            for d in dirs:
                if d == '__pycache__':
                    self._clean_trees.append(pjoin(root, d))

        for d in ('build',):
            if os.path.exists(d):
                self._clean_trees.append(d)

    def finalize_options(self):
        pass

    def run(self):
        for clean_me in self._clean_me:
            try:
                os.unlink(clean_me)
            except Exception:
                pass
        for clean_tree in self._clean_trees:
            try:
                shutil.rmtree(clean_tree)
            except Exception:
                pass

#-----------------------------------------------------------------------------
# Main setup
#-----------------------------------------------------------------------------

long_desc = \
"""
"""

setup(
    name = "numpush",
    version = '0.0.1dev',
    packages = find_packages(),
    ext_modules = extensions,
    package_data = {},
    author = "Stephen Diehl",
    author_email = "stephen.m.diehl@gmail.com",
    url = 'http://github.com/sdiehl/numpush',
    download_url = 'http://github.com/sdiehl/numpush/downloads',
    description = "Distributed data/code push for Numpy derivative structures",
    long_description = long_desc,
    license = "MIT",
    cmdclass = {'build_ext': build_ext, 'clean': CleanCommand},
    classifiers = [
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Operating System :: POSIX',
        'Topic :: System :: Networking',
        'Programming Language :: Python :: 2.7',
    ]
)
