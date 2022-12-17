from flask import Flask, render_template, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from flask_mail import Mail
from werkzeug.utils import secure_filename
import json
import math
import os

# Reading a json file cofig.json
with open('cofig.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']

# Update and save smtp server
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_POST='465',
    MAIL_USERNAME=params['gmail_user'],
    MAIL_PASSWORD=params['gmail_password']
)
mail = Mail(app)

# Check if user in local_server or prod_server
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)

# Contact Database Model


class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)

# Posts Database Model


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    subtitle = db.Column(db.String(30), nullable=False)
    subcontent = db.Column(db.String(300), nullable=False)
    slug = db.Column(db.String(30), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)


@app.route("/")
def home():
    flash("Welcome to NavedBlog!", "success")
    posts = Posts.query.filter_by().all()[0: params['no_of_post']]
    date1 = date.today()
    return render_template('index.html', params=params, posts=posts, date=date1)

# Dashboard


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" in session and session['user'] == params['admin_user']:
        posts = Posts.query.all()
        return render_template("dashboard.html", params=params, posts=posts)

    if request.method == "POST":
        username = request.form.get("username")
        userpass = request.form.get("password")
        # Check is user logged in or not and redirect to dashboard
        if username == params['admin_user'] and userpass == params['admin_password']:
            flash("You are login to dashboard", "success")
            # set the session variable
            session['user'] = username
            posts = Posts.query.all()
            return render_template("dashboard.html", params=params, posts=posts)
    else:
        # If user is not logged in to redirect to login page
        return render_template("login.html", params=params)

    flash("Please correct conditonals", "danger")
    return render_template("login.html", params=params)

# Posts


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_router(post_slug):
    # Fetch all posts to the database
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('single.html', params=params, post=post)

# Edit a post


@app.route("/edit/<string:sno>", methods=["GET", "POST"])
def edit(sno):
    if ("user" in session and session['user'] == params['admin_user']):
        if request.method == "POST":
            box_title = request.form.get('title')
            sub_title = request.form.get('subtitle')
            sub_content = request.form.get('subcontent')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')

            # 0
            if sno == '0':
                post = Posts(title=box_title, subtitle=sub_title, subcontent=sub_content, slug=slug,
                             content=content, tagline=tagline, img_file=img_file, date=datetime.now())
                db.session.add(post)
                db.session.commit()
                flash("These post is added", "success")
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.subtitle = sub_title
                post.subcontent = sub_content
                post.slug = slug
                post.content = content
                post.tagline = tagline
                post.img_file = img_file
                post.date = datetime.now()
                db.session.commit()
                flash("You are post edit successfully", "success")
                return redirect('/edit/' + sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post=post, sno=sno)

# About


@app.route("/about")
def about():
    return render_template('about.html', params=params)

# Blog


@app.route("/blog")
def blog():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_post']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_post']):(page-1) *
                  int(params['no_of_post']) + int(params['no_of_post'])]
    if page == 1:
        prev = "#"
        next = "blog?page=" + str(page+1)
    elif page == last:
        prev = "blog?page=" + str(page-1)
        next = "#"
    else:
        prev = "blog?page=" + str(page-1)
        next = "blog?page=" + str(page+1)

    return render_template('blog.html', params=params, posts=posts, prev=prev, next=next)

# Uploader


@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if ("user" in session and session['user'] == params['admin_user']):
        if (request.method == "POST"):
            f = request.files['file']
            f.save(os.path.join(
                app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            flash("Upload Successfully", "success")
            return redirect('/dashboard')

# Logout a dashboard


@app.route("/logout", methods=['GET', 'POST'])
def logout():
    session.pop('user')
    flash("You are loggedin to dashboard", "success")
    return redirect('/dashboard')

# Delete a Post


@app.route("/delete/<string:sno>", methods=['GET', 'POST'])
def delete(sno):
    if ("user" in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
        flash("You are post is deleted", "success")
    return redirect('/dashboard')


# Contact
@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if (request.method == "POST"):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('msg')
        entry = Contact(name=name, phone=phone, email=email,
                        msg=message,  date=datetime.now())
        print(name, email, phone, message)
        print(entry)
        db.session.add(entry)
        db.session.commit()
        flash("You are message will be sent", "success")

        # mail.send_message('New message from ' + name,
        #                   sender=email,
        #                   recipients = [params['gmail_user']],
        #                   body = message + "\n" + phone
        #                   )
    return render_template('contact.html', params=params)


app.run(debug=True)
