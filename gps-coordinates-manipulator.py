#!/usr/bin/env python

from geopy.distance import vincenty

'''This file contains methods used to process GPS coordinates'''
def log_position_and_angle(position, angle):
    pass

def vincenty_direct(latitude, longitude, angle):
    '''Applies Vincenty's Direct Formula to calculate resulting position from:
    phi_1: initial latitude
    L_1: initial longitude
    alpha_1: initial azimuth (radians????)
    s: distance between points'''

def generate_vector_file(vector_length):
    p1 = vincenty(vector_length) #10 km
    p2 = p1.destination(initial_point, angle)
