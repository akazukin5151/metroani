import sys
from itertools import chain

from cytoolz import sliding_window


def rgb(values: list[int]) -> list[float]:
    return [x/255 for x in values]


def pairs(lst):
    return sliding_window(2, chain(lst, [lst[0]]))


def find_prev_unskipped_station(station_idx, settings):
    '''
    Number of stations between current station to the previous station
    that is not skipped
    '''
    for idx, setting in enumerate(reversed(settings[:station_idx])):
        if not setting.skip:
            return idx + 1  # Number of stations, not the index

    # Warnings doesn't work, maybe hidden by moviepy?
    print(
        'The first station has skip=true. '
        'Please make that station skip=false or add a preceding station '
        'with skip=false.',
        file=sys.stderr
    )
    return 1
