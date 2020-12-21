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

duration = (1 + 0.7 + 1 + 0.7 + 1) * 2

(video
    .subclip(0, duration)
    .write_videofile('examples/example.webm', codec='libvpx', fps=24, threads=4))
