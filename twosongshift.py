"""
twosongshift.py

Takes 2 songs and determines the ideal transition between them if tempo is ignored.

Created by Jacob Mulford on 3/01/2015

Based on infinitejuke.com

This script was altered on 04/04/2015 to be called by another class, and returns the ideal transition instead of writing it to a file
"""
import math
import sys
import pyechonest.track as track

usage = """
Usage: python twosongshift.py <first_filename> <second_filename> <ratio> <output_file>

Example: python twosongshift.py CallMeMaybe.mp3 ShakeItOff.mp3 .33 Transitions.txt

This will determine the transitions between the segments .33 of each side from the middle of CallMeMaybe.mp3 and ShakeItOff.mp3, and will put the
best transition into Transitions.txt.  Transitions.txt will hold 2 integers.
The first integer will be the segment in CallMeMaybe.mp3, and the second integer will be the
segment in ShakeItOff.mp3.
"""

#replaced main
def get_transition(first_filename, second_filename, ratio):
    #set up the 2 files for analysis
    track_one = track.track_from_filename(first_filename)
    track_one.get_analysis()

    track_two = track.track_from_filename(second_filename)
    track_two.get_analysis()

    if (ratio > 1.0 or ratio < 0.0):
        print "Error: ratio must be between 0.0 and 1.0"
        sys.exit(-1)

    first_middle = len(track_one.segments)/2
    second_middle = len(track_two.segments)/2

    first_start = int(first_middle - (first_middle * ratio))
    first_end = int(first_middle + (first_middle * ratio))

    second_start = int(second_middle - (second_middle * ratio))
    second_end = int(second_middle + (second_middle * ratio))

    #compare each segment in the first file to each segment in the second file
    comparisons = []
    for i in range(first_start,first_end):
        appender = []
        for j in range(second_start,second_end):
            compare = compare_segments(track_one.segments[i],track_two.segments[j])
            appender.append(compare)
        comparisons.append(appender)

    (first_low,second_low) = (0,0)

    for i in range(0,len(comparisons)):
        for j in range(0,len(comparisons[i])):
            if comparisons[i][j] < comparisons[first_low][second_low]:
                first_low = i
                second_low = j

    print "Waiting 6 seconds"
    time.sleep(6)

    return (first_low+first_start,second_low+second_start)

#determines the weighted Euclidean distance between 2 segments
def compare_segments(seg_one, seg_two):
    timbre_distance = euc_dist(seg_one['timbre'],seg_two['timbre'])
    pitch_distance = euc_dist(seg_one['pitches'],seg_two['pitches'])
    loud_distance = (seg_one['loudness_start'] - seg_two['loudness_start'])**2
    return timbre_distance + 10*pitch_distance + loud_distance

#calculates euclidean distance
def euc_dist(arr_one,arr_two):
    sum = 0
    for i in range(0,min(len(arr_one),len(arr_two))):
        sum = sum + (arr_one[i] - arr_two[i])**2
    return math.sqrt(sum)

