from distutils.core import setup

setup(name='ct',
      version='0.3pre',
      scripts=['scripts/list_projects.py', 'scripts/list_hours.py'],
      packages=['ct'],
      data_files=[
        ('share/ct', ['config.ini.sample']),
      ],
      install_requires=['lxml'],
      package_dir = {'': 'src'},
)
