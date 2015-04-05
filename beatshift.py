"""
beatshift.py

Shifts the beat of a file over a given period of time by a given magnitude at the given interval

Created by Jacob Mulford on 2/18/2015

Based on https://github.com/echonest/remix/blob/master/examples/stretch/simple_stretch.py

Updated on 04/04/2015 to be a method called by another script
"""
import dirac
from echonest.remix import audio
from pyechonest import track

usage = """
Usage: python beatshift.py <input_filename> <start_beat> <shift_length> <shift_magnitude> <output_filename>

Example: python beatshift.py CallMeMaybe.mp3 10 50 -10 CallMeShift.mp3

This will shift the tempo of CallMeMaybe.mp3 by -10 bpm over 50 beats starting at beat 10.
"""

def tempo_shift(input_filename, seg_range, shift_length, second_song):
    t1 = track.track_from_filename(input_filename)
    t2 = track.track_from_filename(second_song)

    start_range, end_range = seg_range

    shift_length = min(shift_length, end_range - start_range)
    shift_magnitude = t2.tempo - t1.tempo

    beat_increment = (1.0*shift_magnitude)/shift_length
    beat_ratio = 1.0
    beat_count = 0

    audiofile = audio.LocalAudioFile(input_filename)
    beats = audiofile.analysis.segments
    collect = []

    for i in range(start_range, end_range):
        if (i > (end_range - shift_length)):
            desired_bpm = beat_increment * (i - (end_range - shift_length)) + t1.tempo
            beat_ratio = t1.tempo/desired_bpm

        beat_audio = beats[i].render()

        if (beat_ratio == 1.0):
            collect.append(beat_audio)
        else:
            scaled_beat = dirac.timeScale(beat_audio.data, beat_ratio)
            ts = audio.AudioData(ndarray=scaled_beat, shape=scaled_beat.shape,
                    sampleRate=audiofile.sampleRate, numChannels=scaled_beat.shape[1])
            collect.append(ts)
    
    print "Waiting 9 seconds"
    time.sleep(9)

    return collect

