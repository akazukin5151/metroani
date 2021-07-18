'''I hate the python import system'''

import metroani


if __name__ == '__main__':
    # Make animation
    video = metroani.make_video(*metroani.settings_from_json('settings/dev.json'))

    # For development purposes, output only first 10 seconds, or just save first frame
    (video
        .subclip(0, 10)
        #.write_videofile('output/metroani.avi', codec='libx264', fps=60, threads=4))
        .save_frame('output/frame.png'))
