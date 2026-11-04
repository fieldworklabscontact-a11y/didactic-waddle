# didactic-waddle

Here is the plan: this repository is for storing data in videos: Here is the projected pipeline: 1. select a video and then a file that you want to store. (COMPLETED 4:17 pm 11/3/26) When the generate button is selected, the file injects itself into the metadata of the mp4 player. the file comes with an additional marker that is specific to the program which it flags and extracts after it is reinserted in the storage app.

To do list:
Find an app that allows for metadata to be seen and its folder partition; make a python script that prompts for this and accesses the appropriate file. (COMPLETED 11/3/26)

Append a new partition in the mp4 file with a specialized meta data marker that the app flags (UPDATE 11/3: I am using webm, storing files at the end of webm video files.)

Add the file into that partition

When a video is added to extract a file it finds the marked partion and copies the file and brings it to the user.

