# S3 NEXRAD Search
This command line tool and python library searches the NEXRAD dataset based on a lat/lon domain and
time range. It returns relevant files within the dataset with the option to
download them. 

## Command Line Interface

Usage:

    nexrad_get [-h] [-v] [-r] [-o DOWNLOAD_DIR] -w MAXLAT -a MAXLON -s
                   MINLAT -d MINLON -t STARTTIME -e ENDTIME

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         Print non-error output [DEFAULT: False]
      -r, --dryrun          List files only, implies -v
      -o DOWNLOAD_DIR, --download_dir DOWNLOAD_DIR
                            Directory for temporary downloads
      -w MAXLAT, --maxlat MAXLAT
                            Maximum latitude of search domain
      -a MAXLON, --maxlon MAXLON
                            Maximum longitude of search domain
      -s MINLAT, --minlat MINLAT
                            Minimum latitude of search domain
      -d MINLON, --minlon MINLON
                           Minimum longitude of search domain
      -t STARTTIME, --starttime STARTTIME
                            Start of time range with format %Y-%m-%dT%H:%M:%S ex.
                            2015-05-05T10:15:00
      -e ENDTIME, --endtime ENDTIME
                            End of time range with format %Y-%m-%dT%H:%M:%S ex.
                            2015-05-05T10:15:00

Example Usage:

    $ nexrad_get --starttime 2015-05-05T15:05:00 --endtime 2015-05-05T15:20:00 --maxlat 41.22 --maxlon "-84.79" --minlat 38.22 --minlon "-87.79" -o temp -v -p 20
    Found stations: KIWX,KIND,KILN,KVWX,KLVX for domain 41.22,-84.79 to 38.22,-87.79
    Found files for time range: 2015-05-05 15:05:00 to 2015-05-05 15:20:00
    2015/05/05/KIWX/KIWX20150505_150845_V06.gz
    2015/05/05/KIWX/KIWX20150505_151253_V06.gz
    2015/05/05/KIWX/KIWX20150505_151702_V06.gz
    2015/05/05/KIND/KIND20150505_150723_V06.gz
    2015/05/05/KIND/KIND20150505_151126_V06.gz
    2015/05/05/KIND/KIND20150505_151527_V06.gz
    2015/05/05/KIND/KIND20150505_151930_V06.gz
    2015/05/05/KILN/KILN20150505_150819_V06.gz
    2015/05/05/KILN/KILN20150505_151202_V06.gz
    2015/05/05/KILN/KILN20150505_151543_V06.gz
    2015/05/05/KILN/KILN20150505_151925_V06.gz
    2015/05/05/KVWX/KVWX20150505_150812_V06.gz
    2015/05/05/KVWX/KVWX20150505_151758_V06.gz
    2015/05/05/KLVX/KLVX20150505_151148_V06.gz
    temp/KVWX20150505_150812_V06.gz downloaded
    temp/KLVX20150505_151148_V06.gz downloaded
    temp/KILN20150505_150819_V06.gz downloaded
    temp/KIND20150505_151527_V06.gz downloaded
    temp/KVWX20150505_151758_V06.gz downloaded
    temp/KIWX20150505_150845_V06.gz downloaded
    temp/KILN20150505_151202_V06.gz downloaded
    temp/KILN20150505_151925_V06.gz downloaded
    temp/KILN20150505_151543_V06.gz downloaded
    temp/KIND20150505_151126_V06.gz downloaded
    temp/KIND20150505_151930_V06.gz downloaded
    temp/KIND20150505_150723_V06.gz downloaded
    temp/KIWX20150505_151253_V06.gz downloaded
    temp/KIWX20150505_151702_V06.gz downloaded


## Python Library

Relevant function definitions and doc strings from class S3NEXRADHelper:

    def __init__(self, verbose=True, threads=1):
        """Initalizes variables for this class

        verbose: Boolean of if we should print non-error information
        threads: The amount of threads to use for downloading from S3
        """
        self.s3conn = boto.connect_s3(anon=True)
        self.bucket = self.s3conn.get_bucket("noaa-nexrad-level2")
        self.verbose = verbose
        self.thread_max = threads
        self.threads = []
        self.thread_count = 0

    def findNEXRADKeysByTimeAndDomain(self, start_datetime, end_datetime,
            maxlat, maxlon, minlat, minlon):
        """Get list of keys to nexrad files on s3 from a time range and 
        lat/lon domain.

        start_datetime: start of time range in a datetime.datetime object
        end_datetime: end of time range in a datetime.datetime object
        maxlat: maximum latitude of domain
        maxlon: maximum longitude of domain
        minlat: minimum lattitude of domain
        minlon: minimum longitude of domain

        returns: List of keys in nexrad s3 bucket corespopnding to the
        parameters
        """

    def downloadNEXRADFiles(self, download_dir, s3keys):
        """Download files from S3 NEXRAD bucket

        download_dir: The directory to download the file to
        s3keys: list of keys in the nexrad bucket to download

        returns: list of downloaded file paths
        """
        
    def getStationsFromDomain(self, maxlat, maxlon, minlat, minlon):
        """Searches station list for radar stations that would be relevant
        to the domain provided.

        maxlat: maximum latitude of domain
        maxlon: maximum longitude of domain
        minlat: minimum lattitude of domain
        minlon: minimum longitude of domain
        """        
        
    def searchNEXRADS3(self, start_datetime, end_datetime, station_list):
        """Find available files from a date range and a station list

        start_datetime: start of time range in a datetime.datetime object
        end_datetime: end of time range in a datetime.datetime object
        station_list: list of station ids as strings ex. ["KIND", "KVBX"]

        returns: list of keys in the nexrad s3 bucket within the time 
        range for the specified stations
        """        

Example usage:
    
    from s3_nexrad_search import S3NEXRADHelper
    
    nexrad = S3NEXRADHelper()
    s3keys = nexrad.findNEXRADKeysByTimeAndDomain(
            datetime.datetime(day=5, month=5, year=2015, hour=5),
            datetime.datetime(day=5, month=5, year=2015, hour=6),
            41.22, -84.79, 38.22, -87.79)
    nexrad.downloadNEXRADFiles('temp', s3keys)
