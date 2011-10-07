from distutils.core import setup

setup(name='ct',
      version='0.4',
      packages=['ct'],
      data_files=[
        ('share/ct', ['config.ini.sample']),
      ],
      install_requires=['lxml'],
      package_dir = {'': 'src'},
)
