from distutils.core import setup

setup(
        name='daftpunk',
        version='v0.1',
        description='Scrape data from daft.ie',
        author='Nic Roland',
        author_email='nicroland9@gmail.com',
        packages=['daftpunk'],
        scripts = ['bin/daftpunk'],
        long_description=open('README.md').read(),
        )
