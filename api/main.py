from flask import Flask, render_template , request , redirect , url_for
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from bs4 import BeautifulSoup
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField , FileField
from wtforms.validators import DataRequired, URL, Email, Length
from flask_ckeditor import CKEditorField ,  CKEditor
from werkzeug.utils import secure_filename
import os
import re
import base64


class CreatePostForm(FlaskForm):

    title = StringField("News Title: ", validators=[DataRequired()])
    # img_url = StringField("news Image URL", description="Leave empty, if you want default image!")
    image = FileField("file")

    video = FileField("video")

    body_first = CKEditorField("Blog Content", validators=[DataRequired()])
    body_second = CKEditorField("Blog Content" , validators=[DataRequired()])

    submit = SubmitField("Submit Post")

app = Flask(__name__)


app.config['SECRET_KEY'] = "abcd"


ckeditor = CKEditor(app)
bootstrap = Bootstrap(app)

def subtitle(text):
    first_full_stop_index = text.find('.')

    soup = BeautifulSoup(text[:first_full_stop_index + 1], 'html.parser')
    cleaned_text = soup.get_text()

    if first_full_stop_index != -1:
        soup = BeautifulSoup(text[:first_full_stop_index + 1], 'html.parser')
        cleaned_text = soup.get_text()
        return cleaned_text + ".."
    else:
        soup = BeautifulSoup(text, 'html.parser')
        cleaned_text = soup.get_text()
        return cleaned_text + "..."

def oneLine(text):
    words = text.split()
    return ' '.join(words[:3]) + '...'

import urllib.parse

app.jinja_env.filters['subtitle'] = subtitle
app.jinja_env.filters['oneLine'] = oneLine


app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("POSTGRES_MY_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)
# db.init_app(app)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    body_first = db.Column(db.String(250), nullable=False)
    body_second = db.Column(db.String(250) ,  nullable=False)
    # image = db.Column(db.String(250) , nullable = False)
    image_data = db.Column(db.LargeBinary)
    video_data = db.Column(db.LargeBinary)
    time = db.Column(db.DateTime, nullable=False , default = datetime.utcnow)
    def __repr__(self):
        return f'<Book {self.title}>'


# with app.app_context():
#      db.create_all()


@app.route('/')
def home():
    result = db.session.execute(db.select(News).order_by(News.time.desc()))
    all_news = result.scalars().all()
    for news in all_news:
        if news.image_data:
            news.image_data_base64 = base64.b64encode(news.image_data).decode('utf-8')
        else:
            news.image_data_base64 = None

    return render_template("index.html" , all_news = all_news)

@app.route('/KalbeAli/KalbeRaza/add' , methods=["POST" , "GET"])
def add():
    form = CreatePostForm()

    if form.validate_on_submit():
        news = News(
            title=form.title.data,
            body_first=form.body_first.data,
            body_second=form.body_second.data
        )
        if 'image' in request.files:
            image = request.files['image']
            if image:
                image_data = image.read()
                news.image_data = image_data  # Assuming you have an "image_data" field in your News model

        if 'video' in request.files:
            video = request.files['video']
            if video:
                video_data = video.read()
                news.video_data = video_data

        db.session.add(news)
        db.session.commit()
        return redirect(url_for("success"))

    return render_template("add.html", form=form)

@app.route('/post/<int:ID>')
def post(ID):
    result = db.session.execute(db.select(News).order_by(News.time.desc()))
    all_news = result.scalars().all()
    for news in all_news:
        if news.image_data:
            news.image_data_base64 = base64.b64encode(news.image_data).decode('utf-8')
        else:
            news.image_data_base64 = None
        if news.video_data:
            news.video_data_base64 = base64.b64encode(news.video_data).decode('utf-8')
        else:
            news.video_data_base64 = None
    new = News.query.get(ID)
    i=0
    j=1
    k=2
    if all_news[0] == new:
        i=3
    elif all_news[1] == new :
        j=3
    elif all_news[2] == new :
        k=3
    marquee_news = [all_news[i],all_news[j],all_news[k]]
    return render_template("post.html" , current_news = new , marquee_news=marquee_news , all_news = all_news)






@app.route('/KalbeAli/KalbeRaza/delete', methods=["POST", "GET"])
def delete():
    if request.method == "POST":
        news_name = request.form["title"]

        # Check if a row with the given title exists in the database
        existing_news = db.session.query(News).filter_by(title=news_name).first()

        if existing_news:
            try:
                db.session.delete(existing_news)
                db.session.commit()
                return redirect(url_for("home"))
            except IntegrityError as e:
                # Handle any potential database errors
                db.session.rollback()
                return "Error: Unable to delete the row.", 500
        else:
            return "Error: The news with the given title does not exist.", 404

        # filename = "static/files"+ encode_spaces(news_name) + ".png"
        # file_path = os.path.join(app.static_folder, filename)
        # if os.path.exists(file_path):
        #     os.remove(file_path)

    return render_template("delete.html")


@app.route('/add/success')
def success():
    return render_template("success.html")





if __name__ == "__main__":
    app.run(debug=True )
