from distutils.core import setup
from daftpunk import VERSION

setup(
        name='daftpunk',
        version=VERSION,
        description='Scrape & process data from daft.ie',
        author='Nic Roland',
        author_email='nicroland9@gmail.com',
        packages=['daftpunk'],
        scripts = ['bin/dp_searcher', 'bin/dp_worker'],
        install_requires=[
            'pika',
            'requests',
            'beautifulsoup4',
            'redis',
            'nltk',
            ],
        license='MIT',
        )
