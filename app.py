"""
Pluto Genogram Pintar — Flask entrypoint (lokal + Vercel Hobby gratis).

Vercel:
- HTML/API → serverless function ini (app.py)
- CSS/JS/favicon → folder public/ (CDN edge, tanpa hitung function)
"""

import os

from flask import Flask, render_template, send_from_directory

from routes.routes import api_bp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(PUBLIC_DIR, "static")


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=TEMPLATES_DIR,
        static_folder=STATIC_DIR,
        static_url_path="/static",
    )
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "pluto-genogram-dev-key")
    app.config["JSON_AS_ASCII"] = False
    app.config["VERCEL"] = bool(os.environ.get("VERCEL"))

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
            PUBLIC_DIR,
            "favicon.svg",
            mimetype="image/svg+xml",
        )

    return app


# Vercel memerlukan instance bernama `app`
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
