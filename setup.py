from distutils.core import setup

setup(name='mechcrawler',
    version='0.1',
    license='BSD',
    description="Subclasses of mechanize's Browser with added crawling and testing functionality",
    author='Kenji Wellman',
    author_email='kenji.wellman@interstellr.com',
    url='http://interstellr.com/',
    requires=['mechanize'],
    packages=['mechcrawler'],
)
