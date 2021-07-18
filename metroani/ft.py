'''Functions of time that draws animation frames'''
import gizeh as gz

from cytoolz import curry

from .s_types import Yamanote, Tokyu, JR
from .graphics import (
    draw_metro_frames,
    draw_yamanote_frames,
    draw_jr_frames,
    draw_tokyu_frames,
    make_line_info,
    make_station_icon,
)

__all__ = ['make_frames']


def thresholdify_beginning(pivot, constant_value):
    '''TLDR: turns a / function into _/
    Given a function f(t, duration), return a new function g(t, d) which satisfies:
    1) g(d, d) = f(d, d)             -- (if t == d, then g == f)
    2) g(t, d) = if t <= pivot
                 then: constant_value
                 else: h(t)
                     where h = a linear function of t from g(pivot, d) to g(d, d)
    '''
    def wrapper(f: 'func[T, T] -> T') -> 'func[T, T] -> T':
        def g(t, d):
            if t <= pivot:
                return constant_value
            x1 = pivot
            x2 = d
            y1 = constant_value
            y2 = f(d, d)
            gradient = (y2 - y1) / (x2 - x1)
            c = y2 - gradient*x2
            return gradient*t + c  # h(t)
        return g
    return wrapper


def thresholdify_end(pivot, constant_value):
    '''TLDR: turns a \ function into \_
    Given a function f(t, duration), return a new function g(t, d) which satisfies:
    1) g(0, d) = f(0, d)             -- (if t == d == 0, then g == f)
    2) g(t, d) = if t >= d - pivot
                 then: constant_value
                 else: h(t)
                     where h = a linear function of t from g(0, d) to g(d-pivot, d)
    '''
    def wrapper(f: 'func[T, T] -> T') -> 'func[T, T] -> T':
        def g(t, d):
            if t >= d - pivot:
                return constant_value
            x1 = 0
            x2 = d - pivot
            y1 = f(0, d)
            y2 = constant_value
            gradient = (y2 - y1) / (x2 - x1)
            c = y2 - gradient*x2
            return gradient*t + c  # h(t)
        return g
    return wrapper


@thresholdify_beginning(pivot=0.1, constant_value=0.01)
def show_text_scaler(t, duration):
    '''Scaling function for text-showing animation; Piecewise looks like _/
    Scale ranges from 0 to 1
    '''
    return t / duration


@thresholdify_end(pivot=0.1, constant_value=0.01)
def hide_text_scaler(t, duration):
    '''Scaling function for text-hiding animation; Piecewise looks like \_
    Scale ranges from 0 to 1
    '''
    return 1 - (t / duration)


@thresholdify_beginning(pivot=0.1, constant_value=0.01)
def show_text_alpha(t, _):
    '''Piecewise function that looks like _/'''
    return 2 * t


@thresholdify_end(pivot=0.1, constant_value=0.01)
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
    t, duration, surface, new_text, old_text, show_xy, new_font, old_font,
    new_fontsize, old_fontsize, fontcolor, old_scale_x, new_scale_x,
    new_center_xy, old_center_xy, hide_xy=None
):
    '''Draws one text showing animation and one text hiding animation'''
    # If both texts are the same, no animation is needed
    if new_text == old_text:
        return make_hide_text_frames(
            0, duration, surface, old_text, show_xy, old_font, old_fontsize, fontcolor,
            old_scale_x, old_center_xy
        )

    make_show_text_frames(
        t, duration, surface, new_text, show_xy, new_font, new_fontsize,
        fontcolor, new_scale_x, new_center_xy
    )

    if hide_xy is None:
        hide_xy = show_xy
    make_hide_text_frames(
        t, duration, surface, old_text, hide_xy, old_font, old_fontsize, fontcolor,
        old_scale_x, old_center_xy
    )
    return surface


def make_text_frames_from_setting(t, constants, surface, settings, old, new, color):
    make_text_frames(
        t, constants.duration, surface, new.name, old.name,
        settings.xy, new.font, old.font,
        new.fontsize, old.fontsize, color,
        old.scale_x, new.scale_x, new.enter_xy,
        old.exit_xy
    )
    return surface


def make_text_frames_simple(
    t, constants, surface, new_text, old_text, show_xy,
    new, old, fontcolor, old_scale_x, new_scale_x,
    new_center_xy, old_center_xy, hide_xy=None
):
    '''More complicated than make_text_frames_from_setting but less than
    make_text_frames
    '''
    return make_text_frames(
        t, constants.duration, surface, new_text, old_text, show_xy,
        new.font, old.font, new.fontsize, old.fontsize, fontcolor,
        old.scale_x, new.scale_x, new_center_xy, old_center_xy,
        hide_xy=hide_xy
    )


def make_direction_text(t, n, constants, surface, new_term, old_term, settings,
                        new, old, color):
    new_text = new_term.terminus
    old_text = old_term.terminus
    make_text_frames_simple(
        t, constants, surface, new_text, old_text,
        settings[n].xy, new, old, color, old.scale_x, new.scale_x,
        new.enter_xy, old.exit_xy
    )


def join_text(term):
    if term.name_after_terminus:
        return ' '.join([term.terminus, term.name])
    return ' '.join([term.name, term.terminus])


@curry
def make_frames(
    t, constants, n, settings, next_settings, terminal_settings,
    old, new, old_next, new_next, old_term, new_term, service_settings,
    old_service, new_service
):
    '''Returns the frames from the transition of three texts as a function of time'''
    surface = gz.Surface(constants.width, constants.height, bg_color=(1,1,1))

    # Apply theme
    case = {
        'metro': (draw_metro_frames, draw_metro_text),
        'yamanote': (draw_yamanote_frames, draw_yamanote_text),
        'jr': (draw_jr_frames, draw_jr_text),
        'tokyu': (draw_tokyu_frames, draw_tokyu_text),
    }
    if (funcs := case.get(constants.theme.lower(), None)):
        funcs[0](surface, constants, service_settings)
        funcs[1](
            t, constants, surface, n, new_term, old_term, terminal_settings,
            settings, new, old, next_settings, old_next, new_next,
            service_settings, old_service, new_service
        )

    # Line info graphics
    make_line_info(surface, constants, settings, n)

    # Station icon
    if n == 0 and constants.show_direction:
        make_station_icon(
            surface, settings, n, constants,
            text=terminal_settings.terminus_number
        )
    else:
        make_station_icon(surface, settings, n, constants)

    return surface.get_npimage()


def draw_metro_text(
    t, constants, surface, n, new_term, old_term, terminal_settings,
    settings, new, old, next_settings, old_next, new_next,
    service_settings, old_service, new_service
):
    make_station_text(
        t, constants, n, surface, new_term, old_term, settings, new, old,
        color=(0, 0, 0)
    )
    make_next_text(
        t, n, constants, surface, next_settings, old_next, new_next,
        color=(0, 0, 0)
    )
    make_service_text(
        t, constants, surface, service_settings,
        old_service, new_service, color=(1, 1, 1)
    )
    draw_terminus_text(
        t, n, constants, surface, new_term, old_term, terminal_settings,
        color=(0, 0, 0)
    )


def draw_yamanote_text(
    t, constants, surface, n, new_term, old_term, terminal_settings,
    settings, new, old, next_settings, old_next, new_next,
    service_settings, old_service, new_service
):
    make_station_text(
        t, constants, n, surface, new_term, old_term, settings, new, old,
        color=Yamanote.bg_color
    )
    make_next_text(
        t, n, constants, surface, next_settings, old_next, new_next,
        color=Yamanote.bg_color
    )
    make_service_text(
        t, constants, surface, service_settings,
        old_service, new_service, color=constants.line_color
    )
    draw_terminus_text(
        t, n, constants, surface, new_term, old_term, terminal_settings,
        color=Yamanote.bg_color
    )


def draw_jr_text(
    t, constants, surface, n, new_term, old_term, terminal_settings,
    settings, new, old, next_settings, old_next, new_next,
    service_settings, old_service, new_service
):
    make_station_text(
        t, constants, n, surface, new_term, old_term, settings, new, old,
        color=JR.station_font_color
    )
    make_next_text(
        t, n, constants, surface, next_settings, old_next, new_next,
        color=(0, 0, 0)
    )
    make_service_text(
        t, constants, surface, service_settings,
        old_service, new_service, color=(0, 0, 0)
        #Should be constants.line_color but need stroke
    )
    draw_terminus_text(
        t, n, constants, surface, new_term, old_term, terminal_settings,
        color=(0, 0, 0)
    )


def draw_tokyu_text(
    t, constants, surface, n, new_term, old_term, terminal_settings,
    settings, new, old, next_settings, old_next, new_next,
    service_settings, old_service, new_service
):
    make_station_text(
        t, constants, n, surface, new_term, old_term, settings, new, old,
        color=Tokyu.station_color
    )
    make_next_text(
        t, n, constants, surface, next_settings, old_next, new_next,
        color=Tokyu.station_color
    )
    make_service_text(
        t, constants, surface, service_settings,
        old_service, new_service, color=(1, 1, 1)
    )
    draw_terminus_text(
        t, n, constants, surface, new_term, old_term, terminal_settings,
        color=Tokyu.station_color
    )


def make_station_text(
    t, constants, n, surface, new_term, old_term, settings, new, old, color
):
    if n == 0 and constants.show_direction:
        return make_direction_text(
            t, n, constants, surface, new_term, old_term, settings, new, old,
            color
        )
    return make_text_frames_from_setting(
        t, constants, surface, settings[n],
        old, new, color
    )


def make_next_text(
    t, n, constants, surface, next_settings, old_next, new_next, color
):
    if not (n == 0 and constants.show_direction):
        make_text_frames_from_setting(
            t, constants, surface, next_settings,
            old_next, new_next, color
        )


def make_service_text(
    t, constants, surface, service_settings, old_service, new_service, color
):
    make_text_frames_from_setting(
        t, constants, surface, service_settings,
        old_service, new_service, color
    )


def draw_terminus_text(
    t, n, constants, surface, new_term, old_term, terminal_settings, color
):
    if n == 0 and constants.show_direction:
        # TODO: scale x should always be 0
        return make_text_frames_simple(
            t, constants, surface, new_term.name, old_term.name,
            new_term.xy, new_term, old_term, color,
            old_term.scale_x, new_term.scale_x, new_term.enter_xy,
            old_term.exit_xy, hide_xy=old_term.xy
        )

    new_text = join_text(new_term)
    old_text = join_text(old_term)

    return make_text_frames_simple(
        t, constants, surface, new_text, old_text, terminal_settings.xy,
        new_term, old_term, color, old_term.scale_x,
        new_term.scale_x, new_term.combined_enter_xy, old_term.combined_exit_xy
    )
