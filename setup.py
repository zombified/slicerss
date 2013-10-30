from setuptools import setup

setup(
    name='slice',
    version='0.0.1',
    description='Utility for managing rss feeds',
    author='Joel Kleier',
    author_email='joel@kleier.us',
    url='http://joelkleier.com',
    packages=[],
    install_requires=[
        'beautifulsoup4',
        'docopt',
        'django',
        'feedparser',
        'lxml',
        'opml',
        'python-dateutil',
        'pytz',
        'requests',
        'sqlalchemy',
    ],
    scripts = [
    ],
)

