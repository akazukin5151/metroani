import os
import sys

sys.path.append(os.path.abspath('.'))

import metroani


(
    constants, station_settings, terminal_settings, state_settings
) = metroani.all_settings_from_json('settings/yamanote.json')

video = metroani.make_video(
    station_settings, state_settings, terminal_settings,
    constants
)

gif_duration = (1 + 0.7 + 1 + 0.7 + 1) * 2

(video
    .subclip(0, gif_duration)
    .resize(0.5)
    #.save_frame('output/yamanote.png'))
    .write_gif('examples/yamanote.gif', fps=24))

os.system('gifsicle -O3 examples/yamanote.gif -o examples/out.gif')
os.system('rm examples/yamanote.gif')
os.system('mv examples/out.gif examples/yamanote.gif')
