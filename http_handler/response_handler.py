import json
from flask import Response


class ResponseHandler:
    def __init__(self):
        self.response = None
        self.status_code = None
        self.headers = dict()
        self.headers["Content-Type"] = "application/json"

    def generate_response(self):
        return Response(response=json.dumps(self.response), status=self.status_code, headers=self.headers)

    def set_header(self, new_header):
        self.headers.update(new_header)

    def set_response(self, data):
        self.response = data

    def set_status_code(self, status_code):
        self.status_code = status_code

