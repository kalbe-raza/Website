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
app.config['UPLOAD_FOLDER'] = "api/static/files"
app.config['UPLOAD_VIDEO'] = "api/static/video"
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
def encode_spaces(title):
    # Encode the title to create a safe filename
    #encoded_name = urllib.parse.quote(title)
    name = title.replace(' ','1')
    name = name.replace('?' ,'2')
    name = name.replace("'" , '3')
    name = name.replace("," , '4')
    return name

app.jinja_env.filters['subtitle'] = subtitle
app.jinja_env.filters['oneLine'] = oneLine
app.jinja_env.filters['encode_spaces'] = encode_spaces


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
    time = db.Column(db.DateTime, nullable=False , default = datetime.utcnow)
    def __repr__(self):
        return f'<Book {self.title}>'


# with app.app_context():
#      db.create_all()


@app.route('/')
def home():
    result = db.session.execute(db.select(News).order_by(News.time.desc()))
    all_news = result.scalars().all()
    return render_template("index.html" , all_news = all_news)

@app.route('/post/<int:ID>')
def post(ID):
    result = db.session.execute(db.select(News).order_by(News.time.desc()))
    all_news = result.scalars().all()
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

@app.route('/KalbeAli/KalbeRaza/add' , methods=["POST" , "GET"])
def add():
    form = CreatePostForm()

    if form.validate_on_submit():
        news = News(
            title=form.title.data,
            body_first=form.body_first.data,
            body_second=form.body_second.data
        )
        image = form.image.data
        name = encode_spaces(form.title.data)
        image.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(name+".png")))

        video = form.video.data
        video.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_VIDEO'],secure_filename(name+".mp4")))

        db.session.add(news)
        db.session.commit()
        return redirect(url_for("success"))

    return render_template("add.html", form=form)







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
