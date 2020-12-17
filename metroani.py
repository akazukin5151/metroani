from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np
import gizeh as gz
import moviepy.editor as mpy
import moviepy.video.fx.all as vfx
from cytoolz import curry, sliding_window


# Functions of time that draws animation frames

def show_text_scaler(t, duration):
    '''Scaling function for text-showing animation'''
    return 0.01 if t == 0 else t / duration

def hide_text_scaler(t, duration):
    '''Scaling function for text-hiding animation'''
    return 1 if t == 0 else 1 - (t / duration)


def make_scale_text_frames(
    t, duration, surface, skip_if_t, scaler_func,
    text, xy, font, fontsize, x_scale,
    center_xy
):
    '''Draws either a text showing or hiding animation'''
    if t != skip_if_t:
        scaler = scaler_func(t, duration)
        new = gz.text(text, font, fontsize, xy=xy)
        new.scale(rx=x_scale, ry=scaler, center=center_xy).draw(surface)


def make_text_frames(
    t, duration, surface, new_text, old_text, xy, new_font, old_font,
    new_fontsize, old_fontsize, old_scale_x, new_scale_x
    , new_center_xy, old_center_xy
):
    '''Draws one text showing animation and one text hiding animation'''
    make_scale_text_frames(
        t, duration, surface, 0, show_text_scaler, new_text, xy, new_font,
        new_fontsize, new_scale_x, new_center_xy
    )
    make_scale_text_frames(
        t, duration, surface, duration, hide_text_scaler, old_text, xy, old_font,
        old_fontsize, old_scale_x, old_center_xy
    )
    return surface


def make_text_frames_from_setting(t, constants, surface, settings, old, new):
    make_text_frames(
        t, constants.duration, surface, new.name, old.name,
        settings.xy, new.font, old.font,
        new.fontsize, old.fontsize,
        old.scale_x, new.scale_x, new.enter_xy,
        old.exit_xy
    )
    return surface


def make_line_frames(surface, constants):
    gz.polyline(
        [(0, constants.sep_height), (constants.width, constants.sep_height)],
        stroke=Metro.stroke_color, stroke_width=Metro.stroke_width
    ).draw(surface)


def make_rectangle_frames(surface, constants):
    gz.rectangle(
        lx=constants.width*2, ly=Metro.rectangle_height,
        xy=[0,0], fill=Metro.rectangle_fill
    ).draw(surface)


def draw_metro_frames(surface, constants):
    make_line_frames(surface, constants)
    make_rectangle_frames(surface, constants)


@curry
def make_frames(
    t, constants, settings, next_settings, terminal_settings,
    old, new, old_next, new_next, old_term, new_term
):
    '''Returns the frames from the transition of three texts as a function of time'''
    surface = gz.Surface(constants.width, constants.height, bg_color=(1,1,1))

    case = {
        'metro': draw_metro_frames
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
        .write_videofile(filename, codec=codec, fps=fps))


# Setting classes
@dataclass
class Constants:
    width: int
    height: int
    duration: float
    sep_height: int
    theme: str  # Enum('Theme', 'Metro Yamanote JR Tokyu')


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
