"""Pluto Genogram Pintar — Flask application entrypoint for Vercel."""

import os
from flask import Flask, render_template, send_from_directory

from api.routes import api_bp


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        static_url_path="/static",
    )
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "pluto-genogram-dev-key")
    app.config["JSON_AS_ASCII"] = False

    app.register_blueprint(api_bp)

    @app.route("/")
    def landing():
        return render_template("landing.html")

    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")

    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, "static"),
            "favicon.svg",
            mimetype="image/svg+xml",
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
