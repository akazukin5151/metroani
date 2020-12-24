import os
import sys

sys.path.append(os.path.abspath('.'))

import metroani


video = metroani.make_video(*metroani.settings_from_json('settings/den_en_toshi.json'))

gif_duration = (1 + 0.7 + 1 + 0.7 + 1) * 2

(video
    .subclip(0, gif_duration)
    .resize(0.5)
    .write_gif('examples/den_en_toshi.gif', fps=24))

os.system('gifsicle -O3 examples/den_en_toshi.gif -o examples/out.gif')
os.system('rm examples/den_en_toshi.gif')
os.system('mv examples/out.gif examples/den_en_toshi.gif')
