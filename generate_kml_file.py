#!/usr/bin/env python

'''This file reads the log files in each directory,  generates new points based on start
points and AOAs, and outputs a KMZ file for import into Google Earth'''


from geopy.distance import vincenty
import pykml

def vincenty_direct(latitude, longitude, angle):
    '''Applies Vincenty's Direct Formula to calculate resulting position from:
    phi_1: initial latitude
    L_1: initial longitude
    alpha_1: initial azimuth (radians????)
    s: distance between points'''
    p1 = vincenty(vector_length) #10 km
    p2 = p1.destination(initial_point, angle)

def get_kml_path_object(something_goes_here):
    return KML.Placemark(...)

def generate_vector_file(vector_length):
    #over here, generate an array pf path objects

    #sources from https://code.google.com/p/pykml/source/browse/src/utilities/test_gen_pykml.py
    output_map = KML.kml(
        KML.Document(
            KML.Folder(
                KML.name("Paths"),
                KML.Placemark(
    
    #of each

    output_map.Document.append(
        KML.Placemark(



# for each subdirectory of globaly defined path
# open the log file. read each coordinate/angle and convert to p2.
# build up a long string of paths. The path name should be the timestamp. 2014-02-07-23-55-55
# create a kmz file from the path string
