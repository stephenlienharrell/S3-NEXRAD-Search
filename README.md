# S3 NEXRAD Search
This python library searches the NEXRAD dataset based on a lat/lon domain and
time range. It returns relevant files within the dataset with the option to
download them. 

Relevant function definitions and doc strings:

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
