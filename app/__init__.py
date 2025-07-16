from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import markdown
from markupsafe import Markup

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'

@app.template_filter('markdown')
def markdown_filter(text):
    """Convert markdown text to HTML"""
    if not text:
        return ''
    return Markup(markdown.markdown(text, extensions=['nl2br', 'codehilite']))

from app import routes, models
