from datetime import datetime
import feedparser

from werkzeug import check_password_hash, generate_password_hash
from flask import Blueprint, request, render_template, flash, g, redirect, url_for
from flask.ext.login import login_user, logout_user, login_required

from app import app, db
from app.forms.users import RegisterForm, LoginForm, ResetPasswordForm
from app.models.users import User

from app.helpers import get_minecraft_stats, get_rss_feed

mod = Blueprint('frontend', __name__)


@mod.route("/")
def index():
    full_stats = get_minecraft_stats()
    rss = get_rss_feed()

    return render_template("frontend/index.html",
                           user = g.user,
                           rss = rss,
                           hostname = "someblocks.com",
                           hostip = full_stats['hostip'],
                           players = full_stats['players'],
                           online = full_stats['numplayers'],
                           maxplayers = full_stats['maxplayers'])


@mod.route("/login", methods=["GET", "POST"])
def login():
    """
    Login form
    """
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('frontend.index'))
    form = LoginForm(request.form)
    if form.validate_on_submit() or request.method == "POST":
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember = form.remember_me.data)
            return redirect(request.args.get("next") or url_for("frontend.index"))
        flash("Wrong username or password", "error")
    return render_template("frontend/login.html",
        form = form)


@mod.route("/logout")
def logout():
    logout_user()
    flash("You were logged out", "info")
    return redirect(url_for("frontend.index"))


@mod.route("/register/", methods=["GET", "POST"])
def register():
    """
    Registration Form
    """

    # Temporary: on my server I've disabled the registration
    if not app.config['REGISTRATION']:
        return redirect(url_for('frontend.index'))

    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('frontend.index'))

    form = RegisterForm(request.form)
    if form.validate_on_submit():
        user = User(form.username.data, form.email.data, \
            generate_password_hash(form.password.data))
        user.regdate = datetime.utcnow()
        db.session.add(user)
        db.session.commit()

        login_user(user, remember = True)

        flash("Thanks for registering")
        return redirect(url_for("users.profile", username=g.user.username))
    return render_template("frontend/register.html",
        form = form)


@mod.route("/resetpassword", methods=["GET", "POST"])
def reset_password():
    """
    Reset Password Form
    """

    # This is only temporary.
    if not app.config['REGISTRATION']:
        return redirect(url_for('frontend.index'))


    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        user.password = generate_password_hash(form.password.data)
        db.session.commit()

        # TODO: Sending an email
        flash("Please check your email to confirm your new password", "info")
        return redirect(url_for("frontend.login"))
    return render_template("frontend/reset_password.html",
        form = form)

@mod.route("/server")
def server():
    return render_template("frontend/server.html")

@mod.route("/worlds")
def worlds():
    return render_template("frontend/worlds.html")

@mod.route("/about")
def about():
    return render_template("frontend/about.html")

@mod.route("/help")
def help():
    return render_template("frontend/help.html")
