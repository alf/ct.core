from distutils.core import setup

setup(name='ct',
      version='0.1pre',
      scripts=['scripts/list_projects.py', 'scripts/list_hours.py'],
      packages=['ct'],
      install_requires=['lxml'],
      package_dir = {'': 'src'},
)
