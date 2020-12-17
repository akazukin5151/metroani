from metroani import Constants, CircularList, Transition, Translation, W

# Constants
constants = Constants(1920, 1080, 0.7)

# Station settings
saginomiya_names = CircularList([
    Translation('鷺ノ宮', 'Hiragino Sans GB W3', 200, [W/2, 150], [W/2, 320], 1),
    Translation('Saginomiya', 'Roboto', 170, [1400, 120], [1400, 350], 0.8),
    Translation('鷺之宮', 'Hiragino Sans GB W3', 170, [1400, 120], [1400, 350], 1),
])
saginomiya = Transition(saginomiya_names, [1300, 220])

toritsu_kasei_names = CircularList([
    Translation('都立家政', 'Hiragino Sans GB W3', 200, [W/2, 150], [W/2, 320], 1),
    Translation('Toritsu-Kasei', 'Roboto', 170, [1400, 120], [1400, 350], 0.8),
    Translation('都立家政', 'Hiragino Sans GB W3', 170, [1400, 120], [1400, 350], 1),
])
toritsu_kasei = Transition(toritsu_kasei_names, [1300, 220])
station_settings = [saginomiya, toritsu_kasei]

# Terminus station setting
terminal = CircularList([
    Translation('西武新宿 ゆき', 'Hiragino Sans GB W3', 70, [W/2, 35], [W/2, 100], 1),
    Translation('For Seibu Shinjuku', 'Roboto', 60, [W/2, 35], [W/2, 110], 0.8),
    Translation('開往 西武新宿', 'Hiragino Sans GB W3', 60, [W/2, 35], [W/2, 110], 1),
])
terminal_settings = Transition(terminal, [650, 70])

# Train state settings
next_ = CircularList([
    Translation('つぎは', 'Hiragino Sans GB W3', 70, [W/2, 250], [W/2, 330], 1),
    Translation('Next', 'Roboto', 60, [W/2, 250], [W/2, 330], 1),
    Translation('下一站', 'Hiragino Sans GB W3', 60, [W/2, 250], [W/2, 330], 1),
])
next_settings = Transition(next_, [300, 280])

arriving = CircularList([
    Translation('まもなく', 'Hiragino Sans GB W3', 70, [W/2, 250], [W/2, 330], 1),
    Translation('Arriving at', 'Roboto', 60, [W/2, 250], [W/2, 330], 1),
    Translation('即將到達', 'Hiragino Sans GB W3', 60, [W/2, 250], [W/2, 330], 1),
])
arriving_settings = Transition(arriving, [300, 280])

stopping = CircularList([
    Translation('ただいま', 'Hiragino Sans GB W3', 70, [W/2, 250], [W/2, 330], 1),
    Translation('Now stopping at', 'Roboto', 60, [W/2, 250], [W/2, 330], 0.8),
    Translation('這一站', 'Hiragino Sans GB W3', 60, [W/2, 250], [W/2, 330], 1),
])
stopping_settings = Transition(stopping, [300, 280])

