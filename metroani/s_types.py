from __future__ import annotations
from typing import NamedTuple

from .utils import rgb


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
    show_direction: bool


class LineTranslation(NamedTuple):
    '''Collection of values unique for every language, for lines'''
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


class TerminusTranslation(NamedTuple):
    '''Collection of values unique for every language, for terminus text'''
    # 'Inherit' from StationTranslation
    name: str
    font: str
    fontsize: int
    scale_x: float
    enter_xy: list[int]
    exit_xy: list[int]
    # New
    terminus: str
    name_after_terminus: bool
    xy: list[int]
    # TODO: consider splitting it up for 'normal' and 'direction' settings
    combined_enter_xy: list[int]
    combined_exit_xy: list[int]
    # TODO: station icon line color


class Transition(NamedTuple):
    '''Transition-wide settings for state settings
    Contains circular-list of the text in every language
    '''
    names: list[StationTranslation]
    xy: list[int]

    @classmethod
    def from_json(cls, settings: 'json', section: str):
        return cls(
            [StationTranslation(**ss) for ss in settings[section]['translations']],
            settings[section]['xy']
        )


class TerminusTransition(NamedTuple):
    '''Transition-wide settings for terminal settings
    Contains circular-list of the text in every language
    '''
    # 'Inherit' from Transition
    names: list[TerminusTranslation]
    xy: list[int]
    # New
    terminus_number: str

    @classmethod
    def from_json(cls, settings: 'json', section: str):
        return cls(
            [TerminusTranslation(**ss) for ss in settings[section]['translations']],
            settings[section]['xy'],
            settings[section]['terminus_number'],
        )


class StationTransition(NamedTuple):
    '''Transition-wide settings for station settings
    Contains circular-list of the text in every language
    '''
    names: list[StationTranslation]
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
                [StationTranslation(**ss) for ss in station['translations']],
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


# Themes
class Metro(NamedTuple):
    stroke_color = [0, 0, 0]
    stroke_width = 10
    rectangle_height = 250
    rectangle_fill = [0.95, 0.95, 0.95]
    service_fill = rgb([69, 114, 197])


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
    service_fill = rgb([204, 73, 62])
