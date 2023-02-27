from flask import Blueprint


v1_blueprint = Blueprint('v1', __name__, url_prefix="/v1")
v2_blueprint = Blueprint('v2', __name__)

