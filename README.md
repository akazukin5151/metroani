# Metroani

Programatically create multilingual train announcement animations, Japan style.

![example](examples/example.gif)

(From `python examples/gif.py`, `python examples/webm.py`)


# Features

- Most essential settings can be customized in a JSON file or through a Python API
- Script itself can be edited for advanced customization
- Four built-in themes
    - `Metro`: Tokyo Metro light theme with line color as accent. Used by Tokyo Metro
    - `Yamanote`: Dark background for station name. Used by newer JR East lines such as the Yamanote and Saikyo Line
    - `JR`: Gray background and older look with more boxes. Used by other JR East lines such as the Keihin-Tohoku and Chuo Line
    - `Tokyu`: Dark background for station name and circles for stations (TODO). Used by Tokyu Lines

# Examples

TODO: examples for each theme


# Usage

1. `git clone https://github.com/twenty5151/metroani`
2. `cd metroani`
3. `pip install -r requirements.txt`
4. (Optional: install `gifsicle` to compress gifs)
5. Start by running the examples and adjusting the settings in `settings/`

Notes:

- Running `python metroani/metroani.py` will create a video using development/debugging settings (which should be avoided). Best to experiment `examples/webm.py` and `settings/gif.json`. See `settings/README.md`
- Python 3.9 was used to develop the script, but Python 3.7 (or later) should be fine (as long as it supports `from __future__ import annotations`).

**TODO: document every setting**

The basic workflow is:

1. Write the settings in either JSON or Python
2. For JSON, use `metroani.all_settings_from_json()` to convert the JSON setting file into Python settings objects
3. For Python, directly instantiate the settings objects. Use `rgb()` to convert 0-255 RGB values to 0-1 values required by gizeh.
4. (Optional: edit the script itself, for advanced users)
5. Pass those settings objects into `metroani.make_video()`, which returns a MoviePy clip
6. (Optional: edit the MoviePy clip however you want)
7. Write the MoviePy clip into a file (see their [manual](https://zulko.github.io/moviepy/ref/VideoClip/VideoClip.html#videoclip))

# License

The code is licensed under the Mozilla Public License v2, but it does not apply to any content. Any content you create with this script is fully owned by you, and you have the full copyright over them.
