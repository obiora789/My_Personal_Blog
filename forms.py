from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField
from wtforms.validators import InputRequired, URL, Length, EqualTo, ValidationError
from flask_ckeditor import CKEditorField


# WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[InputRequired()], render_kw={"placeholder": "Enter Blog title"})
    subtitle = StringField("Subtitle", validators=[InputRequired()], render_kw={"placeholder": "Enter Blog subtitle"})
    img_url = StringField("Blog Image URL", validators=[InputRequired(), URL()],
                          render_kw={"placeholder": "Enter Blog Image Link"})
    author = StringField("Author", validators=[InputRequired()], render_kw={"placeholder": "Enter Blog Author"})
    body = CKEditorField("Blog Content", validators=[InputRequired()], render_kw={"placeholder": "Enter Blog Content"})
    submit = SubmitField("Submit Post")


class RegisterForm(FlaskForm):
    email = EmailField("Email", validators=[InputRequired()], render_kw={"placeholder": "Enter your email"})
    password = PasswordField("Password", validators=[InputRequired(), Length(min=8, max=60)],
                             render_kw={"placeholder": "Enter your password"})
    copy_password = PasswordField("Repeat Password", validators=[
        InputRequired(), Length(min=8, max=60), EqualTo("password", message="Passwords must match!")
    ], render_kw={"placeholder": "Repeat Password"})
    name = StringField("Name", validators=[InputRequired()], render_kw={"placeholder": "Enter your full name"})
    submit = SubmitField("SIGN ME UP!")


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[InputRequired()], render_kw={"placeholder": "Enter your Email"})
    password = PasswordField("Password", validators=[InputRequired(), Length(min=8, max=60)],
                             render_kw={"placeholder": "Enter your password"})
    submit = SubmitField("SIGN IN")


class CommentForm(FlaskForm):
    comment = CKEditorField("Comment", validators=[InputRequired()], render_kw={"placeholder": "Add a Comment"})
    submit = SubmitField("Submit Comment")
