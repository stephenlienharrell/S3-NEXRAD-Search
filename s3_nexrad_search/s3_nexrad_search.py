import datetime
import math
import multiprocessing
import os
import time

import boto
import matplotlib
import numpy
import trianglesolver
import utm

__author__ = "Stephen Lien Harrell <stephen@teknikal.org>"
# also sharrell@purdue.edu

# From https://en.wikipedia.org/wiki/NEXRAD
# "The deployment of the dual polarization capability (Build 12) to NEXRAD sites began in 2010 and was completed by the summer of 2013."
# Would love to have specifics on deployment for this, for now just assume August 2013
DUAL_POLE_DEPLOYMENT_COMPLETION=datetime.datetime(month=8, year=2013, day=1)

# From https://en.wikipedia.org/wiki/NEXRAD
# The first installation of a WSR-88D for operational use in everyday forecasting was in Sterling, Virginia on June 12, 1992. The last system deployed as part of this installation campaign was installed in North Webster, Indiana on August 30, 1997. In 2011
WSR88D_DEPLOYMENT_COMPLETION=datetime.datetime(month=8, year=1997, day=30)

# https://aws.amazon.com/public-datasets/nexrad/
# "The full historical archive from NOAA from June 1991 to present is available"
S3_NEXRAD_START_DATE=datetime.datetime(month=6, year=1991, day=1)

DATASET_START_DATE=DUAL_POLE_DEPLOYMENT_COMPLETION

# beam distance from: https://www.roc.noaa.gov/WSR88D/Engineering/NEXRADTechInfo.aspx
WSR88D_BEAM_DISTANCE=230

# Lowest angle of WSR88D
WSR88D_LOW_ANGLE=math.radians(0.5)

# Highest angle of WSR88D
WSR88D_HIGH_ANGLE=math.radians(19.5)

# Earth radius in km
EARTH_RADIUS_KM=6371.0

# Coefficent for the distance of the radius of a radar station that would be relevant
RELEVANT_DISTANCE_COEFFICENT=0.5

# Data pulled from https://en.wikipedia.org/wiki/NEXRAD
# Elevation data from the Google Maps Elevation API: https://developers.google.com/maps/documentation/elevation/start
STATION_INDEX = [
        {"station_id": "PAPD", "latitude": 65.0351238, "longitude": -147.5014222, "station_elevation": 788.463378906},
        {"station_id": "PAEC", "latitude": 64.5114973, "longitude": -165.2949071, "station_elevation": 24.3814811707},
        {"station_id": "PABC", "latitude": 60.791987, "longitude": -161.876539, "station_elevation": 45.4714241028},
        {"station_id": "PAHG", "latitude": 60.6156335, "longitude": -151.2832296, "station_elevation": 33.0453109741},
        {"station_id": "PAIH", "latitude": 59.46194, "longitude": -146.30111, "station_elevation": 9.58207035065},
        {"station_id": "PAKC", "latitude": 58.6794558, "longitude": -156.6293335, "station_elevation": 24.7693424225},
        {"station_id": "PACG", "latitude": 56.85214, "longitude": -135.552417, "station_elevation": 72.8054656982},
        {"station_id": "KMBX", "latitude": 48.39303, "longitude": -100.8644378, "station_elevation": 453.602722168},
        {"station_id": "KGGW", "latitude": 48.2064536, "longitude": -106.6252971, "station_elevation": 692.583557129},
        {"station_id": "KATX", "latitude": 48.1945614, "longitude": -122.4957508, "station_elevation": 151.496307373},
        {"station_id": "KOTX", "latitude": 47.6803744, "longitude": -117.6267797, "station_elevation": 726.6328125},
        {"station_id": "KMVX", "latitude": 47.5279417, "longitude": -97.3256654, "station_elevation": 300.624237061},
        {"station_id": "KTFX", "latitude": 47.4595023, "longitude": -111.3855368, "station_elevation": 1131.57897949},
        {"station_id": "KLGX", "latitude": 47.116806, "longitude": -124.10625, "station_elevation": 72.0566177368},
        {"station_id": "KMSX", "latitude": 47.0412971, "longitude": -113.9864373, "station_elevation": 2416.84350586},
        {"station_id": "KDLH", "latitude": 46.8368569, "longitude": -92.2097433, "station_elevation": 435.757995605},
        {"station_id": "KBIS", "latitude": 46.7709329, "longitude": -100.7605532, "station_elevation": 505.457763672},
        {"station_id": "KMQT", "latitude": 46.5311443, "longitude": -87.5487131, "station_elevation": 429.599578857},
        {"station_id": "KCBW", "latitude": 46.0391944, "longitude": -67.8066033, "station_elevation": 229.192352295},
        {"station_id": "KBLX", "latitude": 45.8537632, "longitude": -108.6068165, "station_elevation": 1097.45544434},
        {"station_id": "KRTX", "latitude": 45.7150308, "longitude": -122.9650542, "station_elevation": 480.622253418},
        {"station_id": "KPDT", "latitude": 45.6906118, "longitude": -118.8529301, "station_elevation": 460.415618896},
        {"station_id": "KABR", "latitude": 45.4558185, "longitude": -98.4132046, "station_elevation": 397.455749512},
        {"station_id": "KAPX", "latitude": 44.907106, "longitude": -84.719817, "station_elevation": 444.954559326},
        {"station_id": "KMPX", "latitude": 44.8488029, "longitude": -93.5654873, "station_elevation": 290.205993652},
        {"station_id": "KCXX", "latitude": 44.5109941, "longitude": -73.166424, "station_elevation": 96.5139389038},
        {"station_id": "KGRB", "latitude": 44.4984644, "longitude": -88.111124, "station_elevation": 208.527801514},
        {"station_id": "KUDX", "latitude": 44.1248485, "longitude": -102.8298157, "station_elevation": 920.275146484},
        {"station_id": "KGYX", "latitude": 43.8913555, "longitude": -70.2565545, "station_elevation": 123.742012024},
        {"station_id": "KARX", "latitude": 43.822766, "longitude": -91.1915767, "station_elevation": 385.875732422},
        {"station_id": "KTYX", "latitude": 43.7556319, "longitude": -75.6799918, "station_elevation": 565.0},
        {"station_id": "KFSD", "latitude": 43.5877467, "longitude": -96.7293674, "station_elevation": 435.657104492},
        {"station_id": "KCBX", "latitude": 43.4902104, "longitude": -116.2360436, "station_elevation": 931.590515137},
        {"station_id": "KSFX", "latitude": 43.1055967, "longitude": -112.6860487, "station_elevation": 1363.46582031},
        {"station_id": "KRIW", "latitude": 43.0660779, "longitude": -108.4773731, "station_elevation": 1696.25708008},
        {"station_id": "KMKX", "latitude": 42.9678286, "longitude": -88.5506335, "station_elevation": 292.873931885},
        {"station_id": "KBUF", "latitude": 42.9488055, "longitude": -78.7369108, "station_elevation": 210.751663208},
        {"station_id": "KGRR", "latitude": 42.893872, "longitude": -85.5449206, "station_elevation": 235.494491577},
        {"station_id": "KDTX", "latitude": 42.6999677, "longitude": -83.471809, "station_elevation": 325.859527588},
        {"station_id": "KENX", "latitude": 42.5865699, "longitude": -74.0639877, "station_elevation": 558.070068359},
        {"station_id": "KBGM", "latitude": 42.1997045, "longitude": -75.9847015, "station_elevation": 486.897369385},
        {"station_id": "KMAX", "latitude": 42.0810766, "longitude": -122.7173334, "station_elevation": 2283.64038086},
        {"station_id": "KLNX", "latitude": 41.9579623, "longitude": -100.5759609, "station_elevation": 901.889648438},
        {"station_id": "KBOX", "latitude": 41.9558919, "longitude": -71.1369681, "station_elevation": 34.3613433838},
        {"station_id": "KDMX", "latitude": 41.7311788, "longitude": -93.7229235, "station_elevation": 299.356231689},
        {"station_id": "KDVN", "latitude": 41.611556, "longitude": -90.5809987, "station_elevation": 229.582611084},
        {"station_id": "KLOT", "latitude": 41.6044264, "longitude": -88.084361, "station_elevation": 201.561080933},
        {"station_id": "KCLE", "latitude": 41.4131875, "longitude": -81.8597451, "station_elevation": 232.110565186},
        {"station_id": "KIWX", "latitude": 41.3586356, "longitude": -85.7000488, "station_elevation": 291.789398193},
        {"station_id": "KOAX", "latitude": 41.3202803, "longitude": -96.3667971, "station_elevation": 347.570922852},
        {"station_id": "KMTX", "latitude": 41.2627795, "longitude": -112.4480081, "station_elevation": 1968.43981934},
        {"station_id": "KCYS", "latitude": 41.1519308, "longitude": -104.8060325, "station_elevation": 1867.6307373},
        {"station_id": "KCCX", "latitude": 40.9228521, "longitude": -78.0038738, "station_elevation": 733.065734863},
        {"station_id": "KOKX", "latitude": 40.8655093, "longitude": -72.8638548, "station_elevation": 31.604637146},
        {"station_id": "KLRX", "latitude": 40.7396933, "longitude": -116.8025529, "station_elevation": 2055.91210938},
        {"station_id": "KPBZ", "latitude": 40.5316842, "longitude": -80.2179515, "station_elevation": 360.94921875},
        {"station_id": "KBHX", "latitude": 40.4986955, "longitude": -124.2918867, "station_elevation": 730.621398926},
        {"station_id": "KUEX", "latitude": 40.320966, "longitude": -98.4418559, "station_elevation": 601.917175293},
        {"station_id": "KILX", "latitude": 40.150544, "longitude": -89.336842, "station_elevation": 177.434738159},
        {"station_id": "KDIX", "latitude": 39.9470885, "longitude": -74.4108027, "station_elevation": 44.7942123413},
        {"station_id": "KFTG", "latitude": 39.7866156, "longitude": -104.5458126, "station_elevation": 1675.9786377},
        {"station_id": "KRGX", "latitude": 39.7541931, "longitude": -119.4620597, "station_elevation": 2529.13623047},
        {"station_id": "KIND", "latitude": 39.7074962, "longitude": -86.2803675, "station_elevation": 239.935531616},
        {"station_id": "KILN", "latitude": 39.5083314, "longitude": -83.8176925, "station_elevation": 314.308288574},
        {"station_id": "KBBX", "latitude": 39.4956958, "longitude": -121.6316557, "station_elevation": 52.6806488037},
        {"station_id": "KGLD", "latitude": 39.3667737, "longitude": -101.7004341, "station_elevation": 1113.39050293},
        {"station_id": "KGJX", "latitude": 39.0619824, "longitude": -108.2137012, "station_elevation": 3046.57763672},
        {"station_id": "KTWX", "latitude": 38.996998, "longitude": -96.232618, "station_elevation": 418.096984863},
        {"station_id": "KLWX", "latitude": 38.9753957, "longitude": -77.4778444, "station_elevation": 82.3895339966},
        {"station_id": "KDOX", "latitude": 38.8257651, "longitude": -75.4400763, "station_elevation": 14.4144229889},
        {"station_id": "KEAX", "latitude": 38.8102231, "longitude": -94.2644924, "station_elevation": 304.820037842},
        {"station_id": "LPLA", "latitude": 38.73028, "longitude": -27.32167, "station_elevation": 995.914611816},
        {"station_id": "KLSX", "latitude": 38.6986863, "longitude": -90.682877, "station_elevation": 186.451065063},
        {"station_id": "KDAX", "latitude": 38.5011529, "longitude": -121.6778487, "station_elevation": 9.16355609894},
        {"station_id": "KPUX", "latitude": 38.4595034, "longitude": -104.1816223, "station_elevation": 1599.49328613},
        {"station_id": "KRLX", "latitude": 38.3110763, "longitude": -81.7229015, "station_elevation": 328.85546875},
        {"station_id": "KVWX", "latitude": 38.2603901, "longitude": -87.7246553, "station_elevation": 155.295959473},
        {"station_id": "KLVX", "latitude": 37.9753058, "longitude": -85.9438455, "station_elevation": 220.269515991},
        {"station_id": "KDDC", "latitude": 37.7608043, "longitude": -99.9688053, "station_elevation": 790.674621582},
        {"station_id": "KICT", "latitude": 37.6545724, "longitude": -97.4431461, "station_elevation": 407.627838135},
        {"station_id": "KICX", "latitude": 37.5931771, "longitude": -112.8637719, "station_elevation": 3259.25219727},
        {"station_id": "KJKL", "latitude": 37.590762, "longitude": -83.313039, "station_elevation": 415.126831055},
        {"station_id": "KSGF", "latitude": 37.235223, "longitude": -93.4006011, "station_elevation": 388.133117676},
        {"station_id": "RKSG", "latitude": 37.207652, "longitude": 127.285614, "station_elevation": 430.03793335},
        {"station_id": "KMUX", "latitude": 37.155152, "longitude": -121.8984577, "station_elevation": 1057.89123535},
        {"station_id": "KPAH", "latitude": 37.0683618, "longitude": -88.7720257, "station_elevation": 120.565567017},
        {"station_id": "KFCX", "latitude": 37.0242098, "longitude": -80.2736664, "station_elevation": 879.090270996},
        {"station_id": "KAKQ", "latitude": 36.9840475, "longitude": -77.007342, "station_elevation": 34.4969215393},
        {"station_id": "KVNX", "latitude": 36.7406166, "longitude": -98.1279409, "station_elevation": 368.980804443},
        {"station_id": "KHPX", "latitude": 36.7368894, "longitude": -87.2854328, "station_elevation": 174.537643433},
        {"station_id": "KHNX", "latitude": 36.3142088, "longitude": -119.6320903, "station_elevation": 72.0174713135},
        {"station_id": "KOHX", "latitude": 36.2472389, "longitude": -86.5625185, "station_elevation": 176.830490112},
        {"station_id": "KINX", "latitude": 36.1750977, "longitude": -95.5642802, "station_elevation": 202.862304688},
        {"station_id": "KMRX", "latitude": 36.168538, "longitude": -83.401779, "station_elevation": 407.261138916},
        {"station_id": "RKJK", "latitude": 35.92417, "longitude": 126.62222, "station_elevation": 24.3717212677},
        {"station_id": "KESX", "latitude": 35.7012894, "longitude": -114.8918277, "station_elevation": 1481.92224121},
        {"station_id": "KRAX", "latitude": 35.6654967, "longitude": -78.4897855, "station_elevation": 105.193130493},
        {"station_id": "KNQA", "latitude": 35.3447802, "longitude": -89.8734534, "station_elevation": 87.3559570312},
        {"station_id": "KTLX", "latitude": 35.3333873, "longitude": -97.2778255, "station_elevation": 370.923034668},
        {"station_id": "KSRX", "latitude": 35.2904423, "longitude": -94.3619075, "station_elevation": 192.766220093},
        {"station_id": "KAMA", "latitude": 35.2334827, "longitude": -101.7092478, "station_elevation": 1094.82958984},
        {"station_id": "KABX", "latitude": 35.1497579, "longitude": -106.8239576, "station_elevation": 1789.65551758},
        {"station_id": "KEYX", "latitude": 35.0979358, "longitude": -117.5608832, "station_elevation": 840.429992676},
        {"station_id": "KHTX", "latitude": 34.930508, "longitude": -86.0837388, "station_elevation": 538.872131348},
        {"station_id": "KGSP", "latitude": 34.8833435, "longitude": -82.2200757, "station_elevation": 287.539581299},
        {"station_id": "KVBX", "latitude": 34.8383137, "longitude": -120.3977805, "station_elevation": 373.35067749},
        {"station_id": "KLZK", "latitude": 34.8365261, "longitude": -92.2621697, "station_elevation": 173.993942261},
        {"station_id": "KMHX", "latitude": 34.7759313, "longitude": -76.8762571, "station_elevation": 8.73695468903},
        {"station_id": "KFDX", "latitude": 34.6341569, "longitude": -103.6186427, "station_elevation": 1418.25488281},
        {"station_id": "KFSX", "latitude": 34.574449, "longitude": -111.198367, "station_elevation": 2261.4152832},
        {"station_id": "KVTX", "latitude": 34.4116386, "longitude": -119.1795641, "station_elevation": 830.90411377},
        {"station_id": "KFDR", "latitude": 34.3620014, "longitude": -98.9766884, "station_elevation": 383.358886719},
        {"station_id": "KLTX", "latitude": 33.9891631, "longitude": -78.4291059, "station_elevation": 18.303440094},
        {"station_id": "KCAE", "latitude": 33.9487579, "longitude": -81.1184281, "station_elevation": 70.5524291992},
        {"station_id": "KGWX", "latitude": 33.8967796, "longitude": -88.3293915, "station_elevation": 144.803924561},
        {"station_id": "KSOX", "latitude": 33.8176452, "longitude": -117.6359743, "station_elevation": 923.408813477},
        {"station_id": "KLBB", "latitude": 33.6541242, "longitude": -101.814149, "station_elevation": 993.510437012},
        {"station_id": "KFFC", "latitude": 33.3635771, "longitude": -84.565866, "station_elevation": 261.607788086},
        {"station_id": "KIWA", "latitude": 33.289111, "longitude": -111.6700092, "station_elevation": 410.986938477},
        {"station_id": "KBMX", "latitude": 33.1722806, "longitude": -86.7698425, "station_elevation": 196.879852295},
        {"station_id": "KHDX", "latitude": 33.0768844, "longitude": -106.1200923, "station_elevation": 1285.55737305},
        {"station_id": "KNKX", "latitude": 32.9189891, "longitude": -117.041814, "station_elevation": 291.50668335},
        {"station_id": "KJGX", "latitude": 32.6755239, "longitude": -83.3508575, "station_elevation": 156.225311279},
        {"station_id": "KCLX", "latitude": 32.6554866, "longitude": -81.0423124, "station_elevation": 31.1657505035},
        {"station_id": "KFWS", "latitude": 32.5730186, "longitude": -97.3031911, "station_elevation": 210.197479248},
        {"station_id": "KDYX", "latitude": 32.5386009, "longitude": -99.2542863, "station_elevation": 460.04083252},
        {"station_id": "KMXX", "latitude": 32.5366608, "longitude": -85.7897848, "station_elevation": 123.997749329},
        {"station_id": "KYUX", "latitude": 32.4953477, "longitude": -114.6567214, "station_elevation": 53.358833313},
        {"station_id": "KSHV", "latitude": 32.450813, "longitude": -93.8412774, "station_elevation": 82.6875839233},
        {"station_id": "KDGX", "latitude": 32.2797358, "longitude": -89.9846309, "station_elevation": 153.181747437},
        {"station_id": "KMAF", "latitude": 31.9433953, "longitude": -102.1894383, "station_elevation": 873.089416504},
        {"station_id": "KEMX", "latitude": 31.8937186, "longitude": -110.6304306, "station_elevation": 1589.84436035},
        {"station_id": "KEPZ", "latitude": 31.8731115, "longitude": -106.697942, "station_elevation": 1252.69677734},
        {"station_id": "KEOX", "latitude": 31.4605622, "longitude": -85.4592401, "station_elevation": 131.946609497},
        {"station_id": "KSJT", "latitude": 31.3712815, "longitude": -100.4925227, "station_elevation": 577.01550293},
        {"station_id": "KPOE", "latitude": 31.1556923, "longitude": -92.9762596, "station_elevation": 123.123786926},
        {"station_id": "KVAX", "latitude": 30.8903853, "longitude": -83.0019021, "station_elevation": 54.7624778748},
        {"station_id": "KGRK", "latitude": 30.7217637, "longitude": -97.3829627, "station_elevation": 165.986541748},
        {"station_id": "KMOB", "latitude": 30.6795378, "longitude": -88.2397816, "station_elevation": 63.1785812378},
        {"station_id": "KEVX", "latitude": 30.5649908, "longitude": -85.921559, "station_elevation": 42.5061149597},
        {"station_id": "KJAX", "latitude": 30.4846878, "longitude": -81.7018917, "station_elevation": 8.6268119812},
        {"station_id": "KTLH", "latitude": 30.397568, "longitude": -84.3289116, "station_elevation": 18.8315582275},
        {"station_id": "KLIX", "latitude": 30.3367133, "longitude": -89.8256618, "station_elevation": 6.59722566605},
        {"station_id": "KLCH", "latitude": 30.125382, "longitude": -93.2161188, "station_elevation": 3.53188371658},
        {"station_id": "KEWX", "latitude": 29.7039802, "longitude": -98.028506, "station_elevation": 195.63734436},
        {"station_id": "KHGX", "latitude": 29.4718835, "longitude": -95.0788593, "station_elevation": 4.79184913635},
        {"station_id": "KDFX", "latitude": 29.2730823, "longitude": -100.2802312, "station_elevation": 343.964935303},
        {"station_id": "KMLB", "latitude": 28.1131808, "longitude": -80.6540988, "station_elevation": 10.2366123199},
        {"station_id": "KCRP", "latitude": 27.7840203, "longitude": -97.511234, "station_elevation": 13.181974411},
        {"station_id": "KTBW", "latitude": 27.7054701, "longitude": -82.40179, "station_elevation": 11.8444347382},
        {"station_id": "RODN", "latitude": 26.30194, "longitude": 127.90972, "station_elevation": 5.96002388},
        {"station_id": "KBRO", "latitude": 25.9159979, "longitude": -97.4189526, "station_elevation": 6.66874933243},
        {"station_id": "KAMX", "latitude": 25.6111275, "longitude": -80.412747, "station_elevation": 3.33103895187},
        {"station_id": "KBYX", "latitude": 24.5974996, "longitude": -81.7032355, "station_elevation": 1.70358395576},
        {"station_id": "PHKI", "latitude": 21.8938762, "longitude": -159.5524585, "station_elevation": 59.5274085999},
        {"station_id": "PHMO", "latitude": 21.1327531, "longitude": -157.1802807, "station_elevation": 412.600006104},
        {"station_id": "PHKM", "latitude": 20.1254606, "longitude": -155.778054, "station_elevation": 1152.22705078},
        {"station_id": "PHWA", "latitude": 19.0950155, "longitude": -155.5688846, "station_elevation": 418.051971436},
        {"station_id": "TJUA", "latitude": 18.1155998, "longitude": -66.0780644, "station_elevation": 844.801513672},
        {"station_id": "PGUA", "latitude": 13.455965, "longitude": 144.8111022, "station_elevation": 79.0276412964}
]

STATION_IDS = [station["station_id"] for station in STATION_INDEX]
STATION_LATLONS = [(station["latitude"], station["longitude"]) for station in STATION_INDEX]


class S3NEXRADHelper:

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

    def findNEXRADKeysByTimeAndDomain(self, start_datetime, end_datetime, maxlat, maxlon, minlat, minlon, height):
        """Get list of keys to nexrad files on s3 from a time range and lat/lon domain.

        start_datetime: start of time range in a datetime.datetime object
        end_datetime: end of time range in a datetime.datetime object
        maxlat: maximum latitude of domain
        maxlon: maximum longitude of domain
        minlat: minimum lattitude of domain
        minlon: minimum longitude of domain
        height: height above sealevel in meters for domain

        returns: List of keys in nexrad s3 bucket corespopnding to the parameters
        """
        station_list = self.getStationsFromDomain(maxlat, maxlon, minlat, minlon, height)
        if not station_list:
            print "No stations found for specified domain"
            return

        if self.verbose:
           print "Found stations: %s for domain %s,%s to %s,%s" % (','.join(station_list),
                   maxlat, maxlon, minlat, minlon)
        files = self.searchNEXRADS3(start_datetime, end_datetime, station_list)

        if self.verbose:
            print "Found files for time range: %s to %s" % (
                    start_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    end_datetime.strftime("%Y-%m-%d %H:%M:%S"))
            for filekey in files:
                print filekey

        return files

    def downloadNEXRADFiles(self, download_dir, s3keys):
        """Download files from S3 NEXRAD bucket

        download_dir: The directory to download the file to
        s3keys: list of keys in the nexrad bucket to download

        returns: list of downloaded file paths
        """
        if not os.path.exists(download_dir):
            print "Unable to find download directory, skipping downloads"
            return
        file_paths = []
        for key in s3keys:
            file_path = os.path.join(download_dir, key.split('/')[-1])
            file_paths.append(file_path)

            self._addToThreadPool(_downloadFile, (key, file_path, self.verbose))
            self._waitForThreadPool()

        self._waitForThreadPool(thread_max=0)

        return file_paths
            
    def getStationsFromDomain(self, maxlat, maxlon, minlat, minlon, height=10000):
        """Searches station list for radar stations that would be relevant
        to the domain provided.

        maxlat: maximum latitude of domain
        maxlon: maximum longitude of domain
        minlat: minimum lattitude of domain
        minlon: minimum longitude of domain
        height: height above sealevel in meters for domain

        returns: list of station ids ex. ['KIND', 'KLVX']
        """

        # http://geokov.com/education/utm.aspx
        # easting values increase towards east
        # max lon is east side
        # max lat is north 

        maxnorth_domain, maxeast_domain, max_zone_number, max_zone_letter = utm.from_latlon(maxlat, maxlon)

        minnorth_domain, mineast_domain, min_zone_number, min_zone_letter = utm.from_latlon(minlat, minlon)

        relevant_stations = []
        possibly_relevant_stations = []
        for i, latlon in enumerate(STATION_LATLONS): 
            lat, lon = latlon

            station_radius = self._calculateRadiusAtHeight(height, 
                    STATION_INDEX[i]['station_elevation'])
            if station_radius is None:
                continue

            relevant_radius = RELEVANT_DISTANCE_COEFFICENT*station_radius

            maxeast = maxeast_domain + relevant_radius
            maxnorth = maxnorth_domain + relevant_radius
            domain_maxlat, domain_maxlon = utm.to_latlon(maxnorth, maxeast, max_zone_number,
                max_zone_letter, strict=False)

            mineast = mineast_domain - relevant_radius
            minnorth = minnorth_domain - relevant_radius
            domain_minlat, domain_minlon = utm.to_latlon(minnorth, mineast, min_zone_number,
                    min_zone_letter, strict=False)

            # Vertical band of relevant domain bounded by user-given domain
            if ((lat <= domain_maxlat and lat >= domain_minlat) and
                    (lon <= maxlon and lon >= minlon)):
                relevant_stations.append(STATION_INDEX[i]['station_id'])

            # Horizontal band of relevant domain bounded by user-given domain
            elif ((lat <= maxlat and lat >= minlat) and
                    (lon <= domain_maxlon and lon >= domain_minlon)):
                relevant_stations.append(STATION_INDEX[i]['station_id'])

            # north east corner of relevant domain
            elif ((lat <= domain_maxlat and lat >= maxlat) and 
                    (lon <= domain_maxlon and lon >= maxlon) and
                    _isStationInDomainCorner(maxlat, maxlon,
                        STATION_INDEX[i]['latitude'], 
                        STATION_INDEX[i]['longitude'],
                        relevant_radius)):

                relevant_stations.append(STATION_INDEX[i]['station_id'])

            # south east corner of relevant domain
            elif ((lat <= domain_minlat and lat >= minlat) and
                    (lon <= domain_maxlon and lon >= maxlon) and
                    _isStationInDomainCorner(minlat, maxlon,
                        STATION_INDEX[i]['latitude'], 
                        STATION_INDEX[i]['longitude'],
                        relevant_radius)):

                relevant_stations.append(STATION_INDEX[i]['station_id'])

            # south west corner of relevant domain
            elif ((lat <= domain_minlat and lat >= minlat) and
                    (lon <= domain_minlon and lon >= minlon) and
                    _isStationInDomainCorner(minlat, minlon,
                        STATION_INDEX[i]['latitude'], 
                        STATION_INDEX[i]['longitude'],
                        relevant_radius)):

                relevant_stations.append(STATION_INDEX[i]['station_id'])

            # north west corner of relevant domain
            elif ((lat <= domain_maxlat and lat >= maxlat) and
                    (lon <= domain_minlon and lon >= minlon) and
                    _isStationInDomainCorner(maxlat, minlon,
                        STATION_INDEX[i]['latitude'], 
                        STATION_INDEX[i]['longitude'],
                        relevant_radius)):

                relevant_stations.append(STATION_INDEX[i]['station_id'])

        return relevant_stations

    def searchNEXRADS3(self, start_datetime, end_datetime, station_list):
        """Find available files from a date range and a station list

        start_datetime: start of time range in a datetime.datetime object
        end_datetime: end of time range in a datetime.datetime object
        station_list: list of station ids as strings ex. ["KIND", "KVBX"]

        returns: list of keys in the nexrad s3 bucket within the time range for the specified stations
        """
        start = start_datetime
        if start_datetime < DATASET_START_DATE:
            if verbose:
                print "Start time is before the dataset start date, will use dataset start time instead"
            start = DATASET_START_DATE

        end = end_datetime
        if end_datetime > datetime.datetime.now():
            if verbose:
                print "End time is in the future, will use today as end time"
            end = datetime.datetime.now()


        dir_key_list = []
        for station_id in station_list:
            if station_id not in STATION_IDS:
                print "Station %s not found, skipping" % station_id
                continue
            current_date = start.replace(hour=0)
            while current_date < end:
                dir_key_list.append("%d/%02d/%02d/%s" % (current_date.year, current_date.month,
                    current_date.day, station_id))
                current_date = current_date + datetime.timedelta(days=1)

        start_dir = "%d/%02d/%02d/" % (start.year, start.month ,start.day)
        end_dir = "%d/%02d/%02d/" % (end.year, end.month, end.day)
        files_list = []

        # 2015/05/06/KSGF/KSGF20150506_224351_V06.gz
        # drop everything except the time the time
        before_time_index = 20
        after_time_index = 35
        for dir_key in dir_key_list:
            for file in self.bucket.list("%s/" % dir_key, "/"):
                file_name = file.name 

                if not file_name.endswith('gz'):
                    continue

                if file_name.startswith(start_dir):
                    file_datetime = datetime.datetime.strptime(
                            file_name[before_time_index:after_time_index],
                            "%Y%m%d_%H%M%S")
                    if file_datetime <= start:
                        continue

                if file_name.startswith(end_dir):
                    file_datetime = datetime.datetime.strptime(
                            file_name[before_time_index:after_time_index],
                            "%Y%m%d_%H%M%S")
                    if file_datetime >= end:
                        continue

                files_list.append(file_name)
        return files_list

    def _calculateRadiusAtHeight(self, height, station_elevation):
        """This function calculates the radius at the specified height above sealevel.
        This function takes into consideration both the height of the radar station 
        and the ange of the radar beam. This is a rough estimate and does not take
        into account refraction or beam width. It also assumes a spherical earth.

        height: height above sea level in meters
        station_elevation: radar site height above sea level in meters

        returns: ground distance radius of radar in meters or None if height is not available
        """
        # anything bigger can throw errors and this is outside of the operational specs of
        # the current and future VCPs - https://en.wikipedia.org/wiki/NEXRAD
        if height > 90000: return None

        # There should probably be a lower bound here but I haven't been able to find it yet
        #if height < ?: return None

        # highest point above sea level
        if station_elevation > 6267: return None

        # radar must be lower than specified height
        if station_elevation >= height: return None

        # based on figure 2 of http://www.radartutorial.eu/01.basics/Calculation%20of%20height.en.html
        # TODO: include refraction in the calculation
        height_km = height/1000.0 - station_elevation/1000

        localized_radius = EARTH_RADIUS_KM + station_elevation/1000

        # Create an triange on a circle (2d earth), the three side are the length of
        # localized radius connected, the radar beam and the height + localized_radius 
        # connecting to the beam end and the earth center

        height_of_beam_end = localized_radius + height_km

        # lowest angle at the radar site
        # 90 degrees + radar beam angle
        radar_site_angle = math.radians(90) + WSR88D_LOW_ANGLE
        #######
        # Calculate max ground distance at 0.5 degrees for WSR88D_MAX_RADIUS constant
        #a, b, beam_distance, beam_point_angle, B, earth_center_angle = trianglesolver.solve(
        #        a = EARTH_RADIUS_KM, c = WSR88D_BEAM_DISTANCE, B = radar_site_angle, ssa_flag='acute')
        #print earth_center_angle * EARTH_RADIUS_KM
        # WSR88D_MAX_RADIUS=229819.074224
        #######

        a, b, beam_distance, beam_point_angle, B, earth_center_angle = trianglesolver.solve(
                a = localized_radius, b = height_of_beam_end, B = radar_site_angle, ssa_flag='acute')

        # if our beam_distance is too high then check the highest beam
        if (beam_distance > WSR88D_BEAM_DISTANCE):
        
            # angle at the radar site
            # 90 degrees + radar beam angle
            radar_site_angle = math.radians(90) + WSR88D_HIGH_ANGLE

            a, b, beam_distance, beam_point_angle, B, earth_center_angle = trianglesolver.solve(
                    a = localized_radius, b = height_of_beam_end, B = radar_site_angle, ssa_flag='acute')

            # if we still don't have a reasonable beam distance, return None
            if (beam_distance > WSR88D_BEAM_DISTANCE):
                return None

            # If beam distance is fine, solve for this height at max beam_distance so we can 
            # get the appropriate ground distance for the radar's radius at this height
            a, b, c, A, radar_site_angle, earth_center_angle = trianglesolver.solve(
                    a = localized_radius, b = height_of_beam_end, c = WSR88D_BEAM_DISTANCE)

        #print math.degrees(radar_site_angle)

        # the ground distance is the circular segment with angle earth_center_angle and r of localized_radius
        # this assumes a smooth earth (and a shperical cow)
        ground_distance_km = earth_center_angle * localized_radius

        ground_distance = ground_distance_km * 1000

        return ground_distance


    def _isStationInDomainCorner(self, corner_lat, corner_lon, station_lat, station_lon,
            radius):
        """Take the relevant domain distance as the radius for a circle around the point
        of the corner of the user-provided domain. Create this shape and check to see if the 
        station lies within it.

        corner_lat: lattitude of a corner point of the user-provided domain
        corner_lon: longitude of the same corner point of the user-provided domain
        station_lat: latitude of the station to be checked
        station_lon: longitude of the station to be checked
        radius: distance from the corner point to check 
            Highly suggested: the radius is the same distance to calculate the relevant domain


        return: Boolean of if the station is within the domain
        """
        easting_points, northing_points, zone_number, zone_letter =_createGeographicCircle(
                corner_lat, corner_lon, radius)
        shape = []
        for i in range(0, len(easting_points)):
            shape.append([easting_points[i], northing_points[i]])

        relevant_domain = matplotlib.path.Path(numpy_array(shape))

        station_easting, station_northing, station_zone_number, station_zone_letter = utm.from_latlon(
            lat, lon, force_zone_number=zone_number)

        return relevant_domain.contains_point(station_easting, station_northing)

    def _createGeographicCircle(self, lat, lon, radius):
        """Create points on circumfrence of circle centered at lat,lon.
        
        lat: lattiude of center of circle
        lon: longitude of center of circle
        radius: radius of circle in meters

        returns: tuple of (easting_points, northing_points, zone_number, zone_letter)
        """
        center_easting, center_northing, zone_number, zone_letter = utm.from_latlon(lat, lon)

        points_in_shape = 45

        easting_points = []
        northing_points = []

        theta = (math.pi*2) / points_in_shape
        for i in range(1, points_in_shape + 1):
            angle = theta * i

            point_easting = radius * math.cos(angle) + center_easting
            point_northing  = radius * math.sin(angle) + center_northing

        easting_points.append(point_easting)
        northing_points.append(point_northing)

        return (easting_points, northing_points, zone_number, zone_letter)

    def _addToThreadPool(self, function, args):
        proc = multiprocessing.Process(target=function, args=args)
        proc.start()
        self.threads.append(proc)
        self.thread_count += 1

    def _waitForThreadPool(self, thread_max=None):
        if thread_max is None:
            thread_limit = self.thread_max - 1
        else:
            thread_limit = thread_max
        count = 0
        while len(self.threads) > thread_limit:
            time.sleep(.1)
            if count > len(self.threads) - 1:
                count = 0
            if self.threads[count].exitcode is not None:
                self.threads[count].join(1)
                self.threads.pop(count)
            else: 
                count += 1

def _downloadFile(key, file_path, verbose):
    s3conn = boto.connect_s3(anon=True)
    bucket = s3conn.get_bucket("noaa-nexrad-level2")
    keyobj = bucket.get_key(key)
    if keyobj is None:
        if self.verbose: print "Unable to find file %s, skipping" % key
        return

    dfile = open(file_path, 'w')
    try:
        keyobj.get_file(dfile)
    finally:
        dfile.close()

    if verbose:
        print "%s downloaded" % file_path


def main():
    ## EXAMPLE USAGE
    nexrad = S3NEXRADHelper(threads=20)
    s3keys = nexrad.findNEXRADKeysByTimeAndDomain(
            datetime.datetime(day=5, month=5, year=2015, hour=5),
            datetime.datetime(day=5, month=5, year=2015, hour=6), 
            41.22, -84.79, 38.22, -87.79, 20000)
    #nexrad.downloadNEXRADFiles('temp', s3keys)

if __name__ == "__main__":
    main()


# STATIONS
# PAPD 65.0351238 N 147.5014222 W
# PAEC 64.5114973 N 165.2949071 W
# PABC 60.791987 N 161.876539 W
# PAHG 60.6156335 N 151.2832296 W
# PAIH 59.46194 N 146.30111 W
# PAKC 58.6794558 N 156.6293335 W
# PACG 56.85214 N 135.552417 W
# KMBX 48.39303 N 100.8644378 W
# KGGW 48.2064536 N 106.6252971 W
# KATX 48.1945614 N 122.4957508 W
# KOTX 47.6803744 N 117.6267797 W
# KMVX 47.5279417 N 97.3256654 W
# KTFX 47.4595023 N 111.3855368 W
# KLGX 47.116806 N 124.10625 W
# KMSX 47.0412971 N 113.9864373 W
# KDLH 46.8368569 N 92.2097433 W
# KBIS 46.7709329 N 100.7605532 W
# KMQT 46.5311443 N 87.5487131 W
# KCBW 46.0391944 N 67.8066033 W
# KBLX 45.8537632 N 108.6068165 W
# KRTX 45.7150308 N 122.9650542 W
# KPDT 45.6906118 N 118.8529301 W
# KABR 45.4558185 N 98.4132046 W
# KAPX 44.907106 N 84.719817 W
# KMPX 44.8488029 N 93.5654873 W
# KCXX 44.5109941 N 73.166424 W
# KGRB 44.4984644 N 88.111124 W
# KUDX 44.1248485 N 102.8298157 W
# KGYX 43.8913555 N 70.2565545 W
# KARX 43.822766 N 91.1915767 W
# KTYX 43.7556319 N 75.6799918 W
# KFSD 43.5877467 N 96.7293674 W
# KCBX 43.4902104 N 116.2360436 W
# KSFX 43.1055967 N 112.6860487 W
# KRIW 43.0660779 N 108.4773731 W
# KMKX 42.9678286 N 88.5506335 W
# KBUF 42.9488055 N 78.7369108 W
# KGRR 42.893872 N 85.5449206 W
# KDTX 42.6999677 N 83.471809 W
# KENX 42.5865699 N 74.0639877 W
# KBGM 42.1997045 N 75.9847015 W
# KMAX 42.0810766 N 122.7173334 W
# KLNX 41.9579623 N 100.5759609 W
# KBOX 41.9558919 N 71.1369681 W
# KDMX 41.7311788 N 93.7229235 W
# KDVN 41.611556 N 90.5809987 W
# KLOT 41.6044264 N 88.084361 W
# KCLE 41.4131875 N 81.8597451 W
# KIWX 41.3586356 N 85.7000488 W
# KOAX 41.3202803 N 96.3667971 W
# KMTX 41.2627795 N 112.4480081 W
# KCYS 41.1519308 N 104.8060325 W
# KCCX 40.9228521 N 78.0038738 W
# KOKX 40.8655093 N 72.8638548 W
# KLRX 40.7396933 N 116.8025529 W
# KPBZ 40.5316842 N 80.2179515 W
# KBHX 40.4986955 N 124.2918867 W
# KUEX 40.320966 N 98.4418559 W
# KILX 40.150544 N 89.336842 W
# KDIX 39.9470885 N 74.4108027 W
# KFTG 39.7866156 N 104.5458126 W
# KRGX 39.7541931 N 119.4620597 W
# KIND 39.7074962 N 86.2803675 W
# KILN 39.5083314 N 83.8176925 W
# KBBX 39.4956958 N 121.6316557 W
# KGLD 39.3667737 N 101.7004341 W
# KGJX 39.0619824 N 108.2137012 W
# KTWX 38.996998 N 96.232618 W
# KLWX 38.9753957 N 77.4778444 W
# KDOX 38.8257651 N 75.4400763 W
# KEAX 38.8102231 N 94.2644924 W
# LPLA 38.73028 N 27.32167 W
# KLSX 38.6986863 N 90.682877 W
# KDAX 38.5011529 N 121.6778487 W
# KPUX 38.4595034 N 104.1816223 W
# KRLX 38.3110763 N 81.7229015 W
# KVWX 38.2603901 N 87.7246553 W
# KLVX 37.9753058 N 85.9438455 W
# KDDC 37.7608043 N 99.9688053 W
# KICT 37.6545724 N 97.4431461 W
# KICX 37.5931771 N 112.8637719 W
# KJKL 37.590762 N 83.313039 W
# KSGF 37.235223 N 93.4006011 W
# RKSG 37.207652 N 127.285614 E
# KMUX 37.155152 N 121.8984577 W
# KPAH 37.0683618 N 88.7720257 W
# KFCX 37.0242098 N 80.2736664 W
# KAKQ 36.9840475 N 77.007342 W
# KVNX 36.7406166 N 98.1279409 W
# KHPX 36.7368894 N 87.2854328 W
# KHNX 36.3142088 N 119.6320903 W
# KOHX 36.2472389 N 86.5625185 W
# KINX 36.1750977 N 95.5642802 W
# KMRX 36.168538 N 83.401779 W
# RKJK 35.92417 N 126.62222 E
# KESX 35.7012894 N 114.8918277 W
# KRAX 35.6654967 N 78.4897855 W
# KNQA 35.3447802 N 89.8734534 W
# KTLX 35.3333873 N 97.2778255 W
# KSRX 35.2904423 N 94.3619075 W
# Data 35.2358 N 97.4622 W
# KAMA 35.2334827 N 101.7092478 W
# KABX 35.1497579 N 106.8239576 W
# KEYX 35.0979358 N 117.5608832 W
# KHTX 34.930508 N 86.0837388 W
# KGSP 34.8833435 N 82.2200757 W
# KVBX 34.8383137 N 120.3977805 W
# KLZK 34.8365261 N 92.2621697 W
# KMHX 34.7759313 N 76.8762571 W
# KFDX 34.6341569 N 103.6186427 W
# KFSX 34.574449 N 111.198367 W
# KVTX 34.4116386 N 119.1795641 W
# KFDR 34.3620014 N 98.9766884 W
# KLTX 33.9891631 N 78.4291059 W
# KCAE 33.9487579 N 81.1184281 W
# KGWX 33.8967796 N 88.3293915 W
# KSOX 33.8176452 N 117.6359743 W
# KLBB 33.6541242 N 101.814149 W
# KFFC 33.3635771 N 84.565866 W
# KIWA 33.289111 N 111.6700092 W
# KBMX 33.1722806 N 86.7698425 W
# KHDX 33.0768844 N 106.1200923 W
# KNKX 32.9189891 N 117.041814 W
# KJGX 32.6755239 N 83.3508575 W
# KCLX 32.6554866 N 81.0423124 W
# KFWS 32.5730186 N 97.3031911 W
# KDYX 32.5386009 N 99.2542863 W
# KMXX 32.5366608 N 85.7897848 W
# KYUX 32.4953477 N 114.6567214 W
# KSHV 32.450813 N 93.8412774 W
# KDGX 32.2797358 N 89.9846309 W
# KMAF 31.9433953 N 102.1894383 W
# KEMX 31.8937186 N 110.6304306 W
# KEPZ 31.8731115 N 106.697942 W
# KEOX 31.4605622 N 85.4592401 W
# KSJT 31.3712815 N 100.4925227 W
# KPOE 31.1556923 N 92.9762596 W
# KVAX 30.8903853 N 83.0019021 W
# KGRK 30.7217637 N 97.3829627 W
# KMOB 30.6795378 N 88.2397816 W
# KEVX 30.5649908 N 85.921559 W
# KJAX 30.4846878 N 81.7018917 W
# KTLH 30.397568 N 84.3289116 W
# KLIX 30.3367133 N 89.8256618 W
# KLCH 30.125382 N 93.2161188 W
# KEWX 29.7039802 N 98.028506 W
# KHGX 29.4718835 N 95.0788593 W
# KDFX 29.2730823 N 100.2802312 W
# KMLB 28.1131808 N 80.6540988 W
# KCRP 27.7840203 N 97.511234 W
# KTBW 27.7054701 N 82.40179 W
# RODN 26.30194 N 127.90972 E
# KBRO 25.9159979 N 97.4189526 W
# KAMX 25.6111275 N 80.412747 W
# KBYX 24.5974996 N 81.7032355 W
# PHKI 21.8938762 N 159.5524585 W
# PHMO 21.1327531 N 157.1802807 W
# PHKM 20.1254606 N 155.778054 W
# PHWA 19.0950155 N 155.5688846 W
# TJUA 18.1155998 N 66.0780644 W
# PGUA 13.455965 N 144.8111022 E
