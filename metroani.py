from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np
import gizeh as gz
import moviepy.editor as mpy
import moviepy.video.fx.all as vfx
from cytoolz import curry, sliding_window


def rgb(values: list[int]) -> list[float]:
    return [x/255 for x in values]


# Functions of time that draws animation frames

def show_text_scaler(t, duration):
    '''Scaling function for text-showing animation'''
    return 0.01 if t == 0 else t / duration

def hide_text_scaler(t, duration):
    '''Scaling function for text-hiding animation'''
    return 1 if t == 0 else 1 - (t / duration)


def make_scale_text_frames(
    t, duration, surface, skip_if_t, scaler_func,
    text, xy, font, fontsize, fontcolor, x_scale,
    center_xy
):
    '''Draws either a text showing or hiding animation'''
    if t != skip_if_t:
        scaler = scaler_func(t, duration)
        new = gz.text(text, font, fontsize, xy=xy, fill=fontcolor)
        new.scale(rx=x_scale, ry=scaler, center=center_xy).draw(surface)


def make_text_frames(
    t, duration, surface, new_text, old_text, xy, new_font, old_font,
    new_fontsize, old_fontsize, fontcolor, old_scale_x, new_scale_x
    , new_center_xy, old_center_xy
):
    '''Draws one text showing animation and one text hiding animation'''
    make_scale_text_frames(
        t, duration, surface, 0, show_text_scaler, new_text, xy, new_font,
        new_fontsize, fontcolor, new_scale_x, new_center_xy
    )
    make_scale_text_frames(
        t, duration, surface, duration, hide_text_scaler, old_text, xy, old_font,
        old_fontsize, fontcolor, old_scale_x, old_center_xy
    )
    return surface


def make_text_frames_from_setting(t, constants, surface, settings, old, new):
    if constants.theme.lower() == 'yamanote':
        color = Yamanote.bg_color
    elif constants.theme.lower() == 'tokyu':
        color = Tokyu.station_color
    # TODO: only change color for station name
    #elif constants.theme.lower() == 'jr':
        #color = JR.station_font_color
    else:
        color = (0,0,0)

    make_text_frames(
        t, constants.duration, surface, new.name, old.name,
        settings.xy, new.font, old.font,
        new.fontsize, old.fontsize, color,
        old.scale_x, new.scale_x, new.enter_xy,
        old.exit_xy
    )
    return surface


def draw_metro_frames(surface, constants):
    # Draw separator line
    gz.polyline(
        [(0, constants.sep_height), (constants.width, constants.sep_height)],
        stroke=Metro.stroke_color, stroke_width=Metro.stroke_width
    ).draw(surface)

    # Draw background for 'next' station text
    gz.rectangle(
        lx=constants.width*2, ly=Metro.rectangle_height,
        xy=[0,0], fill=Metro.rectangle_fill
    ).draw(surface)


def draw_yamanote_frames(surface, constants):
    # Change background color
    gz.rectangle(
        lx=constants.width * 2, ly=constants.height * 2,
        fill=Yamanote.bg_color
    ).draw(surface)

    # Fill station info in the top with background
    gz.rectangle(
        lx=constants.width, ly=constants.sep_height,
        xy=[constants.width/2,constants.sep_height/2],
        fill=Yamanote.rectangle_fill
    ).draw(surface)

    # Add line color indicator
    gz.rectangle(
        lx=Yamanote.indicator_width, ly=constants.sep_height,
        xy=[Yamanote.indicator_pos, constants.sep_height/2],
        fill=constants.line_color
    ).draw(surface)


def draw_jr_frames(surface, constants):
    # Change background color
    gz.rectangle(
        lx=constants.width * 2, ly=constants.height * 2,
        fill=JR.bottom_bg_color
    ).draw(surface)

    # Fill station info in the top with background
    gz.rectangle(
        lx=constants.width, ly=constants.sep_height,
        xy=[constants.width/2,constants.sep_height/2],
        fill=JR.top_bg_color
    ).draw(surface)

    # Fill station text with background
    gz.rectangle(
        lx=constants.width * JR.box_width_mul,
        ly=constants.sep_height * JR.box_height_mul,
        xy=[constants.width/2, constants.sep_height/2 + 50],
        fill=JR.station_bg_color
    ).draw(surface)


def draw_tokyu_frames(surface, constants):
    # Change background color
    gz.rectangle(
        lx=constants.width * 2, ly=constants.height * 2,
        fill=Tokyu.bg_color
    ).draw(surface)

    # Fill station info in the top with background
    gz.rectangle(
        lx=constants.width, ly=constants.sep_height,
        xy=[constants.width/2,constants.sep_height/2],
        fill=Tokyu.rectangle_fill
    ).draw(surface)


def make_bar(surface, constants):
    bar_height = constants.height * 0.05
    bar_width = constants.width * 0.9
    # For text at the bottom and bar in the top,
    # the bottom of the bars is the center of the section
    bar_y = (
        (constants.height - constants.sep_height) / 2
        + constants.sep_height  # center of section
        - bar_height * 2
    )

    triangle_width = constants.width * 0.03
    # bar_x is the center of the bar, but triangle_x is the start of the bar
    bar_x = constants.width/2 - triangle_width/2
    triangle_x = bar_x + bar_width/2 - 1

    # Light bar
    gz.rectangle(
        lx=bar_width, ly=bar_height,
        xy=[bar_x, bar_y],
        fill=constants.line_color
    ).draw(surface)

    # Dark bar
    gz.rectangle(
        lx=bar_width, ly=bar_height,
        xy=[bar_x, bar_y + bar_height],
        fill=constants.line_color_dark
    ).draw(surface)

    # Light triangle
    gz.polyline(
        [
            (triangle_x                 , bar_y - bar_height/2),
            (triangle_x + triangle_width, bar_y + bar_height/2),
            (triangle_x                 , bar_y + bar_height/2),
        ],
        close_path=True, fill=constants.line_color
    ).draw(surface)

    # Dark triangle
    gz.polyline(
        [
            (triangle_x                 , bar_y + bar_height/2),
            (triangle_x + triangle_width, bar_y + bar_height/2),
            (triangle_x                 , bar_y + bar_height*3/2),
        ],
        close_path=True, fill=constants.line_color_dark
    ).draw(surface)

    # Station rectangles
    rect_width = bar_width * 0.07
    edge_padding = constants.width * 0.02
    rect_x = (
        (constants.width - bar_width - triangle_width)/2
        + rect_width/2
        + edge_padding
    )
    max_stations = 8
    max_rect_x = triangle_x - edge_padding - rect_width/2
    spacing = (max_rect_x - rect_x) / (max_stations - 1)

    for n in range(8):
        gz.rectangle(
            lx=rect_width, ly=bar_height*2*0.8,
            fill=[1,1,1, .9],
            xy=[rect_x + spacing * n, bar_y + bar_height/2]
        ).draw(surface)

    # Draw arrow
    arrow_width = spacing / 2 - rect_width/2
    gz.polyline(
        [
            (rect_x + rect_width/2                        , bar_y - bar_height/2),
            (rect_x + rect_width/2 + arrow_width          , bar_y - bar_height/2),
            (rect_x + spacing - rect_width/2              , bar_y + bar_height/2),
            (rect_x + rect_width/2 + arrow_width          , bar_y + bar_height*3/2),
            (rect_x + rect_width/2                        , bar_y + bar_height*3/2),
            (rect_x + spacing - rect_width/2 - arrow_width, bar_y + bar_height/2),
        ],
        close_path=True, stroke=[1,1,1], stroke_width=5, fill=rgb([251, 3, 1])
    ).draw(surface)
    # TODO flash arrow color


@curry
def make_frames(
    t, constants, settings, next_settings, terminal_settings,
    old, new, old_next, new_next, old_term, new_term
):
    '''Returns the frames from the transition of three texts as a function of time'''
    surface = gz.Surface(constants.width, constants.height, bg_color=(1,1,1))

    case = {
        'metro': draw_metro_frames,
        'yamanote': draw_yamanote_frames,
        'jr': draw_jr_frames,
        'tokyu': draw_tokyu_frames,
    }
    if (func := case.get(constants.theme.lower(), None)):
        func(surface, constants)

    make_text_frames_from_setting(
        t, constants, surface, settings,
        old, new
    )

    make_text_frames_from_setting(
        t, constants, surface, next_settings,
        old_next, new_next
    )

    make_text_frames_from_setting(
        t, constants, surface, terminal_settings,
        old_term, new_term
    )

    make_bar(surface, constants)

    return surface.get_npimage()


# Animation functions


def animate(settings, next_settings, terminal_settings, constants):
    '''Animates a transition between two languages'''
    return [
        mpy.VideoClip(
            make_frames(
                constants=constants, settings=settings,
                next_settings=next_settings, terminal_settings=terminal_settings,
                old=names[0], new=names[1], old_next=next_[0], new_next=next_[1],
                old_term=terminal[0], new_term=terminal[1]
            ),
            duration=constants.duration
        )

        for names, next_, terminal in zip(
            settings.names.pairs(), next_settings.names.pairs(),
            terminal_settings.names.pairs()
        )
    ]


def combine_language_transitions(
    station_setting, state_setting, terminal_settings, constants
):
    '''Combines multiple language transitions for a given train state'''
    return mpy.concatenate_videoclips([
        clip.fx(vfx.freeze, t=constants.duration, freeze_duration=1)
            .fx(vfx.freeze, t=0, freeze_duration=1)
        for clip in animate(station_setting, state_setting, terminal_settings, constants)
    ])


def combine_train_states(station_setting, state_settings, terminal_settings, constants):
    '''Combines multiple train states and multiple language transitions'''
    return [
        combine_language_transitions(
            station_setting, state_setting, terminal_settings, constants
        )
        for state_setting in state_settings
    ]


def write_video(
    filename, stations_settings, state_settings, terminal_settings, constants,
    codec='libx264', fps=60
):
    final = []
    for station_setting in station_settings:
        final.append(combine_train_states(
            station_setting, state_settings, terminal_settings, constants
        ))

    flatten = [clip for station_clips in final for clip in station_clips]
    (mpy.concatenate_videoclips(flatten)
        #.write_videofile(filename, codec=codec, fps=fps)
        .save_frame('frame.png'))


# Setting classes
@dataclass
class Constants:
    width: int
    height: int
    duration: float
    sep_height: int
    line_color: tuple[float]
    line_color_dark: tuple[float]
    theme: str  # Metro | Yamanote | JR | Tokyu


@dataclass
class Translation:
    '''Collection of values unique for every language'''
    name: str
    font: str
    fontsize: int
    enter_xy: list[int]
    exit_xy: list[int]
    scale_x: float


@dataclass
class Transition:
    '''
    Represents a collection of translations to transition between,
    and transition-wide settings
    Contains circular-list of the text in every language
    '''
    names: CircularList[Translation]
    xy: list[int]

    @classmethod
    def from_json(cls, settings: 'json', section: str):
        return cls(
            CircularList(
                [Translation(**ss) for ss in settings[section]['translations']]
            ),
            settings[section]['xy'],
        )

    @classmethod
    def from_json_list(cls, settings: 'json', section: str):
        return [
            cls(
                CircularList(
                    [Translation(**ss) for ss in station['translations']]
                ),
                station['xy'],
            )
            for station in settings[section]
        ]


@dataclass(frozen=True)
class CircularList:  # CircularList[T]
    '''Immutable Circular List'''
    it: 'iter[T]'
    head: int = 0

    def curr(self):
        '''Returns the item that the head currently points to'''
        return self.it[self.head]

    def next(self):
        '''Returns a CircularList with head in the next position'''
        if self.head == len(self.it) - 1:
            return CircularList(self.it, 0)
        return CircularList(self.it, self.head + 1)

    def prev(self):
        '''Returns a CircularList with head in the previous position'''
        if self.head <= 0:
            return CircularList(self.it, len(self.it) - 1)
        return CircularList(self.it, self.head - 1)

    def iter(self):
        '''Returns a list of items 'clockwise'/'rightwards',
        including the current item at the end
        '''
        right = self.it[self.head:]
        left = self.it[:self.head]
        return right + left + [self.curr()]

    def pairs(self):
        return sliding_window(2, self.iter())


def all_settings_from_json(file_):
    with open(file_, 'r') as f:
        settings = json.load(f)

    return (
        Constants(**settings['constants']),
        Transition.from_json_list(settings, 'stations'),
        Transition.from_json(settings, 'terminal'),
        [Transition.from_json(settings['states'], key)
         for key in settings['states'].keys()]
    )

# Themes

@dataclass(frozen=True)
class Metro:
    stroke_color = [0, 0, 0]
    stroke_width = 10
    rectangle_height = 220
    rectangle_fill = [0.95, 0.95, 0.95]


@dataclass(frozen=True)
class Yamanote:
    rectangle_fill = [0.26, 0.26, 0.24]
    bg_color = rgb([229, 229, 299])
    indicator_width = 100
    indicator_pos = 470


@dataclass(frozen=True)
class JR:
    top_bg_color = rgb([173, 175, 179])
    bottom_bg_color = rgb([213, 217, 224])
    station_bg_color = rgb([242, 242, 242])
    station_font_color = rgb([24, 135, 72])
    box_width_mul = 2.3 / 4
    box_height_mul = 2.5 / 4


@dataclass(frozen=True)
class Tokyu:
    rectangle_fill = rgb([22, 22, 22])
    bg_color = rgb([233, 235, 239])
    station_color = [1, 1, 1]


if __name__ == '__main__':
    # TODO: skip transition for states and terminal; only station name has hiragana
    (
        constants, station_settings, terminal_settings, state_settings
    ) = all_settings_from_json('short.json')

    # Make animation
    write_video(
        'metroani.avi', station_settings, state_settings, terminal_settings,
        constants
    )
