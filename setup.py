import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'setuptools',
    'pyramid',
    'SQLAlchemy',
    'transaction',
    'repoze.tm2>=1.0b1', # default_commit_veto
    'zope.sqlalchemy',
    'WebError',
    'pyramid_simpleform',
    'pyramid_jinja2',
    'Jinja2',
    'cryptacular',
    ]

if sys.version_info[:3] < (2,5,0):
    requires.append('pysqlite')

setup(name='flow',
      version='0.1',
      description='',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Framework :: Pylons",
        "Framework :: BFG",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='flow.tests',
      install_requires = requires,
      entry_points = """\
      [paste.app_factory]
      main = flow:main
      """,
      paster_plugins=['pyramid'],
      )

