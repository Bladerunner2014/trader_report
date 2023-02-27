import pytz
import datetime
from datetime import datetime
from datetime import timezone


class UTCTime:
    @staticmethod
    def local_to_utc_date_time():
        dt_str = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        format = "%Y-%m-%dT%H:%M:%SZ"
        local_dt = datetime.datetime.strptime(dt_str, format)
        dt_utc = local_dt.astimezone(pytz.UTC)
        return dt_utc.strftime(format)

    @staticmethod
    def time_delta(startdate=datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'), days=None, hour=None, minute=None,
                   second=None):
        startdate = datetime.datetime.strptime(str(startdate), '%d.%m.%Y %H:%M:%S')
        if days:
            delta_dt = startdate - datetime.timedelta(days)
        if hour:
            delta_dt = startdate.replace(hour=hour, minute=minute, second=second)
        return delta_dt.strftime('%d.%m.%Y %H:%M:%S')

    @staticmethod
    def time_delta_timestamp(startdate=datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'), days=None, hour=None,
                             minute=None, second=None):
        startdate = datetime.datetime.strptime(str(startdate), '%d.%m.%Y %H:%M:%S')
        if days:
            delta_dt = (startdate - datetime.timedelta(days)).replace(tzinfo=datetime.timezone.utc).timestamp() * 1000
        if hour:
            delta_dt = startdate.replace(hour=hour, minute=minute, second=second,
                                         tzinfo=datetime.timezone.utc).timestamp() * 1000
        if not days and not hour:
            delta_dt = startdate.replace(tzinfo=datetime.timezone.utc).timestamp() * 1000

        return delta_dt

    @staticmethod
    def days_between(created_at: str):
        date_format = "%Y-%m-%d %H:%M:%S.%f"
        created_at_datetime_class = datetime.strptime(created_at, date_format)
        now = datetime.strptime(datetime.now(timezone.utc).strftime(date_format), date_format)
        delta = now - created_at_datetime_class
        return str(delta.days)
