import pytz
import datetime
from datetime import timezone


class UTCTime:
    @staticmethod
    def local_to_utc_date_time():
        dt_str = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        format = "%Y.%m.%d %H:%M:%S"
        local_dt = datetime.datetime.strptime(dt_str, format)
        dt_utc = local_dt.astimezone(pytz.UTC)
        return dt_utc.strftime(format)

    @staticmethod
    def time_delta(startdate=datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S'), days=None, hour=None, minute=None,
                   second=None):
        startdate = datetime.datetime.strptime(str(startdate), '%Y.%m.%d %H:%M:%S')
        if days:
            delta_dt = startdate - datetime.timedelta(days)
        if hour:
            delta_dt = startdate.replace(hour=hour, minute=minute, second=second)
        return delta_dt.strftime('%Y.%m.%d %H:%M:%S')

    @staticmethod
    def time_delta_timestamp(startdate=local_to_utc_date_time(), days=None, hour=None,
                             minute=None, second=None):
        startdate = datetime.datetime.strptime(str(startdate), '%Y.%m.%d %H:%M:%S')
        if days:
            delta_dt = (startdate - datetime.timedelta(days)).replace(tzinfo=datetime.timezone.utc).timestamp()
        if hour:
            delta_dt = startdate.replace(hour=hour, minute=minute, second=second,
                                         tzinfo=datetime.timezone.utc).timestamp()
        if not days and not hour:
            delta_dt = startdate.replace(tzinfo=datetime.timezone.utc).timestamp()

        return delta_dt

    @staticmethod
    def days_between(created_at: str):
        date_format = "%Y-%m-%d %H:%M:%S.%f"
        created_at_datetime_class = datetime.datetime.strptime(created_at, date_format)
        now = datetime.datetime.strptime(datetime.datetime.now(timezone.utc).strftime(date_format), date_format)
        delta = now - created_at_datetime_class
        return str(delta.days)
