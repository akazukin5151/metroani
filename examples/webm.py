import os
import sys

sys.path.append(os.path.abspath('.'))

import metroani


(
    constants, station_settings, terminal_settings, state_settings
) = metroani.all_settings_from_json('settings/gif.json')

video = metroani.make_video(
    station_settings, state_settings, terminal_settings,
    constants
)

gif_duration = (1 + 0.7 + 1 + 0.7 + 1) * 2

(video
    .subclip(0, gif_duration)
    .write_videofile('output/metroani.webm', codec='libvpx', fps=24, threads=4))
