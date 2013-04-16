from setuptools import setup

setup(
    name='slice',
    version='1.0',
    description='Utility for managing rss feeds',
    author='Joel Kleier',
    author_email='joel@kleier.us',
    url='http://joelkleier.com',
    packages=[],
    install_requires=[
        'django',
        'feedparser',
        'lxml',
        'opml',
        'python-dateutil',
        'pytz',
        'sqlalchemy',
    ],
    scripts = [
    ],
)

