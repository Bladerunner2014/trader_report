import pytz
import datetime
from datetime import timezone


class UTCTime:
    def local_to_utc_date_time(self):
        dt_str = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        format = "%Y.%m.%d %H:%M:%S"
        local_dt = datetime.datetime.strptime(dt_str, format)
        dt_utc = local_dt.astimezone(pytz.UTC)
        return dt_utc.strftime(format)

    def time_delta(self,startdate=datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S'), days=None, hour=None, minute=None,
                   second=None):
        startdate = datetime.datetime.strptime(str(startdate), '%Y.%m.%d %H:%M:%S')
        if days:
            delta_dt = startdate - datetime.timedelta(days)
        if hour:
            delta_dt = startdate.replace(hour=hour, minute=minute, second=second)
        return delta_dt.strftime('%Y.%m.%d %H:%M:%S')

    def time_delta_timestamp(self, days=None, hour=None,
                             minute=None, second=None):
        startdate = self.local_to_utc_date_time()
        startdate = datetime.datetime.strptime(str(startdate), '%Y.%m.%d %H:%M:%S')
        if days:
            delta_dt = (startdate - datetime.timedelta(days)).replace(tzinfo=datetime.timezone.utc).timestamp()
        if hour:
            delta_dt = startdate.replace(hour=hour, minute=minute, second=second,
                                         tzinfo=datetime.timezone.utc).timestamp()
        if not days and not hour:
            delta_dt = startdate.replace(tzinfo=datetime.timezone.utc).timestamp()

        return delta_dt

    def days_between(self,created_at: str):
        date_format = "%Y-%m-%d %H:%M:%S.%f"
        created_at_datetime_class = datetime.datetime.strptime(created_at, date_format)
        now = datetime.datetime.strptime(datetime.datetime.now(timezone.utc).strftime(date_format), date_format)
        delta = now - created_at_datetime_class
        return str(delta.days)
