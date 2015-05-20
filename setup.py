from distutils.core import setup

VERSION = 'v0.1'

setup(
        name='daftpunk',
        version=VERSION,
        description='Scrape & process data from daft.ie',
        author='Nic Roland',
        author_email='nicroland9@gmail.com',
        packages=['daftpunk'],
        scripts = ['bin/daftpunk'],
        install_requires=[
            'pika',
            ],
        license='MIT',
        )
