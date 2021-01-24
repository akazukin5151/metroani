def rgb(values: list[int]) -> list[float]:
    return [x/255 for x in values]


def find_prev_unskipped_station(station_idx, settings):
    for i in range(1, station_idx + 1):
        if settings[station_idx - i].skip:
            i += 1
        else:
            return i
    else:  # nobreak
        print('Warning')
        return i
