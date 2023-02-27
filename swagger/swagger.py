from swagger_ui import flask_api_doc

parameters = {
    "deepLinking": "true",
    "displayRequestDuration": "true",
    "layout": "\"StandaloneLayout\"",
    "plugins": "[SwaggerUIBundle.plugins.DownloadUrl]",
    "presets": "[SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset]",
}


def run_swagger(app):
    flask_api_doc(app, config_path='swagger-conf.yaml', url_prefix='/api/doc', title='API doc', editor=True)
