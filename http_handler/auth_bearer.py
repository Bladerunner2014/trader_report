
class AuthBearer:
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        return {"Authorization": "Bearer " + self.token}
