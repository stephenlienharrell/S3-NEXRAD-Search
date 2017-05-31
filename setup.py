from setuptools import setup

setup(name='s3_nexrad_search',
      version='1.1',
      description="Command line utility and Python library to search the NEXRAD Level II dataset hosted in Amazon's S3",
      url='https://github.com/stephenlienharrell/S3-NEXRAD-Search',
      download_url = 'https://github.com/stephenlienharrell/S3-NEXRAD-Search/archive/1.1.tar.gz',
      author='Stephen Lien Harrell',
      author_email='stephen@teknikal.org',
      license='MIT',
      install_requires=['matplotlib', 'numpy', 'boto', 'utm'],
      packages=['s3_nexrad_search'],
      keywords = ['radar', 'NEXRAD', 'AWS', 'S3', 'longitude', 'latitude'],
      classifiers=[
          'Programming Language :: Python :: 2.7',
      ],
      scripts=['scripts/nexrad_get'],
      zip_safe=False)
