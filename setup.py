from setuptools import setup, find_packages

setup(
        install_requires=[
            'lxml==2.3.4',
            'PyYAML==3.10',
            'MySQL-python==1.2.4',
            'distribute==0.6.45',
            'nose==1.3.0',
            'mock==1.0.1',
            'testfixtures==3.0.1',
            'wsgiref==0.1.2',
            'pyparsing==1.5.6',
            'freshen==0.2',
            'beautifulsoup4==4.2.1',
            ],
        name='slingshot',
        version='0.2',
        packages=find_packages(),
        entry_points={
          'console_scripts': [
              'slingshot = slingshot.core.slingshot:main',
              'init_db = slingshot.db.initialise_database:main',
              'evaluate_results = slingshot.util.evaluate_results:main',
              'calc = slingshot.util.calc_number_of_tcs:main',
              'compare_res = slingshot.util.compare:main',
              'analyze_compile = slingshot.util.analyze_compile:main',
              'mul = slingshot.util.multi_version_comparison:main',
              ]},
        include_package_data=True
)
