
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

Based on infinitejuke.com and https://github.com/echonest/remix/blob/master/examples/stretch/simple_stretch.py

Updated on 04/05/2015 to reoder the list of songs to make the transitions more ideal
"""

usage = """
Usage: song_mix_loopback.py [list of mp3 files] transition_ratio segment_tempo_change_limit output_file delay[t/f] compare_tempo[t/f] algorithm[p/k]

Example: song_mix_loopback.py YouCanCallMeAl.mp3 CallMeMaybe.mp3 Celebration.mp3 Beethoven5th.mp3 .5 20 mashup.mp3 t f p

This will take the 4 mp3 files, combine them all together using Prim's algorithm at the ideal transitions, and put this
combination into mashup.mp3.  Each song will have up to 20 segments to change tempo, and the middle
50% of each song will be looked at.  The program will delay slightly after each echonest call, and
tempo will not be used in the comparison
"""
from pyechonest import track
from echonest.remix import audio
import twosongshift
import beatshift
import time
def main(mp3_list, transition_ratio, segment_temp_change_limit, output_file, delay, compare_tempo, algorithm):
    #Reorders mp3_list and generates the transitions
    transitions, mp3_list = generate_transitions(mp3_list, transition_ratio, delay, compare_tempo, algorithm)

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
#the ideal transitions between 2 songs.  uses 2 different algorithms for the transitions
def generate_transitions(mp3_list, transition_ratio, delay, compare_tempo, algorithm):
    if (algorithm == "p"):
        return prims_transitions(mp3_list, transition_ratio, delay, compare_tempo)
    else:
        return kruskals_transitions(mp3_list, transition_ratio, delay, compare_tempo)

#prim's algorithm for the song transition
def prims_transitions(mp3_list, transition_ratio, delay, compare_tempo):
    weight = 0.0
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
        weight = weight + curr_dist
        transitions.append(best_trans)

    new_mp3_list = [mp3_list[0]]
    for i in range(1,len(new_mp3_order)):
        new_mp3_list.append(mp3_list[new_mp3_order[i]])

    print weight

    return transitions, new_mp3_list

#kruskal's algorithm for the song transition
def kruskals_transitions(mp3_list, transition_ratio, delay, compare_tempo):
    weight = 0.0

    all_transitions = []

    #generate all the transitions, store in all_transitions
    #the array will hold 2 tuples with a total of 5 values, so that the
    #tuple x will be (song_1, song_2, (segment_1, segment_2, distance))
    for i in range(0,len(mp3_list)-1):
        for j in range(i+1,len(mp3_list)):
            all_transitions.append((i,j,(twosongshift.get_transition(mp3_list[i],mp3_list[j],transition_ratio,delay,compare_tempo))))

    #sort all_transitions based on the distance
    all_transitions = sort_by_distance(all_transitions)

    #for each transition, add it to the list if and only if
    #it doesn't make a cycle without all the nodes
    map_order = []


    for curr_trans in all_transitions:
        (song_1, song_2, (_,_,_)) = curr_trans
        if not makes_incomplete_cycle(map_order, (song_1, song_2), len(mp3_list)):
            map_order.append(curr_trans)
        if len(map_order) == len(mp3_list): #if the map is completed
            break

    #drop the last added transition
    #the songs in this transition become the
    #start and end songs of the final list
    last_trans = map_order.pop()

    #reorder map_order so the transitions
    #come in the order to be played
    (first_song,last_song,(_,_,_)) = last_trans
    map_order = reorder_map(map_order, first_song, last_song)
    #populate new_mp3_order and transitions so
    #these can be used in main.  the mp3 order is
    #seeded with the first song in last_trans
    new_mp3_order = [first_song]
    transitions = []

    for connection in map_order:
        (_,song,segs) = connection
        (seg_1,seg_2,seg_weight) = segs
        weight = weight + seg_weight
        new_mp3_order.append(song)
        transitions.append((seg_1,seg_2))

    new_mp3_list = [mp3_list[new_mp3_order[0]]]
    for i in range(1,len(new_mp3_order)):
        new_mp3_list.append(mp3_list[new_mp3_order[i]])

    print weight

    return transitions, new_mp3_list

#reorders the map so the transitions are made in order
#the final map needs to be structured so transition (a,b)
#goes from song a to song b
def reorder_map(map_order, first_song, last_song):
    new_order = []
    prev_song = first_song

    for i in range(0,len(map_order)):
        for map_value in map_order:
            if map_value not in new_order:

                (song_1, song_2, _) = map_value
                if (song_1 == prev_song or song_2 == prev_song):
                    if song_2 == prev_song:
                        prev_song = song_1
                        map_value = flip_values(map_value)
                    else:
                        prev_song = song_2
                    new_order.append(map_value)
                    if prev_song == last_song:
                        return new_order
                
    return new_order 

#flips the values in the tuple if the songs
#aren't in the desired order
def flip_values(map_value):
    (song_1, song_2, (seg_1, seg_2, distance)) = map_value
    return (song_2, song_1, (seg_2, seg_1, distance))

#determines if the transition will make an incomplete cycle
#uses the current map, the transition to add, and how many
#nodes should be in the full map
def makes_incomplete_cycle(map, transition, node_count):
    all_trans = []
    
    for map_index in map:
        (song_1, song_2, _) = map_index
        all_trans.append((song_1,song_2))

    (song_1, song_2) = transition

    #1st step: make sure no node is visited more than 2 times
    visited_node_count = [0] * node_count
    visited_node_count[song_1] = 1
    visited_node_count[song_2] = 1
    
    for trans in all_trans:
        (song_1, song_2) = trans
        visited_node_count[song_1] = visited_node_count[song_1] + 1
        visited_node_count[song_2] = visited_node_count[song_2] + 1

    for count in visited_node_count:
        if count > 2:
            return True

    #2nd step: make sure the added connection doesn't make an
    #incompleted cycle
    
    visited_node_count = [0] * node_count
    (first_song, _) = transition
    (prev_song, curr_song) = transition

    visited_node_count[prev_song] = 1
    while True:
        next_song = next_transition(all_trans, prev_song, curr_song)
        
        if next_song == -1: #the path has reached a dead end
            return False #can't make an incomplete cycle if the path ends

        prev_song = curr_song
        curr_song = next_song

        visited_node_count[prev_song] = visited_node_count[prev_song] + 1

        if curr_song == first_song: #possibly reaching the full cycle
            if 0 not in visited_node_count: #all the nodes need to be visited
                return False #the cycle is completed
            else:
                return True #went back to start before visiting all nodes

        if visited_node_count[curr_song] > 0:
            return True #found a node that has been seen before, incompleted cycle

#determines the next transition in the map with the given
#previous and current songs
def next_transition(map, prev_song, curr_song):
    for i in range(0,len(map)):
        (song_1, song_2) = map[i]

        if curr_song in [song_1,song_2] and prev_song not in [song_1,song_2]:
            if curr_song == song_1:
                return song_2
            else:
                return song_1
    return -1 #no song found
    
#sorting function to sort the transitions by distance
#uses merge sort
def sort_by_distance(transitions):
    if transitions == [] or len(transitions) == 1:
        return transitions
    
    mid = len(transitions)/2
    first_half = sort_by_distance(transitions[0:mid])
    second_half = sort_by_distance(transitions[mid:len(transitions)])

    return merge_by_distance(first_half,second_half)
    
#helper function for sort_by_distance
def merge_by_distance(first_half, second_half):
    new_array = []

    i = 0
    j = 0

    while (i < len(first_half)) and (j < len(second_half)):
        (_,_,(_,_,first_distance)) = first_half[i]
        (_,_,(_,_,second_distance)) = second_half[j]

        if (first_distance < second_distance):
            new_array.append(first_half[i])
            i = i + 1
        else:
            new_array.append(second_half[j])
            j = j + 1
    while (i < len(first_half)):
        new_array.append(first_half[i])
        i = i + 1
    while (j < len(second_half)):
        new_array.append(second_half[j])
        j = j + 1

    return new_array
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
    for i in range(1,len(sys.argv)-6):
        try:
            mp3_list.append(sys.argv[i])
        except:
            print usage
            sys.exit(-1)
    try:
        transition_ratio = float(sys.argv[len(sys.argv)-6])
        change_limit = float(sys.argv[len(sys.argv)-5])
        outfile_name = sys.argv[len(sys.argv)-4]
        delay = (sys.argv[len(sys.argv)-3])
        compare_tempo = (sys.argv[len(sys.argv)-2])
        algorithm = (sys.argv[len(sys.argv)-1])
    except:
        print usage
        sys.exit(-1)


    if (not (delay in ["t","f"])) and (not (compare_tempo in ["t","f"])) and (not (algorithm in ["p","k"])):
        print usage
        sys.exit(-1)

    delay_bool = delay == "t"
    compare_tempo_bool = compare_tempo == "t"

    main(mp3_list,transition_ratio,change_limit,outfile_name, delay_bool, compare_tempo_bool, algorithm)
