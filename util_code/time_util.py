import datetime
# 时间帮助

def day_get(d,day):
    oneday = datetime.timedelta(days=day)
    day = d - oneday
    date_from = datetime.datetime(day.year, day.month, day.day, 0, 0, 0)
    date_to = datetime.datetime(day.year, day.month, day.day, 23, 59, 59)
    print('---'.join([str(date_from), str(date_to)]))

def week_get(d):
    dayscount = datetime.timedelta(days=d.isoweekday())
    dayto = d - dayscount
    sixdays = datetime.timedelta(days=6)
    dayfrom = dayto - sixdays
    date_from = datetime.datetime(dayfrom.year, dayfrom.month, dayfrom.day, 0, 0, 0)
    date_to = datetime.datetime(dayto.year, dayto.month, dayto.day, 23, 59, 59)
    print ('---'.join([str(date_from), str(date_to)]))

def month_get(d):
    """    
    返回上个月第一个天和最后一天的日期时间
    :return
    date_from: 2016-01-01 00:00:00
    date_to: 2016-01-31 23:59:59
    """
    dayscount = datetime.timedelta(days=d.day)
    dayto = d - dayscount
    date_from = datetime.datetime(dayto.year, dayto.month, 1, 0, 0, 0)
    date_to = datetime.datetime(dayto.year, dayto.month, dayto.day, 23, 59, 59)
    print ('---'.join([str(date_from), str(date_to)]))
    return date_from, date_to


def get_last_week():
    current = datetime.datetime.now()
    oneday = datetime.timedelta(days=30)
    day = current - oneday
    date_from = datetime.datetime(day.year, day.month, day.day, 0, 0, 0)
    date_to = datetime.datetime(current.year, current.month, current.day, 23, 59, 59)
    return date_from,date_to


# 时间格式转化
def trans_format(time_string):
        """
        @note 时间格式转化
        :param time_string:
        :param from_format:
        :param to_format:
        :return:
        """
        # print(len(time_string))
        # 格林尼治时间转化，切片分隔
        time_string = time_string[0:20] + time_string[-4:]
        dt = datetime.datetime.strptime(time_string, '%a %b %d %H:%M:%S %Y')
        times = dt.strftime("%Y-%m-%d %H:%M:%S")

        return times

if __name__ == "__main__":
    cst_time = 'Sat Feb 27 15:01:42 +0800 2021'
    format_time = trans_format(cst_time)
    print(format_time)

    date_from,date_to = get_last_week()
    print(date_from)
    print(date_to)