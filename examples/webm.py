import os
import sys

sys.path.append(os.path.abspath('.'))

import metroani


video = metroani.make_video(*metroani.all_settings_from_json('settings/gif.json'))

duration = (1 + 0.7 + 1 + 0.7 + 1) * 2

(video
    .subclip(0, duration)
    .write_videofile('examples/example.webm', codec='libvpx', fps=24, threads=4))
