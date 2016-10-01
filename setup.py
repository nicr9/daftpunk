from setuptools import setup
from dp2 import VERSION

setup(
        name='daftpunk',
        version=VERSION,
        description='Scrape & process data from daft.ie',
        author='Nic Roland',
        author_email='nicroland9@gmail.com',
        url = 'https://github.com/nicr9/daftpunk',
        download_url = 'https://github.com/nicr9/daftpunk/tarball/%s' % VERSION,
        packages=['dp2'],
        install_requires=[
            'requests',
            'beautifulsoup4',
            'redis',
            ],
        license='MIT',
        )
