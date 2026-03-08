from flask import Flask, render_template, request, redirect, url_for, flash
from data_manager import DataManager
from models import db, Movie
from dotenv import load_dotenv
import requests
import os

# .env Datei laden
load_dotenv()

app = Flask(__name__)
app.secret_key = "movieweb_secret_key"

# Datenbank konfigurieren
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

data_manager = DataManager()


@app.route('/')
def index():
    users = data_manager.get_users()
    return render_template("index.html", users=users)


@app.route('/user', methods=['POST'])
def create_user():
    name = request.form.get("name")

    if not name:
        flash("Bitte einen Namen eingeben.")
        return redirect(url_for("index"))

    try:
        data_manager.create_user(name)
        flash("User erfolgreich erstellt.")
    except Exception as e:
        print("Fehler beim Erstellen des Users:", e)
        flash("User konnte nicht erstellt werden.")

    return redirect(url_for("index"))


@app.route('/user/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):

    try:
        data_manager.delete_user(user_id)
        flash("User gelöscht.")
    except Exception as e:
        print("Fehler beim Löschen:", e)
        flash("User konnte nicht gelöscht werden.")

    return redirect(url_for("index"))


@app.route('/user/<int:user_id>/movies', methods=['GET'])
def user_movies(user_id):
    movies = data_manager.get_movies(user_id)
    return render_template("movies.html", movies=movies, user_id=user_id)


@app.route('/user/<int:user_id>/movies', methods=['POST'])
def add_movie(user_id):

    title = request.form.get("name")

    api_key = os.getenv("OMDB_API_KEY")

    if not title:
        flash("Bitte einen Filmtitel eingeben.")
        return redirect(url_for("index"))

    if not api_key:
        flash("OMDb API-Key fehlt.")
        print("OMDB_API_KEY nicht gefunden")
        return redirect(url_for("index"))

    try:

        response = requests.get(
            "http://www.omdbapi.com/",
            params={
                "apikey": api_key,
                "t": title
            },
            timeout=5
        )

        data = response.json()

        print("OMDb Antwort:", data)

        if data.get("Response") == "False":
            flash("Film wurde nicht gefunden.")
            return redirect(url_for("index"))

        year_value = data.get("Year", "")
        year = int(year_value) if year_value.isdigit() else None

        poster_url = data.get("Poster")
        if poster_url == "N/A":
            poster_url = None

        movie = Movie(
            name=data.get("Title"),
            director=data.get("Director"),
            year=year,
            poster_url=poster_url,
            user_id=user_id
        )

        data_manager.add_movie(movie)

        flash("Film erfolgreich hinzugefügt.")

    except requests.RequestException as e:
        print("OMDb Fehler:", e)
        flash("Fehler beim Abrufen der Filmdaten.")

    except Exception as e:
        print("Fehler beim Speichern:", e)
        flash("Film konnte nicht gespeichert werden.")

    return redirect(url_for("index"))


@app.route('/user/<int:user_id>/movies/<int:movie_id>/update', methods=['POST'])
def update_movie(user_id, movie_id):

    new_title = request.form.get("new_title")

    if not new_title:
        flash("Neuer Titel fehlt.")
        return redirect(url_for("index"))

    try:
        data_manager.update_movie(movie_id, new_title)
        flash("Film aktualisiert.")
    except Exception as e:
        print("Update Fehler:", e)
        flash("Film konnte nicht aktualisiert werden.")

    return redirect(url_for("index"))


@app.route('/user/<int:user_id>/movies/<int:movie_id>/delete', methods=['POST'])
def delete_movie(user_id, movie_id):

    try:
        data_manager.delete_movie(movie_id)
        flash("Film gelöscht.")
    except Exception as e:
        print("Löschfehler:", e)
        flash("Film konnte nicht gelöscht werden.")

    return redirect(url_for("index"))


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)