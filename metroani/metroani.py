from __future__ import annotations

import json
from typing import NamedTuple
from collections import namedtuple

import numpy as np
import gizeh as gz
import moviepy.editor as mpy
import moviepy.video.fx.all as vfx
from cytoolz import curry, sliding_window


def rgb(values: list[int]) -> list[float]:
    return [x/255 for x in values]


# Functions of time that draws animation frames
def thresholdify_inc(pivot, pivot_value):
    '''
    Given an increasing linear function of t, f(t, d), return a new
    function g such that:
    1) g(t, d) = pivot_value when t <= pivot
    2) g(d, d) = f(d, d)
    '''
    def wrapper(f: 'func[T, T] -> T') -> 'func[T, T] -> T':
        def g(t, d):
            if t <= pivot:
                return pivot_value
            x1 = pivot
            x2 = d
            y1 = pivot_value
            y2 = f(x2, d)
            gradient = (y2 - y1) / (x2 - x1)
            c = y2 - gradient*x2
            return gradient*t + c
        return g
    return wrapper


def thresholdify_dec(pivot, pivot_value):
    '''
    Given a decreasing linear function of t, f(t, d), return a new
    function g such that:
    1) g(t, d) = pivot_value when t >= d - pivot
    2) g(0, d) = f(0, d)
    '''
    def wrapper(f: 'func[T, T] -> T') -> 'func[T, T] -> T':
        def g(t, d):
            if t >= d - pivot:
                return pivot_value
            x1 = 0
            x2 = d - pivot
            y1 = f(x1, d)
            y2 = pivot_value
            gradient = (y2 - y1) / (x2 - x1)
            c = y2 - gradient*x2
            return gradient*t + c
        return g
    return wrapper


@thresholdify_inc(pivot=0.1, pivot_value=0.01)
def show_text_scaler(t, duration):
    '''Scaling function for text-showing animation; Piecewise looks like _/
    Scale ranges from 0 to 1
    '''
    return t / duration


@thresholdify_dec(pivot=0.1, pivot_value=0.01)
def hide_text_scaler(t, duration):
    '''Scaling function for text-hiding animation; Piecewise looks like \_
    Scale ranges from 0 to 1
    '''
    return 1 - (t / duration)


@thresholdify_inc(pivot=0.1, pivot_value=0.01)
def show_text_alpha(t, duration):
    '''Piecewise function that looks like _/'''
    return 2 * t


@thresholdify_dec(pivot=0.1, pivot_value=0.01)
def hide_text_alpha(t, duration):
    '''Piecewise function that looks like \_'''
    return -2*t + 2*duration


def make_scale_text_frames(
    t, duration, surface, skip_if_t, scaler_func,
    text, xy, font, fontsize, fontcolor, x_scale,
    center_xy, alpha_func
):
    '''Draws either a text showing or hiding animation'''
    if t != skip_if_t:
        color = list(fontcolor) + [alpha_func(t, duration)]
        scaler = scaler_func(t, duration)
        new = gz.text(text, font, fontsize, xy=xy, fill=color)
        new.scale(rx=x_scale, ry=scaler, center=center_xy).draw(surface)
    return surface


def make_show_text_frames(
    t, duration, surface, new_text, xy, new_font, new_fontsize,
    fontcolor, new_scale_x, new_center_xy
):
    return make_scale_text_frames(
        t, duration, surface, 0, show_text_scaler, new_text, xy, new_font,
        new_fontsize, fontcolor, new_scale_x, new_center_xy, show_text_alpha
    )


def make_hide_text_frames(
    t, duration, surface, old_text, xy, old_font, old_fontsize, fontcolor,
    old_scale_x, old_center_xy
):
    return make_scale_text_frames(
        t, duration, surface, duration, hide_text_scaler, old_text, xy, old_font,
        old_fontsize, fontcolor, old_scale_x, old_center_xy, hide_text_alpha
    )


def make_text_frames(
    t, duration, surface, new_text, old_text, xy, new_font, old_font,
    new_fontsize, old_fontsize, fontcolor, old_scale_x, new_scale_x
    , new_center_xy, old_center_xy
):
    '''Draws one text showing animation and one text hiding animation'''
    # If both texts are the same, no animation is needed
    if new_text == old_text:
        return make_hide_text_frames(
            0, duration, surface, old_text, xy, old_font, old_fontsize, fontcolor,
            old_scale_x, old_center_xy
        )

    make_show_text_frames(
        t, duration, surface, new_text, xy, new_font, new_fontsize,
        fontcolor, new_scale_x, new_center_xy
    )

    make_hide_text_frames(
        t, duration, surface, old_text, xy, old_font, old_fontsize, fontcolor,
        old_scale_x, old_center_xy
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


def make_vertical_text(text, surface, first_xy, spacing, **kwargs):
    for idx, letter in enumerate(text):
        gz.text(
            letter, xy=[first_xy[0], first_xy[1] + spacing*idx], **kwargs
        ).draw(surface)


def make_bar(surface, constants, bar_width, bar_height, bar_x, bar_y):
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


def make_triangles(surface, constants, triangle_x, triangle_width, bar_y,
                   bar_height):
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


def make_station_info(surface, settings_to_show, rect_width, bar_height,
                      rect_x, spacing, bar_y, section_center, constants):
    if constants.theme.lower() == 'tokyu':
        func = gz.circle
        args = {'r': bar_height*0.9}
    else:
        func = gz.rectangle
        args = {'lx': rect_width, 'ly': bar_height*2*0.8}

    for n, setting in zip(range(8), settings_to_show):
        x_pos = rect_x + spacing * n
        color = (.5, .5, .5) if setting.skip else (0, 0, 0)
        arrow_x_pos = x_pos - 15
        arrow_width = 5

        # Station rectangles/circles
        if setting.skip:
            gz.polyline(
                [
                    (arrow_x_pos - arrow_width, bar_y - 5),
                    (arrow_x_pos + arrow_width, bar_y - 5),
                    (arrow_x_pos + 7*arrow_width, bar_y + 30),
                    (arrow_x_pos + arrow_width, bar_y + 65),
                    (arrow_x_pos - arrow_width, bar_y + 65),
                    (arrow_x_pos + 5*arrow_width, bar_y + 30),
                ],
                stroke=[1,1,1], stroke_width=5,
                fill=[1,1,1], close_path=True
            ).draw(surface)
        else:
            func(
                fill=[1,1,1,0.9],
                xy=[x_pos, bar_y + bar_height/2],
                **args
            ).draw(surface)

        # Station numbers
        gz.text(
            setting.station_number, 'Roboto', 50,
            xy=[x_pos, section_center - 40],
            fill=color
        ).draw(surface)

        # Station names
        # TODO: font, fontsize, change language, option to rotate instead
        make_vertical_text(
            setting.names.curr().name, surface,
            first_xy=[x_pos, section_center + 40],
            spacing=70, fontfamily='Hiragino Sans GB W3', fontsize=70,
            fill=color
        )

        # Display every transfer line for every station in its first language
        for idx, transfer in enumerate(setting.transfers):
            y_pos = (bar_y - bar_height) + 10 - idx*40
            # TODO: Transition between different translations
            current_translation = transfer[0]

            gz.text(
                current_translation.name,
                fontfamily=current_translation.font,
                fontsize=current_translation.fontsize,
                xy=[x_pos, y_pos],
                fill=color
            ).scale(
                rx=current_translation.scale_x,
                ry=1,
                center=[x_pos, y_pos]
            ).draw(surface)


def make_seperator(surface, constants, section_center):
    gz.polyline(
        [(0, section_center),(constants.width, section_center)],
        stroke=constants.line_color, stroke_width=8
    ).draw(surface)


def make_arrow(surface, spacing, rect_width, arrow_x_offset, rect_x, bar_y,
               bar_height):
    arrow_width = spacing / 2 - rect_width/2
    points = [
        (
            arrow_x_offset + rect_x + rect_width/2,
            bar_y - bar_height/2
        ),
        (
            arrow_x_offset + rect_x + rect_width/2 + arrow_width,
            bar_y - bar_height/2
        ),
        (
            arrow_x_offset + rect_x + spacing - rect_width/2,
            bar_y + bar_height/2
        ),
        (
            arrow_x_offset + rect_x + rect_width/2 + arrow_width,
            bar_y + bar_height*3/2
        ),
        (
            arrow_x_offset + rect_x + rect_width/2,
            bar_y + bar_height*3/2
        ),
        (
            arrow_x_offset + rect_x + spacing - rect_width/2 - arrow_width,
            bar_y + bar_height/2
        ),
    ]
    gz.polyline(
        points,close_path=True, stroke=[1,1,1], stroke_width=5,
        fill=rgb([251, 3, 1])
    ).draw(surface)
    # TODO flash arrow color


def make_line_info(surface, constants, settings, station_idx):
    # Set values
    # Fundamental constants
    max_stations = 8
    number_of_stations = len(settings)
    remaining_stations = number_of_stations - station_idx
    section_center = (
        (constants.height - constants.sep_height) / 2
        + constants.sep_height
    )

    # Bar settings
    bar_height = constants.height * 0.05
    bar_width = constants.width * 0.955
    bar_x = bar_width/2
    # The bottom of the bars is slightly above the center of the section
    bar_y = (
        section_center - bar_height * 2
        - 40  # Approx fontheight/2
    )

    # Triangle settings
    triangle_width = constants.width * 0.03
    # bar_x is the center of the bar, but triangle_x is the start of the bar
    triangle_x = bar_x + bar_width/2 - 1

    # Rectangle settings
    rect_width = bar_width * 0.06
    edge_padding = constants.width * 0.05
    rect_x = (
        (constants.width - bar_width - triangle_width)/2
        + rect_width/2
        + edge_padding
    )
    max_rect_x = triangle_x - edge_padding - rect_width/2
    spacing = (max_rect_x - rect_x) / (max_stations - 1)

    # Arrow and station slice settings
    arrow_x_offset = 0

    if remaining_stations <= max_stations - 2:
        # End of the line: show all 8 stations from the last
        settings_to_show = settings[-max_stations:]
        # Move arrow to between next rectangle
        arrow_x_offset = spacing * (max_stations - 1 - remaining_stations)
    elif station_idx == 0:
        # 1st -> 2nd station: show 1st station as 'previous'
        settings_to_show = settings[station_idx:station_idx + max_stations]
        # Move arrow to center of first rectangle
        arrow_x_offset = - spacing/2
    else:
        # Anywhere else in the line: show previous station
        settings_to_show = settings[station_idx-1:station_idx + max_stations - 1]

    # Actually draw the frame
    make_bar(surface, constants, bar_width, bar_height, bar_x, bar_y)

    if remaining_stations > max_stations - 1:
        make_triangles(
            surface, constants, triangle_x, triangle_width, bar_y,
            bar_height
        )

    make_station_info(
        surface, settings_to_show, rect_width, bar_height, rect_x,
        spacing, bar_y, section_center, constants
    )

    make_seperator(surface, constants, section_center)

    make_arrow(
        surface, spacing, rect_width, arrow_x_offset, rect_x, bar_y, bar_height
    )


def make_station_icon(surface, settings, n, constants):
    x_pos, y_pos = constants.icon_xy

    if constants.icon_shape.lower() == 'square':
        mod = 40
        gz.square(
            constants.icon_size,
            xy=[x_pos, y_pos],
            stroke=constants.line_color,
            stroke_width=15,
            fill=[1,1,1]
        ).draw(surface)
    else:
        mod = 45
        gz.circle(
            constants.icon_size,
            xy=[x_pos, y_pos],
            stroke=constants.line_color,
            stroke_width=30,
            fill=[1,1,1]
        ).draw(surface)

    line, num = settings[n].station_number.split('-')
    gz.text(
        line, constants.icon_text_font,
        constants.icon_line_fontsize, xy=[x_pos, y_pos-mod]
    ).draw(surface)
    gz.text(
        num, constants.icon_text_font,
        constants.icon_station_fontsize, xy=[x_pos, y_pos+30]
    ).draw(surface)


@curry
def make_frames(
    t, constants, n, settings, next_settings, terminal_settings,
    old, new, old_next, new_next, old_term, new_term
):
    '''Returns the frames from the transition of three texts as a function of time'''
    surface = gz.Surface(constants.width, constants.height, bg_color=(1,1,1))

    # Apply theme
    case = {
        'metro': draw_metro_frames,
        'yamanote': draw_yamanote_frames,
        'jr': draw_jr_frames,
        'tokyu': draw_tokyu_frames,
    }
    if (func := case.get(constants.theme.lower(), None)):
        func(surface, constants)

    # Station text
    make_text_frames_from_setting(
        t, constants, surface, settings[n],
        old, new
    )

    # 'Next' text
    make_text_frames_from_setting(
        t, constants, surface, next_settings,
        old_next, new_next
    )

    # Terminus station text
    make_text_frames_from_setting(
        t, constants, surface, terminal_settings,
        old_term, new_term
    )

    # Line info graphics
    make_line_info(surface, constants, settings, n)

    # Station icon
    make_station_icon(surface, settings, n, constants)

    return surface.get_npimage()


# Animation functions


def animate(n, settings, next_settings, terminal_settings, constants):
    '''Animates a transition between two languages'''
    return (
        mpy.VideoClip(
            make_frames(
                constants=constants, n=n, settings=settings,
                next_settings=next_settings, terminal_settings=terminal_settings,
                old=names[0], new=names[1], old_next=next_[0], new_next=next_[1],
                old_term=terminal[0], new_term=terminal[1]
            ),
            duration=constants.duration
        )

        for names, next_, terminal in zip(
            settings[n].names.pairs(), next_settings.names.pairs(),
            terminal_settings.names.pairs()
        )
        if any([not settings[n].skip for name in names])
    )


def freeze_end(clip, constants):
    return clip.fx(
        vfx.freeze, t=constants.duration,
        freeze_duration=constants.freeze_duration
    )


def freeze_both(clip, constants):
    return freeze_end(clip, constants).fx(
        vfx.freeze, t=0, freeze_duration=constants.freeze_duration
    )


def freeze(idx, clip, constants):
    if idx % 2 != 0:
        return freeze_end(clip, constants)
    return freeze_both(clip, constants)


def concat_or_skip(clips):
    if clips:
        return mpy.concatenate_videoclips(clips)
    return None


def combine_language_transitions(
    n, station_settings, state_setting, terminal_settings, constants
):
    '''Combines multiple language transitions for a given train state'''
    return concat_or_skip([
        freeze(idx, clip, constants)
        for idx, clip in enumerate(animate(
            n, station_settings, state_setting, terminal_settings, constants
        ))
    ])


def combine_train_states(
    n, station_settings, state_settings, terminal_settings, constants
):
    '''Combines multiple train states and multiple language transitions'''
    return (
        combine_language_transitions(
            n, station_settings, state_setting, terminal_settings, constants
        )
        for state_setting in state_settings
    )


def make_video(
    station_settings, state_settings, terminal_settings, constants,
):
    final = (
        combine_train_states(
            n, station_settings, state_settings, terminal_settings, constants
        )
        for n in range(len(station_settings))
    )

    return mpy.concatenate_videoclips([
        clip
        for station_clips in final
        for clip in station_clips
        if clip is not None
    ])



# Setting classes
class Constants(NamedTuple):
    width: int
    height: int
    duration: float
    freeze_duration: float
    sep_height: int
    line_color: tuple[float]
    line_color_dark: tuple[float]
    theme: str  # Metro | Yamanote | JR | Tokyu
    icon_shape: str  # circle | square
    icon_size: int
    icon_xy: tuple[int]
    icon_text_font: str
    icon_line_fontsize: int
    icon_station_fontsize: int


#class AbstractTranslation(NamedTuple):
#    '''Not used in runtime'''
#    name: str
#    font: str
#    fontsize: int
#    scale_x: float


class LineTranslation(NamedTuple):
    '''Collection of values unique for every language, for lines'''
    # 'Inherit' from AbstractTranslation
    name: str
    font: str
    fontsize: int
    scale_x: float


class StationTranslation(NamedTuple):
    '''Collection of values unique for every language, for stations'''
    # 'Inherit' from LineTranslation
    name: str
    font: str
    fontsize: int
    scale_x: float
    # New
    enter_xy: list[int]
    exit_xy: list[int]


class Translation(NamedTuple):
    '''Collection of values unique for every language, for terminal and next'''
    # 'Inherit' from AbstractTranslation
    name: str
    font: str
    fontsize: int
    scale_x: float
    # New
    enter_xy: list[int]
    exit_xy: list[int]


class Transition(NamedTuple):
    '''Transition-wide settings for terminal and state settings
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
            settings[section]['xy']
        )


class StationTransition(NamedTuple):
    '''Transition-wide settings for station settings
    Contains circular-list of the text in every language
    '''
    names: CircularList[StationTranslation]
    xy: list[int]
    station_number: str
    # Inner list is same line in different languages
    # Outer list is collection of different lines
    transfers: list[list[LineTranslation]]
    skip: bool

    @classmethod
    def from_json_list(cls, settings: 'json', section: str):
        return [
            cls(
                CircularList(
                    [StationTranslation(**ss) for ss in station['translations']]
                ),
                station['xy'],
                station['station_number'],
                [
                    [LineTranslation(**translation) for translation in line]
                    for line in station['transfers']
                ],
                station['skip'],
            )
            for station in settings[section]
        ]


class CircularList(NamedTuple):  # CircularList[T]
    '''Immutable Circular List'''
    it: 'list[T]'
    head: int = 0

    def curr(self):
        '''Returns the item that the head currently points to'''
        return self.it[self.head]

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
        StationTransition.from_json_list(settings, 'stations'),
        Transition.from_json(settings, 'terminal'),
        [Transition.from_json(settings['states'], key)
         for key in settings['states'].keys()]
    )

# Themes

class Metro(NamedTuple):
    stroke_color = [0, 0, 0]
    stroke_width = 10
    rectangle_height = 220
    rectangle_fill = [0.95, 0.95, 0.95]


class Yamanote(NamedTuple):
    rectangle_fill = rgb([26, 26, 24])
    bg_color = rgb([229, 229, 229])
    indicator_width = 100
    indicator_pos = 470


class JR(NamedTuple):
    top_bg_color = rgb([173, 175, 179])
    bottom_bg_color = rgb([213, 217, 224])
    station_bg_color = rgb([242, 242, 242])
    station_font_color = rgb([24, 135, 72])
    box_width_mul = 2.3 / 4
    box_height_mul = 2.5 / 4


class Tokyu(NamedTuple):
    rectangle_fill = rgb([22, 22, 22])
    bg_color = rgb([233, 235, 239])
    station_color = [1, 1, 1]


if __name__ == '__main__':
    (
        constants, station_settings, terminal_settings, state_settings
    ) = all_settings_from_json('settings/dev.json')

    # Make animation
    video = make_video(
        station_settings, state_settings, terminal_settings,
        constants
    )

    # For development purposes, output only first 10 seconds, or just save first frame
    (video
        .subclip(0, 10)
        #.write_videofile('output/metroani.avi', codec='libx264', fps=60, threads=4))
        .save_frame('output/frame.png'))
