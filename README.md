#Problem to solve

The script song_mix_loopback.py takes a list of songs, reorders them so each song is musically similar to the next one, with transitions at the best transition between the 2 songs.  If a transition to the next song begins at a later point in the song than the best transition from that song to its next, the song will loop back before the transition, and play up to the transition.

There will be 2 implementations for determining the order of songs.  The first one will use an implementations of Prim's algorithm.  The first song in the list will be used as the seed, and the next song to be played will be the one with the most similar transition.  This pattern will continue until all the songs in the list are part of the path.

The second implementation for determining the order of songs will use an implementation of Kruskal's algorithm.  The transitions to take will be put in sorted order, with the best transition appearing first.  Each transition in the array will be added to the playlist until a cycle is made where each song is played once.  If a transition is taken that makes a cycle without including all of the songs, it is thrown out.  The final mp3 file will begin with the first song in the first transition.

#Inspiration

This is the final project for my class Music Informatics.  The final project will be a way to take a list of MP3 files and play them in order with logical transitions.  All the tools to do this have previously been written.  However, the problem at hand is dealing with a transition that begins later in a song than the next transition.  These 2 scripts attempt to solve this problem in the most optimal way.

#song_mix_loopback.py

usage: python song_mix_loopback.py [mp3 list] transition_ratio segment_tempo_change output_file delay[t/f] compare_tempo[t/f] algorithm[p/k]

example: python song_mix_loopback.py house_of_gold.mp3 pompeii.mp3 little_talks.mp3 0.5 20 out.mp3 t t p
###Process

song_mix_loopback.py begins by determining the best transition from song to song.  This is done by comparing all the segments in a song to all the segments in all of the other songs.  The ordering will be based on either Prim's or Kruska'ls algorithm, depending on the user's choice.

Once the song list has been reordered, each audio quantum, that fits the transition range, from each song is added into an array.  This array will be used to create the mp3 file.  For each song, the quantums are added that fall within the range of that song's transition.  When the quantums are approaching the transition peroid, they will begin to slowly change their tempo to match the tempo of the song it transitions to.

If a loopback is needed, all the quantum up to the loopback will be added to the array, and then the quantum following the loopback will continue as normal.

After each song has its quantum added to the array, the array is compressed from a 2d array into a 1d array, and the file is written.

song_mix_loopback.py has the option for the user to toggle on or off a delay.  Due to echonest limiting a user to 20 calls per minute, this delay is necessary if working with moderately large lists (>5).

In addition, tempo comparison can also be toggled on or off.  Tempo is not necessary for comparison due to the tempo shifting aspect, but if a user wants to limit the change in tempo this can be done.
