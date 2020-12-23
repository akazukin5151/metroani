import os
import sys

sys.path.append(os.path.abspath('.'))

import metroani


video = metroani.make_video(*metroani.settings_from_json('settings/keihin.json'))

gif_duration = (1 + 0.7 + 1 + 0.7 + 1) * 2

(video
    .subclip(0, gif_duration)
    .resize(0.5)
    #.save_frame('output/keihin.png'))
    .write_gif('examples/keihin.gif', fps=24))

os.system('gifsicle -O3 examples/keihin.gif -o examples/out.gif')
os.system('rm examples/keihin.gif')
os.system('mv examples/out.gif examples/keihin.gif')
