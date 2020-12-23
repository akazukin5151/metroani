'''Functions of time that draws animation frames'''
import gizeh as gz

from cytoolz import curry

from .s_types import Yamanote, Tokyu
from .graphics import (
    draw_metro_frames,
    draw_yamanote_frames,
    draw_jr_frames,
    draw_tokyu_frames,
    make_line_info,
    make_station_icon,
)

__all__ = ['make_frames']


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
def show_text_alpha(t, _):
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

