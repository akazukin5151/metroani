# Example JSON settings

## gif.json

The Seibu-Shinjuku line from Saginomiya to Seibu-Shinjuku, with a 1-second freeze duration and one train state (next). Best for learning/experimenting/tinkering with. Used to generate the header gif in the README

## full.json

The Seibu-Shinjuku line from Saginomiya to Seibu-Shinjuku, with a 2-second freeze duration and three train states (next, arriving, currently). Takes a long time to render the full video.

## dev.json

The Seibu-Shinjuku line from Saginomiya to Seibu-Shinjuku, with a 1-second freeze duration and one train state (next). May change at any time; for development and debugging purposes, do not rely on this. Running `python metroani/metroani.py` will create a video with this setting.
