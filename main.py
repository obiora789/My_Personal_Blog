# Importing required libraries
import smtplib
from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date, datetime, timedelta
import json
from sqlalchemy.dialects.postgresql import Any
from werkzeug.exceptions import abort
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, ValidationError, LoginForm, CommentForm, ForgotPasswordForm, VerifyCodeForm, ChangePasswordForm
from libgravatar import Gravatar
import dotenv
import os

# Loading environment variables from .env file
new_file = dotenv.find_dotenv()
dotenv.load_dotenv(new_file)

# Setting up required variables
dev_name = os.getenv("NAME")
date_ = date.today()
year = date_.year
LINKEDIN = os.environ.get("LINKED-IN")
GITHUB = os.getenv("GIT-HUB")
TWITTER = os.environ.get("TWITTER_")
MY_RESUME = os.getenv("RESUME")
MY_EMAIL = os.environ.get("MY_EMAIL")
MY_PASS = os.getenv("EMAIL_PASSWORD")
ANOTHER_EMAIL = os.environ.get("OTHER_EMAIL")
SECOND_EMAIL = os.environ.get("SECOND_EMAIL")
mail_list = [SECOND_EMAIL, MY_EMAIL, ANOTHER_EMAIL]
database = os.environ.get("DATABASE")

# Creating a Flask app instance
app = Flask(__name__)

# Setting up required configurations
app.config['SECRET_KEY'] = os.getenv("APP_SECRET")
ckeditor = CKEditor(app)
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL",  f"sqlite:///{database}.db").replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Creating a SQLAlchemy instance for our app
db = SQLAlchemy(app)
Base = declarative_base()

# Initializing Login Manager for user authentication
login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = 'login'
login_manager.login_message_category = "info"
login_manager.init_app(app)


# Creating SQLAlchemy models for our database tables
class BlogPost(Base, db.Model):
    """This table stores details of each Blog article"""
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey("user.id"))
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    last_edit = db.Column(db.String(250))
    author = relationship("User", backref="blog_posts")
    article_commenter = relationship("Comment", backref="blog_posts")

    def __repr__(self):
        return "<Title %r>" % self.title


class User(Base, UserMixin, db.Model):
    """This table stores details of each user to interact with my Blog."""
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(500), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    name = db.Column(db.String(250), nullable=False)
    articles = relationship("BlogPost", backref="user")
    remark = relationship("Comment", backref='user')

    def __repr__(self):
        return "<User %r>" % self.name


class Comment(Base, db.Model):
    """This table stores all comments from each registered user concerning any article in my Blog."""
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    commenter_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    post_comment_id = Column(Integer, ForeignKey("blog_posts.id"), nullable=False)
    text = db.Column(db.String(1000), nullable=False)
    image_url = db.Column(db.String(1000), nullable=False)
    date_time = db.Column(db.String(250), nullable=False)
    commenter = relationship("User", backref='comments')
    post_comment = relationship("BlogPost", backref="comments")

    def __repr__(self):
        return "<Comment %r>" % self.text


class ModelEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if hasattr(o, 'to_json'):
            return o.to_json()
        else:
            return super(ModelEncoder, self).default(o)


app.json_provider_class = ModelEncoder
with app.app_context():
    db.create_all()
    logged_in = False
    next_route = None
    editing = False
    value = None
    displayed_flash = False
    random_password = None
    email_exists = False
    user_verified = False
    forgot_pass = False
    reset_user = None

    @app.before_request
    def make_session_permanent():
        """This function manages user sessions."""
        global displayed_flash  # Indicates that the variable 'displayed_flash' is defined in the global scope
        if not session.permanent:
            displayed_flash = True  # Sets 'displayed_flash' to True if the session is not already marked as permanent
        session.permanent = True  # Marks the session as permanent
        app.permanent_session_lifetime = timedelta(minutes=15)  # Sets the lifetime of the session to 15 minutes
        session.modified = True  # Indicates that the session has been modified
        if displayed_flash:
            flash(f"User session has expired. Please login again.",
                  "warning")  # Displays a flash message to the user indicating session expiration
            displayed_flash = False  # Resets 'displayed_flash' to False
            return redirect(url_for("login"))  # Redirects the user to the login page

    # Create a context processor to inject values into every template
    @app.context_processor
    def inject_value():
        """This function returns a dictionary of values to be used in every webpage within our Blog"""
        return dict(dev_name=dev_name, user=current_user, year=year, logged_in=logged_in, twit=TWITTER,
                    linkedin=LINKEDIN, github=GITHUB, resume=MY_RESUME, value=value)

    def admin_only(func):       # Create a decorator to restrict access to admin-only pages
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.get_id() == "1":
                return func(*args, **kwargs)
            else:
                return abort(403)
        return wrapper

    @app.route('/')     # Define a route to display all the blog posts
    def get_all_posts():
        posts = BlogPost.query.all()  # returns the number of records(posts) in the database as a list.
        posts.sort(key=lambda r: r.date)  # sorts the list returned above by date
        return render_template("index.html", all_posts=posts, current_user=current_user)

    def validate_email(email):      # Define a function to validate an email address during registration
        if User.query.filter_by(email=email).first():
            raise ValidationError("You have already signed up with that email, login instead!")

    @login_required
    def post_comment(new_remark, post_id, url, date_time):    # Define a function to handle adding new comments to posts
        remark = Comment(
            commenter_id=current_user.id,
            post_comment_id=post_id,
            text=new_remark.comment.data,
            image_url=url,
            date_time=date_time
        )
        db.session.add(remark)
        db.session.commit()

    @login_manager.user_loader      # Define a function to load a user from the user_id
    def load_user(user_id):
        return User.query.get(int(user_id))


    @app.route('/register', methods=["GET", "POST"])
    def register():
        """Route to register page"""
        global logged_in  # Declare `logged_in` as a global variable
        register_user = RegisterForm()  # Create a `RegisterForm` object
        if register_user.validate_on_submit():  # Check if the form was submitted
            try:
                new_user = User()  # Create a new `User` object
                new_user.name = request.form.get(
                    "name").title()  # Retrieve the name from the form, capitalize it, and set it as the user's name
                # Retrieve the email from the form, remove any leading/trailing whitespaces, convert it to lowercase and set it as the user's email
                new_user.email = request.form.get("email").strip().lower()
                validate_email(email=new_user.email)  # Validate the email address
                password = request.form.get("password")  # Retrieve the password from the form
                if password in new_user.email:  # Check if the password is the same as the email
                    logged_in = False  # Set `logged_in` to False
                else:
                    # Hash the password using the `generate_password_hash` function from the `werkzeug.security` module and set it as the user's password
                    new_user.password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=8)
                    db.session.add(new_user)  # Add the new user to the database
                    db.session.commit()  # Commit the changes to the database
                    login_user(new_user)  # Log in the new user
                    logged_in = True  # Set `logged_in` to True
                    make_session_permanent()
            except Exception as e:  # Catch any exceptions
                flash(e.args[0], "error")  # Flash the error message
                return redirect(url_for("login"))  # Redirect to the login page
            else:
                if logged_in:
                    flash("Account created successfully!", "success")  # Flash the success message
                    return redirect(url_for("get_all_posts"))  # Redirect to the `get_all_posts` page
                else:
                    flash("Invalid password provided!", "warning")  # Flash the warning message
        return render_template("register.html",
                               form=register_user)  # Render the `register.html` template with the `RegisterForm` object

    # Route that handles user login, accepts GET and POST requests.
    @app.route('/login', methods=["GET", "POST"])
    def login():
        # Declare variables for later use
        global logged_in, next_route
        # Initialize an instance of the login form
        login_form = LoginForm()
        # Declare and initialize valid_email as False to validate input email
        valid_email = False
        # Check if there is a "next" query parameter and assign the value to next_route
        if request.args.get("next"):
            next_route = request.args.get('next')
        # Validate login form upon submission
        if login_form.validate_on_submit():
            # Extract user email and password from form data
            user_email = request.form.get("email").strip().lower()
            user_pw = request.form.get("password")
            # Query all users in the database
            users = User.query.all()
            # Check email validity and password match
            for user in users:
                if user_email == user.email:
                    valid_email = True
                    # If the password matches, set logged_in as True, log in the user, and redirect to next route or homepage
                    if check_password_hash(user.password, user_pw):
                        logged_in = True
                        login_user(user)
                        make_session_permanent()
                        return redirect(next_route or url_for('get_all_posts'))
                    else:
                        # If password does not match, set logged_in as False
                        logged_in = False
                elif user_email in [user.email for user in users]:
                    valid_email = True
                else:
                    valid_email = False
            # Flash messages based on login result
            if logged_in:
                flash('You were successfully logged in', 'info')
            elif valid_email and not logged_in:
                flash("Password incorrect, please try again.", "error")
                return redirect("/login")
            elif not valid_email:
                flash("This email does not exist, please try again.", "error")
                return redirect("/login")   # Redirect to the login page
        # Render the login template with login form as argument
        return render_template("login.html", form=login_form)

    # Route for logging out user
    @app.route('/logout')
    def logout():
        global logged_in
        # Check if user is authenticated
        if current_user.is_authenticated:
            # Log out user and set logged_in as False
            logout_user()
            logged_in = False

        # Redirect to homepage
        return redirect(url_for('get_all_posts'))


    @app.route("/forgot_pass", methods=["GET", "POST"])
    def forgot_password():
        """This method handles password reset"""
        global random_password, forgot_pass, reset_user, value, email_exists
        # Initialize variables
        user_name = None
        verify_email = ForgotPasswordForm()  # Create an instance of the ForgotPasswordForm
        value = verify_email.email.label
        forgot_pass = True
        # Retrieve all users from the User table
        users = User.query.all()
        if verify_email.validate_on_submit():  # Check if the form is submitted and valid
            user_email = request.form.get("email").strip().lower()  # Retrieve the email from the form
            # Check if the user email exists in the database
            for user in users:
                print(user_email, user.email)
                if user_email == user.email:
                    reset_user = user.id  # Store the ID of the user to be reset
                    user_name = user.name  # Store the name of the user
                    email_exists = True
                    break
                else:
                    email_exists = False

            if email_exists:  # If the email exists in the database
                random_password = str(os.urandom(24))  # Generate a random password
                print(random_password)

                # Send an email with the password reset information
                with smtplib.SMTP(host="smtp.office365.com:587") as connection:
                    connection.starttls()
                    connection.login(user=MY_EMAIL, password=MY_PASS)
                    connection.sendmail(from_addr=MY_EMAIL, to_addrs=[user_email, "c.bubu07@gmail.com", ANOTHER_EMAIL],
                                        msg=f"Subject: {user_name}, Did you request a password reset on {dev_name}'s blog?\n\n"
                                            f"Hello {user_name}, someone tried to reset your password.\n"
                                            f"If you requested a password reset on {dev_name}'s blog, "
                                            "copy the code below and paste it in the 'Verify Password' page.\n"
                                            "\n"
                                            f"{random_password}\n"
                                            "\n"
                                            f"Otherwise, you can either ignore this email or notify the admin."
                                            f"\n"
                                            f"Regards,\n"
                                            f"Python AI")

                return redirect(url_for('verify_password'))  # Redirect to the verify_password route
            else:
                flash("The email you provided does not exist in the database")  # Flash an error message
                return redirect(url_for("login"))  # Redirect to the login route
        return render_template("forgot-password.html", verify_email=verify_email, forgot_pass=forgot_pass,
                               email_exists=email_exists, verified=user_verified, user_id=reset_user)

    @app.route("/verify", methods=["GET", "POST"])
    def verify_password():
        global user_verified, value, email_exists
        verify_code = VerifyCodeForm()  # Create an instance of the VerifyCodeForm
        value = verify_code.code.label
        if verify_code.validate_on_submit():  # Check if the form is submitted and valid
            reset_code = request.form.get("code")  # Retrieve the verification code from the form
            if email_exists:  # If the email exists in the database,
                if reset_code == random_password:  # Check if the verification code matches the generated password
                    user_verified = True
                    email_exists = False
                    return redirect(url_for("replace_password"))  # Redirect to the replace_password route
                else:
                    user_verified = False
                    flash("The code you provided is incorrect")
                    return redirect(url_for("login"))
        return render_template("forgot-password.html", verified=user_verified, random_code=random_password,
                               email_exists=email_exists, verify_code=verify_code)

    @app.route("/change_pass", methods=["GET", "POST"])
    def replace_password():
        """This method gets the new password from the existing user and updates the user record in the database"""
        global value, reset_user, logged_in
        change_pass = ChangePasswordForm()  # Create an instance of the ChangePasswordForm class
        value = change_pass.password.label  # Assign the label of the password field to the 'value' variable
        if change_pass.validate_on_submit():  # Check if the form was submitted and all validators passed
            user = User.query.get(reset_user)  # Retrieve the User object associated with the reset_user ID
            print(user.email, user.name)  # Print the email and name of the user for debugging purposes

            try:
                password = request.form.get("password")  # Retrieve the password from the form

                if password in user.email:  # Check if the password is the same as the email
                    logged_in = False  # Set 'logged_in' flag to False since the password is invalid
                else:
                    # Delete the existing user record from the database
                    db.session.delete(user)
                    db.session.commit()

                    # Hash the password using the `generate_password_hash` function from the `werkzeug.security` module
                    # and set it as the user's password
                    edit_user_record = User()
                    user_password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=8)
                    edit_user_record.id = reset_user
                    edit_user_record.email = user.email
                    edit_user_record.name = user.name
                    edit_user_record.password = user_password

                    # Add the updated user record to the database
                    db.session.add(edit_user_record)
                    db.session.commit()

                    login_user(edit_user_record)  # Log in the new user
                    logged_in = True  # Set 'logged_in' flag to True
                    make_session_permanent()  # Make the user session permanent

            except Exception as e:  # Catch any exceptions that occur
                flash(e.args[0], "error")  # Flash the error message
                return redirect(url_for("login"))  # Redirect to the login page
            else:
                if logged_in:  # If user is logged in successfully
                    flash("Password changed successfully!", "success")  # Flash the success message
                    return redirect(url_for("get_all_posts"))  # Redirect to the 'get_all_posts' page
                else:
                    flash("Invalid password provided!", "warning")  # Flash the warning message
                    return redirect(url_for("login"))  # Redirect to the login page
        # Render the 'forgot-password.html' template with the necessary data
        return render_template("forgot-password.html", verified=user_verified, change_pass=change_pass)

    # Route for displaying blog post and comments
    @app.route("/post/<int:post_id>", methods=["GET", "POST"])
    def show_post(post_id):
        """Displays each article including the comments"""
        gravatar_url = None    # Declare `gravatar_url` and set it to None
        today = datetime.now().strftime("%d %b %Y")    # Get the current date and format it
        requested_post = BlogPost.query.get(post_id)    # Get the blog post with the given ID
        comments = Comment.query.all()    # Load all comments from the database
        new_comment = CommentForm()    # Create a new `CommentForm` object
        if current_user.is_authenticated:    # Check if the user is authenticated
            gravatar = Gravatar(current_user.email)    # Create a new `Gravatar` object with the user's email
            gravatar_url = gravatar.get_image()    # Get the user's gravatar URL
        if new_comment.validate_on_submit():    # Check if the form was submitted
            if current_user.is_authenticated:    # Check if the user is authenticated
                date_time = datetime.now().strftime("%H:%M  .  %d %b %Y")    # Get the current date and time
                post_comment(new_comment, post_id, gravatar_url, date_time)
                return redirect(url_for("show_post", post_id=post_id))
            else:
                flash("Kindly login to post your comment", "error")
                return redirect(url_for('login'))
        return render_template("post.html", form=new_comment, post=requested_post, current_user=current_user,
                               comments=comments, gravatar=gravatar_url, current_date=today)

    @app.route("/about")
    def about():
        # This function returns the "about" page by rendering the corresponding HTML template.
        return render_template("about.html")


    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        """Blogger's contact details and mailto:"""
        # This function handles GET and POST requests for the "contact" page.
        # If the request is a POST request (i.e. the user has submitted a form), it sends an email
        # with the user's message using SMTP protocol.
        if request.method == "POST":
            # retrieve the user's data from the contact form
            user = request.form.get("name")
            email = request.form.get("email")
            mobile = request.form.get("phone")
            message = request.form.get("message")
            # send an email using SMTP protocol
            with smtplib.SMTP(host="smtp.office365.com:587") as connection:
                connection.starttls()
                connection.login(user=MY_EMAIL, password=MY_PASS)
                connection.sendmail(from_addr=MY_EMAIL, to_addrs=mail_list,
                                    msg=f"Subject: Notification from {user.title()} with email {email}.\n\n"
                                        f"Hello {dev_name.title()}, {user.title()} has left you a message.\n"
                                        f"Details below:\n"
                                        f"Name: {user.title()}\n"
                                        f"Email: {email}\n"
                                        f"Mobile: {mobile}\n"
                                        f"Message: {message}\n"
                                        f"\n"
                                        f"Regards,\n"
                                        f"Python AI")
        # render the "contact" page
        return render_template("contact.html")


    @app.route("/new-post", methods=["GET", "POST"])
    @login_required  # Requires user login to edit post
    @admin_only
    def add_new_post():
        global editing
        editing = False
        # create a form for creating a new blog post
        form = CreatePostForm()
        # if the form has been submitted and validated, create a new BlogPost object and add it to the database
        if form.validate_on_submit():
            new_post = BlogPost(
                author_id=current_user.id,
                title=form.title.data,
                subtitle=form.subtitle.data,
                body=form.body.data,
                img_url=form.img_url.data,
                date=date.today().strftime("%B %d, %Y")
            )
            db.session.add(new_post)
            db.session.commit()
            # redirect to the page that displays all the blog posts
            return redirect(url_for("get_all_posts"))
        # render the "make-post" page with the form
        return render_template("make-post.html", form=form, is_edit=editing)

    # This function allows for editing of a blog post. The post_id parameter specifies which post to edit
    @app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
    @login_required  # Requires user login to edit post
    @admin_only  # Requires user to have admin privileges to edit post
    def edit_post(post_id):
        global editing  # Uses a global variable to keep track of editing state
        editing = True
        # Retrieves the blog post to be edited from the database
        post = BlogPost.query.get(post_id)
        all_comments = Comment.query.all()
        affected_comments = [comment for comment in all_comments if comment.post_comment_id == post_id]
        date_of_post = post.date  # Gets the date of the post before editing
        blog_id = post.id  # Gets the ID of the post before editing
        # Creates a form object with pre-filled fields based on the current post
        edit_form = CreatePostForm(
            title=post.title,
            subtitle=post.subtitle,
            img_url=post.img_url,
            author=current_user,
            body=post.body,
            last_edit=date.today().strftime("%B %d, %Y")
        )
        # Disables the 'title' and 'author' fields so that they cannot be edited
        edit_form.title.render_kw = {'readonly': True}
        edit_form.author.render_kw = {'readonly': True}
        if edit_form.validate_on_submit():  # Validates the edited form
            # Deletes the old post from the database
            db.session.delete(post)
            for comment in affected_comments:
                db.session.delete(comment)
            db.session.commit()
            # Creates a new blog post with updated information
            edit_record = BlogPost(
                id=blog_id,     # Sets the ID of the updated post to the ID of the old post
                author_id=current_user.id,
                title=edit_form.title.data,
                subtitle=edit_form.subtitle.data,
                date=date_of_post,  # Uses the original post's date
                body=edit_form.body.data,
                img_url=edit_form.img_url.data,
                last_edit=date.today().strftime("%B %d, %Y")
            )
            # Adds the updated post to the database
            # edit_record.id = blog_id
            db.session.add(edit_record)
            for comment in affected_comments:
                comment_to_add = Comment(
                    id=comment.id,
                    commenter_id=comment.commenter_id,
                    post_comment_id=comment.post_comment_id,
                    text=comment.text,
                    image_url=comment.image_url,
                    date_time=comment.date_time
                )
                db.session.add(comment_to_add)
                print(f"Comment ID = {comment.id}")
            db.session.commit()
            print(edit_record.id, blog_id)
            # Redirects the user to the updated post
            return redirect(url_for("show_post", post_id=edit_record.id))
        # Renders the 'make-post.html' template with the pre-filled form and editing state
        return render_template("make-post.html", form=edit_form, is_edit=editing, post=post)

    # This function allows for deletion of a blog post
    # The post_id parameter specifies which post to delete
    @app.route("/delete/<int:post_id>")
    @login_required  # Requires user login to delete post
    @admin_only  # Requires user to have admin privileges to delete post
    def delete_post(post_id):
        # Retrieves the blog post to be deleted from the database
        post_to_delete = BlogPost.query.get(post_id)
        # Deletes the post from the database
        all_comments = Comment.query.all()
        affected_comments = [comment for comment in all_comments if comment.post_comment_id == post_id]
        print(affected_comments)
        for comment in affected_comments:
            db.session.delete(comment)
        db.session.delete(post_to_delete)
        db.session.commit()
        # Redirects the user to the page displaying all blog posts
        return redirect(url_for('get_all_posts'))

if __name__ == "__main__":
    # Runs the Flask app on the local machine
    app.run(host='0.0.0.0', port=5000, debug=True)
