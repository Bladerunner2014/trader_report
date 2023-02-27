import json
import logging
import requests

from constants.status_code import StatusCode


class RequestHandler:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def send_post_request(self, base_url: str, end_point: str, port: str
                          , timeout: str, error_log_dict: dict, headers: dict = None, body=None):
        """
        post_request send post request .

        :param base_url: destination base_url
        :param end_point: destination end_point
        :param port: destination port
        :param body: request body
        :param timeout: request timeout
        :param error_log_dict: error log dictionary for specified destination service
        :param headers: request headers
        :return: returns the response
        """
        default_headers = {"Content-Type": "application/json"}
        if headers:
            default_headers.update(headers)
        data = None
        if body:
            data = json.dumps(body)
        try:
            r = requests.post(url=base_url + ":" + port + end_point, data=data, headers=default_headers,
                              timeout=int(timeout))
        except requests.exceptions.Timeout as error:
            self.logger.error(error_log_dict["REQUEST_TIMEOUT"])
            self.logger.error(error)
            raise error
        except requests.exceptions.ConnectionError as error:
            self.logger.error(error_log_dict["CONNECTION_ERROR"])
            self.logger.error(error)
            raise error
        except Exception as error:
            self.logger.error(error_log_dict["REQUEST_ERROR"])
            self.logger.error(error)
            raise error
        if r.status_code in [StatusCode.SUCCESS, StatusCode.NOCONTENT]:
            return r.json(), r.status_code
        else:
            return r.text, r.status_code

    def send_put_request(self, base_url: str, end_point: str, port: str, body: str, timeout: str, error_log_dict: dict,
                         headers: dict = None):
        """
        post_request send post request .

        :param base_url: destination base_url
        :param end_point: destination end_point
        :param port: destination port
        :param body: request body
        :param timeout: request timeout
        :param error_log_dict: error log dictionary for specified destination service
        :return: returns the response
        """
        default_headers = {"Content-Type": "application/json"}
        if headers:
            default_headers.update(headers)
        data = None
        if body:
            data = json.dumps(body)
        try:
            r = requests.put(url=base_url + ":" + port + end_point, data=data, headers=default_headers,
                             timeout=int(timeout))
        except requests.exceptions.Timeout as error:
            self.logger.error(error_log_dict["REQUEST_TIMEOUT"])
            self.logger.error(error)
            raise error
        except requests.exceptions.ConnectionError as error:
            self.logger.error(error_log_dict["CONNECTION_ERROR"])
            self.logger.error(error)
            raise error
        except Exception as error:
            self.logger.error(error_log_dict["REQUEST_ERROR"])
            self.logger.error(error)
            raise error
        if r.status_code == StatusCode.SUCCESS:
            return r.json(), r.status_code
        else:
            return r.text, r.status_code

    def send_get_request(self, base_url: str, port: str, end_point: str, timeout: str, error_log_dict: dict,
                         params: dict = None):
        """
        post_request send post request .

        :param base_url: destination host
        :param port: destination port
        :param end_point: destination end point
        :param params: request params
        :param timeout: request timeout
        :param error_log_dict: error log dictionary for specified destination service
        :return: returns the response
        """
        default_headers = {"Content-Type": "application/json"}
        try:
            r = requests.get(url=base_url + ":" + port + end_point, params=params, headers=default_headers,
                             timeout=int(timeout))
        except requests.exceptions.Timeout as error:
            self.logger.error(error_log_dict["REQUEST_TIMEOUT"])
            self.logger.error(error)
            raise error
        except requests.exceptions.ConnectionError as error:
            self.logger.error(error_log_dict["CONNECTION_ERROR"])
            self.logger.error(error)
            raise error
        except Exception as error:
            self.logger.error(error_log_dict["REQUEST_ERROR"])
            self.logger.error(error)
            raise error
        if r.status_code == StatusCode.SUCCESS:
            return r.json(), r.status_code
        else:
            return r.text, r.status_code

    @staticmethod
    def create_json_from_args(**kwargs):
        return locals()["kwargs"]

