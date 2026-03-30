import os
import requests
from flask import Flask, request, redirect, render_template, url_for, flash
from data_manager import DataManager
from models import db, Movie, User


app = Flask(__name__)

# Konfig.
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/movies.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev_key_123'

db.init_app(app)
data_manager = DataManager()


# Routes
@app.route('/')
def home():
    users = data_manager.get_users()
    return render_template('index.html', users=users)


@app.route('/add_user', methods=['POST'])
def add_user():
    name = request.form.get('name')
    if name:
        data_manager.create_user(name)
    return redirect(url_for('home'))


@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    data_manager.delete_user(user_id)
    return redirect(url_for('home'))


@app.route('/users/<int:user_id>')
def list_user_movies(user_id):
    current_user = data_manager.get_user_by_id(user_id)
    movies = data_manager.get_movies(user_id)
    return render_template('movies.html', movies=movies, user=current_user, user_id=user_id)


@app.route('/users/<int:user_id>/add_movie', methods=['POST'])
def add_movie(user_id):
    title = request.form.get('title')
    year_opt = request.form.get('year')
    api_key = "c3c6eb95"

    try:
        url = f"http://www.omdbapi.com/?t={title}&apikey={api_key}"
        if year_opt:
            url += f"&y={year_opt}"

        response = requests.get(url, timeout=5)
        data = response.json()

        if data.get('Response') == 'True':
            # Jahr (nimmt nur die ersten 4 Ziffern)
            raw_year = data.get('Year', '0')
            clean_year = int(raw_year[:4]) if raw_year[:4].isdigit() else 0

            new_movie = Movie(
                name=data.get('Title'),
                director=data.get('Director'),
                year=clean_year,
                poster_url=data.get('Poster'),
                user_id=user_id
            )
            data_manager.add_movie(new_movie)
            flash("Movie successfully added!", "success")
        else:
            flash(f"Error: {data.get('Error')}", "danger")

    except Exception as e:
        print(f"API/DB Error: {e}")
        flash("An error occurred while adding the movie.", "danger")

    return redirect(url_for('list_user_movies', user_id=user_id))


@app.route('/users/<int:user_id>/update_movie/<int:movie_id>', methods=['POST'])
def update_movie(user_id, movie_id):
    new_name = request.form.get('new_name')
    if new_name:
        data_manager.update_movie(movie_id, new_name)
    return redirect(url_for('list_user_movies', user_id=user_id))


@app.route('/users/<int:user_id>/delete_movie/<int:movie_id>', methods=['POST'])
def delete_movie(user_id, movie_id):
    data_manager.delete_movie(movie_id)
    return redirect(url_for('list_user_movies', user_id=user_id))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)