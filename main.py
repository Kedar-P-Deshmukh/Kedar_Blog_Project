from flask import Flask, render_template, redirect, url_for, flash,request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm,RegisterUserForm,LoginUserForm,CommentForm
from flask_gravatar import Gravatar
from functools import wraps


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)




gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)



##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


login_manager=LoginManager()
login_manager.init_app(app)

##CONFIGURE TABLES
class User(UserMixin,db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250),unique=True, nullable=False)
    password = db.Column(db.String(250),  nullable=False)
    name = db.Column(db.String(250), nullable=False)

    posts = relationship("BlogPost", back_populates="author")

    comments = relationship("Comment", back_populates="comment_author")

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    comments = relationship("Comment", back_populates="parent_post")




class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")

db.create_all()



def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.id == 1 :
            return redirect(url_for('get_all_posts'))
        return f(*args, **kwargs)
    return decorated_function





@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/')
def get_all_posts():

    posts = BlogPost.query.all()
    print("print")
    #print(posts[0].author_id)
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=["GET","POST"])
def register():
    registerform=RegisterUserForm()
    if request.method=="POST":
        email=registerform.email.data
        user=User.query.filter_by(email=email).first()
        if not user:
            password=registerform.password.data
            name=registerform.name.data
            newuser=User(email=email,password=password,name=name)
            db.session.add(newuser)
            db.session.commit()
            login_user(newuser)
            return redirect(url_for('get_all_posts'))
        else:
            flash("You are already registerd with this email, Login instead")
            return redirect(url_for('login'))
    return render_template("register.html",form=registerform)


@app.route('/login', methods=["GET","POST"])
def login():
    loginUserForm=LoginUserForm()
    if request.method=="POST":
        email=loginUserForm.email.data
        password=loginUserForm.password.data
        user=User.query.filter_by(email=email).first()
        if user:
            if user.password==password:
                login_user(user)
                return redirect(url_for('get_all_posts'))
            else:
                flash("Incorrect password")
                return redirect(url_for('login'))
        else:
            flash("Email Not found")
            return redirect(url_for('login'))
    return render_template("login.html" ,form=loginUserForm)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>" , methods=["GET","POST"])
def show_post(post_id):
    commentform = CommentForm()
    requested_post = BlogPost.query.get(post_id)
    if commentform.validate_on_submit():
        if not current_user.is_authenticated:
            flash("Log in to Comment")
            return redirect(url_for('login'))
        else:
            newcomment = Comment(
                text=commentform.comment_text.data,
                comment_author=current_user,
                parent_post=requested_post
                )
            db.session.add(newcomment)
            db.session.commit()

    return render_template("post.html", post=requested_post,commentform=commentform)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post" , methods=["GET","POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y"),
            author_id = current_user.id)


        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>" , methods=["GET","POST"])
@admin_only
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
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000,debug=True)
