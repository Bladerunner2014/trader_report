import logging
from flask import Flask, request
from dotenv import dotenv_values
from constants.error_message import ErrorMessage
from blueprint import v1_blueprint
from constants.status_code import StatusCode
from swagger import swagger
from log import log
from managers.report_manager import Report

app = Flask("auth")
config = dotenv_values(".env")
logger = logging.getLogger(__name__)


@v1_blueprint.route("/asset", methods=["GET"])
def asset():
    user_id = request.headers.get('user_id')
    rep = Report(user_id)
    res = rep.asset_report()
    if user_id is None:
        logger.error(ErrorMessage.BAD_REQUEST)
        return ErrorMessage.BAD_REQUEST, StatusCode.BAD_REQUEST

    return res.generate_response()


@v1_blueprint.route("/pnl", methods=["GET"])
def seven_day_pnl_ratio():
    user_id = request.headers.get('user_id')
    if user_id is None:
        logger.error(ErrorMessage.BAD_REQUEST)
        return ErrorMessage.BAD_REQUEST, StatusCode.BAD_REQUEST
    rep = Report(user_id)
    res = rep.generate_weekly_pnl_report()

    return res.generate_response()


@v1_blueprint.route("/roi", methods=["GET"])
def roi():
    user_id = request.headers.get('user_id')
    if user_id is None:
        logger.error(ErrorMessage.BAD_REQUEST)
        return ErrorMessage.BAD_REQUEST, StatusCode.BAD_REQUEST
    rep = Report(user_id)
    res = rep.seven_day_pnl_ratio_roi()
    return res.generate_response()





swagger.run_swagger(app)
log.setup_logger()

app.register_blueprint(v1_blueprint)
app.run(host=config["HOST"], port=config["PORT"], debug=config["DEBUG"])
