""" All methods associated to dates  """
from datetime import datetime


def get_year_month_day() -> list:
    """ Return Year month and day
        :return: <list> str str str
    """
    now = datetime.now()
    return now.year, now.month, now.day
