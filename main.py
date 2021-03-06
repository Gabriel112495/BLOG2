from flask import Flask, render_template, redirect, url_for, flash,request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm,RegisterForm,LogForm,CommentForm
from flask_gravatar import Gravatar


from functools import wraps
from flask import abort

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://avgtyrhhtdfbma:cf7e907fc29b5d8a05e2f7e4236ed9a97cc9e95be203cbf8a1b664050f7b9012@ec2-34-254-69-72.eu-west-1.compute.amazonaws.com:5432/dc8v4e2uj2qe3j'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


##CONFIGURE TABLES
class User(UserMixin,db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), nullable=False)
    name = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    #This will act like a List of BlogPost objects attached to each User.
    #The "author" refers to the author property in the BlogPost class.


    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Create reference to the User object, the "posts" refers to the posts protperty in the User class.
    author = relationship("User", back_populates="posts")
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments = relationship("Comment", back_populates="parent_post")


class Comment(db.Model):
    __tablename__ = "comment"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment = db.Column(db.String(350), nullable=False)
    comment_author = relationship("User", back_populates="comments")
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")



@app.route('/')
def get_all_posts():



    posts = BlogPost.query.all()

    return render_template("index.html", all_posts=posts,current_user=current_user)


@app.route('/register',methods=["GET","POST"])
def register():
    form=RegisterForm()
    if request.method=="POST":

        if User.query.filter_by(email=form.email.data).first():
            flash("Acest email este inregistrat deja")
            return render_template("register.html", form=form)

        new_user=User()
        new_user.email=form.email.data
        new_user.name=form.name.data
        new_user.password=generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('get_all_posts'))
    return render_template("register.html",form=form)


@app.route('/login',methods=["GET","POST"])
def login():
    form=LogForm()
    if request.method=="POST":
        email=form.email.data
        password=form.password.data

        user=User.query.filter_by(email=email).first()
        if not user:
            flash("This user does not exist")
            return redirect(url_for('login'))



        if user and check_password_hash(user.password,password):
            login_user(user)
            return redirect(url_for('get_all_posts'))
        else:
            flash("Password is not correct")
            return redirect(url_for("login"))


    return render_template("login.html",form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>",methods=["GET","POST"])
def show_post(post_id):
    form=CommentForm()
    requested_post = BlogPost.query.get(post_id)
    if request.method=="POST":
        new_comment = Comment(
            comment=form.body2.data,
            comment_author=current_user,
            parent_post=requested_post
    )
        db.session.add(new_comment)
        db.session.commit()
    return render_template("post.html", post=requested_post,current_user=current_user,form=form)


@app.route("/about")
def about():
    return render_template("about.html",current_user=current_user)


@app.route("/contact")
def contact():
    return render_template("contact.html",current_user=current_user)


@app.route("/new-post",methods=["GET","POST"])

def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author_id=current_user.id,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form,current_user=current_user)


@app.route("/edit-post/<int:post_id>")
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form,current_user=current_user)


@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True)
