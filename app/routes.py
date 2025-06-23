from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, ClassForm, NoteForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Class, Note
import os
from werkzeug.utils import secure_filename

@app.route('/')
@app.route('/index')
@login_required
def index():
    classes = Class.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', title='Home', classes=classes)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/add_class', methods=['GET', 'POST'])
@login_required
def add_class():
    form = ClassForm()
    if form.validate_on_submit():
        cl = Class(name=form.name.data, author=current_user)
        db.session.add(cl)
        db.session.commit()
        flash('Your class has been added!')
        return redirect(url_for('index'))
    return render_template('add_class.html', title='Add Class', form=form)

@app.route('/edit_class/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_class(id):
    form = ClassForm()
    cl = Class.query.get(id)
    if form.validate_on_submit():
        cl.name = form.name.data
        db.session.commit()
        flash('Your class has been updated!')
        return redirect(url_for('index'))
    elif request.method == 'GET':
        form.name.data = cl.name
    return render_template('edit_class.html', title='Edit Class', form=form)

@app.route('/delete_class/<int:id>')
@login_required
def delete_class(id):
    cl = Class.query.get(id)
    for note in cl.notes:
        db.session.delete(note)
    db.session.delete(cl)
    db.session.commit()
    flash('Your class has been deleted!')
    return redirect(url_for('index'))

@app.route('/add_note/<int:class_id>', methods=['GET', 'POST'])
@login_required
def add_note(class_id):
    form = NoteForm()
    if form.validate_on_submit():
        f = form.image.data
        filename = secure_filename(f.filename)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        note = Note(date=form.date.data, topics=form.topics.data, image_path=filename, class_id=class_id)
        db.session.add(note)
        db.session.commit()
        flash('Your note has been added!')
        return redirect(url_for('index'))
    return render_template('add_note.html', title='Add Note', form=form)

@app.route('/edit_note/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_note(id):
    form = NoteForm()
    note = Note.query.get(id)
    if form.validate_on_submit():
        if form.image.data:
            f = form.image.data
            filename = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            note.image_path = filename
        note.date = form.date.data
        note.topics = form.topics.data
        db.session.commit()
        flash('Your note has been updated!')
        return redirect(url_for('index'))
    elif request.method == 'GET':
        form.date.data = note.date
        form.topics.data = note.topics
    return render_template('edit_note.html', title='Edit Note', form=form)

@app.route('/delete_note/<int:id>')
@login_required
def delete_note(id):
    note = Note.query.get(id)
    db.session.delete(note)
    db.session.commit()
    flash('Your note has been deleted!')
    return redirect(url_for('index'))
