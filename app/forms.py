from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, MultipleFileField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from app.models import User
from flask_wtf.file import FileAllowed

class LoginForm(FlaskForm):
    username_or_email = StringField('Username or Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class ClassForm(FlaskForm):
    name = StringField('Class Name', validators=[DataRequired()])
    submit = SubmitField('Submit')

class NoteForm(FlaskForm):
    date = StringField('Date', validators=[DataRequired()])
    topics = StringField('Topics', validators=[DataRequired()])
    images = MultipleFileField('Images', validators=[DataRequired(), FileAllowed(['jpg', 'png'], 'Images only!')])
    submit = SubmitField('Submit')

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')
