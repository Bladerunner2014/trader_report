import datetime


class SampleModel:
    __table_name__ = 'auth'
    id = "id"
    user_id = "user_id"
    refresh_token = "refresh_token"
    created_at = "created_at"

    def __init__(self):
        self.user_id = None
        self.refresh_token = None
        self.created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")



