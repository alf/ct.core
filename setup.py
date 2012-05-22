from distutils.core import setup

setup(name='ct.core',
      version='0.4',
      packages=['ct', 'ct.core'],
      data_files=[
        ('share/ct', ['config.ini.sample']),
      ],
      install_requires=['lxml'],
      package_dir={'': 'src'},
)
