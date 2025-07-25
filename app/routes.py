from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, ClassForm, NoteForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Class, Note, NoteImage
from sqlalchemy import or_
import os
from werkzeug.utils import secure_filename
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import base64
import mimetypes

def get_ocr_text(image_path):
    mimetype, _ = mimetypes.guess_type(image_path)
    if not mimetype or not mimetype.startswith('image'):
        return ""

    with open(image_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

    llm = ChatOpenAI(model="gpt-4.1", max_tokens=2048)

    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": "perform ocr on the image, and return the text in markdown format",
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mimetype};base64,{image_base64}",
                    "detail": "auto",
                },
            },
        ]
    )

    response = llm.invoke([message])
    return response.content

@app.route('/')
@app.route('/index')
@app.route('/index/<int:class_id>')
@login_required
def index(class_id=None):
    classes = Class.query.filter_by(user_id=current_user.id).all()
    if class_id is None and classes:
        selected_class = classes[0]
    else:
        selected_class = Class.query.get(class_id)
    
    notes = []
    if selected_class:
        notes = Note.query.filter_by(class_id=selected_class.id).all()

    return render_template('index.html', title='Home', classes=classes, notes=notes, selected_class=selected_class)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(
            or_(User.username == form.username_or_email.data,
                User.email == form.username_or_email.data)
        ).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username/email or password')
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
    db.session.delete(cl)
    db.session.commit()
    flash('Your class has been deleted!')
    return redirect(url_for('index'))

@app.route('/add_note/<int:class_id>', methods=['GET', 'POST'])
@login_required
def add_note(class_id):
    form = NoteForm()
    if form.validate_on_submit():
        note = Note(date=form.date.data, topics=form.topics.data, class_id=class_id)
        db.session.add(note)
        db.session.commit()

        files = request.files.getlist(form.images.name)
        for f in files:
            if f:
                filename = secure_filename(f.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                f.save(image_path)
                
                ocr_text = get_ocr_text(image_path)
                
                note_image = NoteImage(image_path=filename, ocr_text=ocr_text, note_id=note.id)
                db.session.add(note_image)

        db.session.commit()
        flash('Your note has been added!')
        return redirect(url_for('index', class_id=class_id))
    return render_template('add_note.html', title='Add Note', form=form)

@app.route('/edit_note/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_note(id):
    form = NoteForm()
    note = Note.query.get(id)
    if form.validate_on_submit():
        files = request.files.getlist(form.image.name)
        for f in files:
            if f:
                filename = secure_filename(f.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                f.save(image_path)
                
                ocr_text = get_ocr_text(image_path)
                
                note_image = NoteImage(image_path=filename, ocr_text=ocr_text, note_id=note.id)
                db.session.add(note_image)

        note.date = form.date.data
        note.topics = form.topics.data
        db.session.commit()
        flash('Your note has been updated!')
        return redirect(url_for('index', class_id=note.class_id))
    elif request.method == 'GET':
        form.date.data = note.date
        form.topics.data = note.topics
    return render_template('edit_note.html', title='Edit Note', form=form, note=note)

@app.route('/delete_note/<int:id>')
@login_required
def delete_note(id):
    note = Note.query.get(id)
    class_id = note.class_id
    for image in note.images:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image.image_path))
    db.session.delete(note)
    db.session.commit()
    flash('Your note has been deleted!')
    return redirect(url_for('index', class_id=class_id))

@app.route('/delete_image/<int:id>')
@login_required
def delete_image(id):
    image = NoteImage.query.get(id)
    note_id = image.note_id
    note = Note.query.get(note_id)
    class_id = note.class_id
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image.image_path))
    db.session.delete(image)
    db.session.commit()
    flash('Your image has been deleted!')
    return redirect(url_for('edit_note', id=note_id))
