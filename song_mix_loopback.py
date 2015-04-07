"""
song_mix_loopback.py

Takes a list of songs, determines the transitions between all consecutive songs, 
and creates a single mp3 file with the given transitions and tempo changes between songs.

If one of the transitions is past the point of the next best transition, the song will
loop back to a point before the transition, and play from there.

The user can specify a transition ratio (how much of the song to look at) and a maximum
number of segments to change tempo.  For the ratio, the number should be between 0.0 and 1.0,
and the number given will be how much of the song to look at from the middle.  For example,
a ratio of 0.5 will look at the middle 1/2 of the song, 25% on each side from the middle.

Created by Jacob Mulford on 04/04/2015

Based on infinitejuke.com and simple stretch (cite this)

Updated on 04/05/2015 to reoder the list of songs to make the transitions more ideal
"""

usage = """
Usage: song_mix_loopback.py [list of mp3 files] transition_ratio segment_tempo_change_limit output_file delay[t/f] compare_tempo[t/f]

Example: song_mix_loopback.py YouCanCallMeAl.mp3 CallMeMaybe.mp3 Celebration.mp3 Beethoven5th.mp3 .5 20 mashup.mp3 t f

This will take the 4 mp3 files, combine them all together at the ideal transitions, and put this
combination into mashup.mp3.  Each song will have up to 20 segments to change tempo, and the middle
50% of each song will be looked at.  The program will delay slightly after each echonest call, and
tempo will not be used in the comparison
"""
from pyechonest import track
from echonest.remix import audio
import twosongshift
import beatshift
import time
def main(mp3_list, transition_ratio, segment_temp_change_limit, output_file, delay, compare_tempo):
    #Reorders mp3_list and generates the transitions
    transitions, mp3_list = generate_transitions(mp3_list, transition_ratio, delay, compare_tempo)

    print mp3_list
    print transitions

    #generate the array of audio quantums
    first_index, _ = transitions[0]
    collects = []
    collects.append(beatshift.tempo_shift(mp3_list[0],(0,first_index),segment_temp_change_limit,mp3_list[1],delay))

    for i in range(1,len(transitions)):
        end_segment, _ = transitions[i]
        _, start_segment = transitions[i-1]

        if (start_segment >= end_segment): #if loopback needed
            loop_trans = generate_loopback(transitions[i-1],transitions[i],mp3_list,i,delay,compare_tempo)
            start_trans, end_trans = loop_trans

            collects.append(song_loopback(start_segment, end_trans, mp3_list[i],delay))

            start_segment = start_trans

        collects.append(beatshift.tempo_shift(mp3_list[i],(start_segment,end_segment),segment_temp_change_limit,mp3_list[i+1],delay))

    _, last_index = transitions[len(transitions)-1]
    last_song = audio.LocalAudioFile(mp3_list[len(mp3_list)-1])

    col_append = []
    for i in range(last_index, len(last_song.analysis.segments)):
        col_append.append(last_song.analysis.segments[i].render())

    collects.append(col_append)

    #write to file
    #the sum(collects, []) takes the list of lists of quantum and converts it
    #to a single list of quantums
    out = audio.assemble(sum(collects, []), numChannels=2)
    out.encode(output_file)

#generates the array of quantum for a song before its
#loopback is needed
def song_loopback(start_segment, end_trans, song_name, delay):
    audiofile = audio.LocalAudioFile(song_name)
    
    if delay:
        print "Waiting 3 seconds"
        time.sleep(3)

    col_append = []
    for i in range(start_segment, end_trans):
        col_append.append(audiofile.analysis.segments[i].render())

    return col_append


#takes a list of mp3 files and a transition ratio, and returns an array of tuples
#containing each ideal transition.  updates the array mp3_list to be in order of
#the ideal transitions between 2 songs
def generate_transitions(mp3_list, transition_ratio, delay, compare_tempo):
    transitions = []
    new_mp3_order = [0] #the first song the user specifies will always play first
    for i in range(0,len(mp3_list)-1):
        best_trans = (-1,-1)
        best_dist = float("inf")
        best_index = -1
        for j in range(0,len(mp3_list)):
            if (not (j in new_mp3_order)) and (j != i):
                (curr_trans_one, curr_trans_two, curr_dist) = twosongshift.get_transition(mp3_list[i],mp3_list[j],transition_ratio,delay,compare_tempo)
                if (curr_dist < best_dist):
                    best_trans = (curr_trans_one, curr_trans_two)
                    best_dist = curr_dist
                    best_index = j

        new_mp3_order.append(best_index)
        transitions.append(best_trans) 
    new_mp3_list = [mp3_list[0]]
    for i in range(1,len(new_mp3_order)):
        new_mp3_list.append(mp3_list[new_mp3_order[i]])

    print new_mp3_order
    return transitions, new_mp3_list

#determines the ideal transition within a song to fit
#the loopback to make the transition between 2 songs possible
def generate_loopback(trans_one, trans_two, mp3_list, index_in_list, delay, compare_tempo):
    _, one_second = trans_one
    two_first, _ = trans_two

    dest_range = range(0,two_first)
    
    t = track.track_from_filename(mp3_list[index_in_list])
    t.get_analysis()

    if delay:
        print "Waiting 3 seconds"
        time.sleep(3)
    
    src_range = range(one_second, len(t.segments))

    best_trans = (0,one_second)
    best_dist = twosongshift.compare_segments(t.segments[0],t.segments[one_second], compare_tempo)

    for i in dest_range:
        for j in src_range:
            if (i != j): #this check may not be necessary
                new_dist = twosongshift.compare_segments(t.segments[i],t.segments[j],compare_tempo)
                if (best_dist > new_dist):
                    best_dist = new_dist
                    best_trans = (i,j)

    return best_trans

if __name__=='__main__':
    import sys
    mp3_list = []
    for i in range(1,len(sys.argv)-5):
        try:
            mp3_list.append(sys.argv[i])
        except:
            print usage
            sys.exit(-1)
    try:
        transition_ratio = float(sys.argv[len(sys.argv)-5])
        change_limit = float(sys.argv[len(sys.argv)-4])
        outfile_name = sys.argv[len(sys.argv)-3]
        delay = (sys.argv[len(sys.argv)-2])
        compare_tempo = (sys.argv[len(sys.argv)-1])
    except:
        print usage
        sys.exit(-1)


    if (not (delay in ["t","f"])) and (not (compare_tempo in ["t","f"])):
        print usage
        sys.exit(-1)

    delay_bool = delay == "t"
    compare_tempo_bool = compare_tempo == "t"

    main(mp3_list,transition_ratio,change_limit,outfile_name, delay_bool, compare_tempo_bool)
