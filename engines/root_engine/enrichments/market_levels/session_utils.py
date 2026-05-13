from datetime import time as dtime

def classify_session(t):
    asia_open  = dtime(1, 0)
    asia_close = dtime(10, 0)

    europe_open  = dtime(9, 0)
    europe_close = dtime(17, 30)

    usa_open  = dtime(15, 30)
    usa_close = dtime(22, 0)

    if usa_open <= t < usa_close:
        return "usa"
    if europe_open <= t < europe_close:
        return "europe"
    if asia_open <= t < asia_close:
        return "asia"

    return "off"