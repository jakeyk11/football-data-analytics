# %% Imports

import pytube
from moviepy.editor import VideoFileClip

# %% Inputs

# Url of video
link = "https://www.youtube.com/watch?v=1V-LVtI6t2U&ab_channel=SkySportsPremierLeague"

# Save filename
file_name = "output_vid.mp4"

# Start of segment
start = (0,6)

# End of segment
end = (0,12)

# %% Dowload video and save

yt = pytube.YouTube(link)
yt.streams.filter(res="720p").first().download(filename = file_name)

# %% Crop video

clip = VideoFileClip(file_name)
clip1 = clip.subclip(start,end)
clip1.write_videofile(file_name.replace(".mp4", "_cut.mp4"))
