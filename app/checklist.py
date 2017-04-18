from flask import Flask, session, redirect, url_for, request, render_template, flash, g, abort  # escape
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange  # Length, NumberRange
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
from contextlib import closing
from datetime import datetime
import sqlite3

# TODO Categorie et sous-categorie
# TODO Show checklist
# TODO Sélectionner les vars préd. pour un checklist
# TODO Copier les variables prédéfinies dans le code
# TODO Code snippets
# TODO Génération de checklists remplies

app = Flask(__name__)
manager = Manager(app)
bootstrap = Bootstrap(app)

# Read the configurations
app.config.from_pyfile('config/config.py')
# print(app.config['DATABASE'])
# print(app.config['SQLALCHEMY_DATABASE_URI'])

db = SQLAlchemy(app)


# Database Model
class Admin_User(db.Model):
    __tablename__ = 'tadmin_user'
    user_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    user_email = db.Column(db.String(80), nullable=False, unique=True)
    user_pass = db.Column(db.String(100), nullable=False)
    activated = db.Column(db.Boolean(), nullable=False, default=True)

    def __init__(self, first_name, last_name, user_email, user_pass):
        self.first_name = first_name
        self.last_name = last_name
        self.user_email = user_email
        self.user_pass = user_pass

    def __repr__(self):
        return '<user: {}>'.format(self.user_email)


class Checklist(db.Model):
    __tablename__ = 'tchecklist'
    checklist_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    checklist_name = db.Column(db.String(100), nullable=False, unique=True)
    checklist_desc = db.Column(db.Text(), nullable=False, default='')
    audit_crt_user = db.Column(db.String(80), nullable=False)
    audit_crt_ts = db.Column(db.DateTime(), nullable=False)
    audit_upd_user = db.Column(db.String(80), nullable=True)
    audit_upd_ts = db.Column(db.DateTime(), nullable=True)
    deleted_ind = db.Column(db.String(1), nullable=False, default='N')
    sections = db.relationship('Section', backref='tchecklist', lazy='dynamic')
    cl_vars = db.relationship('Checklist_Var', backref='tchecklist', lazy='dynamic')

    def __init__(self, checklist_name, checklist_desc, audit_crt_user, audit_crt_ts):
        self.checklist_name = checklist_name
        self.checklist_desc = checklist_desc
        self.audit_crt_user = audit_crt_user
        self.audit_crt_ts = audit_crt_ts

    def __repr__(self):
        return '<checklist {}>'.format(self.checklist_name)


class Section(db.Model):
    __tablename__ = 'tcl_section'
    section_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    checklist_id = db.Column(db.Integer(), db.ForeignKey('tchecklist.checklist_id'))
    section_seq = db.Column(db.Integer(), nullable=False)
    section_name = db.Column(db.String(100), nullable=False, default='')
    section_detail = db.Column(db.Text(), nullable=False, default='')
    deleted_ind = db.Column(db.String(1), nullable=False, default='N')
    steps = db.relationship('Step', backref='tcl_section', lazy='dynamic')

    def __init__(self, checklist_id, section_seq, section_name, section_detail):
        self.checklist_id = checklist_id
        self.section_seq = section_seq
        self.section_name = section_name
        self.section_detail = section_detail

    def __repr__(self):
        return '<section {}>'.format(self.section_name)


class Step(db.Model):
    __tablename__ = 'tcl_step'
    step_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    checklist_id = db.Column(db.Integer(), nullable=False)
    section_id = db.Column(db.Integer(), db.ForeignKey('tcl_section.section_id'))
    step_seq = db.Column(db.Integer(), nullable=False)
    step_short = db.Column(db.String(100), nullable=False, default='')
    step_detail = db.Column(db.Text(), nullable=True)
    step_user = db.Column(db.String(16), nullable=True)
    step_code = db.Column(db.Text(), nullable=True)
    deleted_ind = db.Column(db.String(1), nullable=False, default='N')

    def __init__(self, checklist_id, section_id, step_seq, step_short, step_detail, step_user, step_code):
        self.checklist_id = checklist_id
        self.section_id = section_id
        self.step_seq = step_seq
        self.step_short = step_short
        self.step_detail = step_detail
        self.step_user = step_user
        self.step_code = step_code

    def __repr__(self):
        return '<step: {}>'.format(self.step_short)


class Predef_Var(db.Model):
    __tablename__ = 'tpredef_var'
    var_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    var_name = db.Column(db.String(16), nullable=False, unique=True)
    var_desc = db.Column(db.Text(), nullable=True)
    checklists = db.relationship('Checklist_Var', backref='tpredef_var', lazy='dynamic')


    def __init__(self, var_name, var_desc):
        self.var_name = var_name
        self.var_desc = var_desc

    def __repr__(self):
        return '<var: {}>'.format(self.var_name)


class Checklist_Var(db.Model):
    __tablename__ = 'tcl_var'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    checklist_id = db.Column(db.Integer, db.ForeignKey('tchecklist.checklist_id'))
    var_id = db.Column(db.Integer, db.ForeignKey('tpredef_var.var_id'))


# Formulaire web pour l'écran de login
class LoginForm(FlaskForm):
    email = StringField('Courriel', validators=[DataRequired(), Email(message='Le courriel est invalide.')])
    password = PasswordField('Mot de Passe', [DataRequired(message='Le mot de passe est obligatoire.')])
    request_password_change = BooleanField('Changer le mot de passe?')
    password_1 = PasswordField('Nouveau Mot de passe',
                               [EqualTo('password_2', message='Les mots de passe doivent être identiques.')])
    password_2 = PasswordField('Confirmation')
    submit = SubmitField('Se connecter')


# Formulaire web pour l'écran de register
class RegisterForm(FlaskForm):
    first_name = StringField('Prénom', validators=[DataRequired(message='Le prénom est requis.')])
    last_name = StringField('Nom de famille', validators=[DataRequired(message='Le nom de famille est requis.')])
    email = StringField('Courriel', validators=[DataRequired(), Email(message='Le courriel est invalide.')])
    password_1 = PasswordField('Mot de passe',
                               [DataRequired(message='Le mot de passe est obligatoire.'),
                                EqualTo('password_2', message='Les mots de passe doivent être identiques.')])
    password_2 = PasswordField('Confirmation')
    submit = SubmitField('S\'enrégistrer')


# Formulaire d'ajout d'une checklist
class AddChecklistForm(FlaskForm):
    checklist_name = StringField('Nom de la checklist')
    checklist_desc = TextAreaField('Description')
    submit = SubmitField('Ajouter')


# Formulaire d'ajout d'une checklist
class UpdChecklistForm(FlaskForm):
    checklist_name = StringField('Nom de la checklist')
    checklist_desc = TextAreaField('Description')
    submit = SubmitField('Modifier')


# Formulaire pour confirmer la suppression d'une checklist
class DelChecklistForm(FlaskForm):
    submit = SubmitField('Supprimer')


# Formulaire pour ajouter une section à une checklist
class AddSectionForm(FlaskForm):
    section_seq = IntegerField('Séquence', validators=[NumberRange(min=0, message="Doit être un entier positif.")])
    section_name = StringField('Nom de la section')
    section_detail = TextAreaField('Description')
    submit = SubmitField('Ajouter')


# Formulaire pour la mise à jour d'une section
class UpdSectionForm(FlaskForm):
    section_seq = IntegerField('Séquence', validators=[NumberRange(min=0, message="Doit être un entier positif.")])
    section_name = StringField('Nom de la section')
    section_detail = TextAreaField('Description')
    submit = SubmitField('Modifier')


# Formulaire pour confirmer la suppression d'une section
class DelSectionForm(FlaskForm):
    submit = SubmitField('Supprimer')


# Formulaire pour ajouter une section à une checklist
class AddStepForm(FlaskForm):
    step_seq = IntegerField('Séquence', validators=[NumberRange(min=0, message="Doit être un entier positif.")])
    step_short = StringField('Nom du step')
    step_detail = TextAreaField('Explication')
    step_user = StringField('Usager à utiliser pour ce step')
    step_code = TextAreaField('Code')
    submit = SubmitField('Ajouter')


# Formulaire pour la mise à jour d'une section
class UpdStepForm(FlaskForm):
    step_seq = IntegerField('Séquence', validators=[NumberRange(min=0, message="Doit être un entier positif.")])
    step_short = StringField('Nom du step')
    step_detail = TextAreaField('Explication')
    step_user = StringField('Usager à utiliser pour ce step')
    step_code = TextAreaField('Code')
    submit = SubmitField('Modifier')


# Formulaire pour confirmer la suppression d'une section
class DelStepForm(FlaskForm):
    submit = SubmitField('Supprimer')


# Formulaire pour ajouter une variable
class AddVarForm(FlaskForm):
    var_name = StringField('Nom de la variable')
    var_desc = StringField('Description')
    submit = SubmitField('Ajouter')


# Formulaire pour ajouter une variable
class UpdVarForm(FlaskForm):
    var_name = StringField('Nom de la variable')
    var_desc = StringField('Description')
    submit = SubmitField('Modifier')


# Formulaire pour confirmer la suppression d'une variable
class DelVarForm(FlaskForm):
    submit = SubmitField('Supprimer')


# This creates the database connection for each request
@app.before_request
def before_request():
    # g.dbh = connect_db()
    return


# This close the db connection at the end of the requests
@app.teardown_request
def teardown_request(exception):
    dbh = getattr(g, 'dbh', None)
    if dbh is not None:
        dbh.close()


# Custom error pages
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


# The following functions are views
@app.route('/')
def index():
    if not logged_in():
        return redirect(url_for('login'))
    app.logger.debug('Entering index()')
    first_name = session.get('first_name', None)
    return render_template('checklist.html', user=first_name)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # The method is GET when the form is displayed and POST to process the form
    app.logger.debug('Entering login()')
    form = LoginForm()
    if form.validate_on_submit():
        user_email = request.form['email']
        password = request.form['password']
        if db_validate_user(user_email, password):
            session['active_time'] = datetime.now()
            request_pwd_change = request.form.get('request_password_change', None)
            if request_pwd_change:
                app.logger.debug("Changer le mot de passe")
                new_password = request.form['password_1']
                change_password(user_email, new_password)
            return redirect(url_for('index'))
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    app.logger.debug('Entering logout()')
    session.pop('first_name', None)
    session.pop('last_name', None)
    session.pop('user_email', None)
    session.pop('active_time', None)
    flash('Vous êtes maintenant déconnecté.')
    return redirect(url_for('index'))


def logged_in():
    user_email = session.get('user_email', None)
    if user_email:
        active_time = session['active_time']
        delta = datetime.now() - active_time
        if (delta.days > 0) or (delta.seconds > 1800):
            flash('Votre session est expirée.')
            return False
        session['active_time'] = datetime.now()
        return True
    else:
        return False


@app.route('/register', methods=['GET', 'POST'])
def register():
    app.logger.debug('Entering register')
    form = RegisterForm()
    if form.validate_on_submit():
        app.logger.debug('Inserting a new registration')
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        user_email = request.form['email']
        user_pass = generate_password_hash(request.form['password_1'])
        if user_exists(user_email):
            flash('Cet usager existe déjà. Veuillez vous connecter.')
            return redirect(url_for('login'))
        else:
            user = Admin_User(first_name, last_name, user_email, user_pass)
            db.session.add(user)
            db.session.commit()
            flash('Come back when your login will be activated.')
            return redirect(url_for('index'))
    return render_template('register.html', form=form)


@app.route('/list_checklists')
def list_checklists():
    if not logged_in():
        return redirect(url_for('login'))
    checklists = Checklist.query.filter_by(deleted_ind='N').order_by(Checklist.checklist_name).all()
    return render_template('list_checklists.html', checklists=checklists)


@app.route('/add_checklist', methods=['GET', 'POST'])
def add_checklist():
    if not logged_in():
        return redirect(url_for('login'))
    app.logger.debug('Entering add_checklist')
    form = AddChecklistForm()
    if form.validate_on_submit():
        app.logger.debug('Inserting a new checklist')
        checklist_name = request.form['checklist_name']
        checklist_desc = request.form['checklist_desc']
        if db_add_checklist(checklist_name, checklist_desc):
            flash('La nouvelle checklist est ajoutée.')
            return redirect(url_for('list_checklists'))
        else:
            flash('Une erreur de base de données est survenue.')
            abort(500)
    return render_template('add_checklist.html', form=form)


@app.route('/del_checklist/<int:checklist_id>', methods=['GET', 'POST'])
def del_checklist(checklist_id):
    if not logged_in():
        return redirect(url_for('login'))
    form = DelChecklistForm()
    if form.validate_on_submit():
        app.logger.debug('Deleting a checklist')
        if db_del_checklist(checklist_id):
            flash("La checklist a été effacée.")
        else:
            flash("Quelque chose n'a pas fonctionné.")
        return redirect(url_for('list_checklists'))
    else:
        cl = Checklist.query.get(checklist_id)
        if cl:
            return render_template('del_checklist.html', form=form, name=cl.checklist_name)
        else:
            flash("L'information n'a pas pu être retrouvée.")
            return redirect(url_for('list_checklists'))


@app.route('/upd_checklist/<int:checklist_id>', methods=['GET', 'POST'])
def upd_checklist(checklist_id):
    if not logged_in():
        return redirect(url_for('login'))
    session['checklist_id'] = checklist_id
    form = UpdChecklistForm()
    if form.validate_on_submit():
        app.logger.debug('Updating a checklist')
        checklist_name = form.checklist_name.data
        checklist_desc = form.checklist_desc.data
        if db_upd_checklist(checklist_id, checklist_name, checklist_desc):
            flash("La checklist a été modifiée.")
        else:
            flash("Quelque chose n'a pas fonctionné.")
        return redirect(url_for('list_checklists'))
    else:
        cl = Checklist.query.get(checklist_id)
        if cl:
            form.checklist_name.data = cl.checklist_name
            form.checklist_desc.data = cl.checklist_desc
            sections = Section.query.filter_by(checklist_id=checklist_id, deleted_ind='N') \
                .order_by(Section.section_seq).all()
            cl_vars = Checklist_Var.query.filter_by(checklist_id=checklist_id).order_by(Checklist_Var.var_id).all()
            for cl_v in cl_vars:
                pr_v = Predef_Var.query.get(cl_v.var_id)
                cl_v.var_name = pr_v.var_name
                cl_v.var_desc = pr_v.var_desc
            return render_template("upd_checklist.html", form=form, checklist_id=checklist_id,
                                   name=cl.checklist_name, desc=cl.checklist_desc, sections=sections, cl_vars=cl_vars)
        else:
            flash("L'information n'a pas pu être retrouvée.")
            return redirect(url_for('list_checklists'))


@app.route('/show_checklist/<int:checklist_id>')
def show_checklist(checklist_id):
    # TODO Review nested data structure and ORM calls
    if not logged_in():
        return redirect(url_for('login'))
    cl = Checklist.query.get(checklist_id)
    if cl:
        checklist_name = cl.checklist_name
        checklist_desc = cl.checklist_desc
        audit_crt_user = cl.audit_crt_user
        audit_crt_ts = cl.audit_crt_ts
        audit_upd_user = cl.audit_upd_user
        audit_upd_ts = cl.audit_upd_ts
        sections = Section.query.filter_by(checklist_id=checklist_id, deleted_ind='N') \
            .order_by(Section.section_seq).all()
        # l_sections = [ [section_name, [step 1, step 2,...]], [section_name, [step 1, step 2, step 3,...]],...]
        for section in sections:
            section_id = section.section_id
            section_name = section.section_name
            app.logger.debug('for section in sections: ' + str(section_id) + section['section_name'])
            steps = Step.query.filter_by(checklist_id=checklist_id, section_id=section_id, deleted_ind='N') \
                .order_by(Step.step_seq).all()
            section['steps'] = steps
        return render_template("show_checklist.html", name=checklist_name, desc=checklist_desc, crt_user=audit_crt_user,
                               crt_ts=audit_crt_ts, upd_user=audit_upd_user, upd_ts=audit_upd_ts, sections=sections)

    else:
        flash("L'information n'a pas pu être retrouvée.")
        return redirect(url_for('list_checklists'))


@app.route('/add_section', methods=['GET', 'POST'])
def add_section():
    if not logged_in():
        return redirect(url_for('login'))
    checklist_id = session['checklist_id']
    app.logger.debug('Entering add_section')
    form = AddSectionForm()
    if form.validate_on_submit():
        app.logger.debug('Inserting a new section')
        section_seq = request.form['section_seq']
        section_name = request.form['section_name']
        section_detail = request.form['section_detail']
        if db_add_section(checklist_id, section_seq, section_name, section_detail):
            flash('La nouvelle section est ajoutée.')
            return redirect(url_for('upd_checklist', checklist_id=checklist_id))
        else:
            flash('Une erreur de base de données est survenue.')
            abort(500)
    return render_template('add_section.html', form=form, checklist_id=checklist_id)


@app.route('/upd_section/<int:section_id>', methods=['GET', 'POST'])
def upd_section(section_id):
    if not logged_in():
        return redirect(url_for('login'))
    session['section_id'] = section_id
    checklist_id = session['checklist_id']
    form = UpdSectionForm()
    if form.validate_on_submit():
        app.logger.debug('Updating a section')
        section_seq = form.section_seq.data
        section_name = form.section_name.data
        section_detail = form.section_detail.data
        if db_upd_section(section_id, section_seq, section_name, section_detail, checklist_id):
            flash("La section a été modifiée.")
        else:
            flash("Quelque chose n'a pas fonctionné.")
        return redirect(url_for('upd_checklist', checklist_id=checklist_id))
    else:
        sect = Section.query.get(section_id)
        if sect:
            form.section_seq.data = sect.section_seq
            form.section_name.data = sect.section_name
            form.section_detail.data = sect.section_detail
            steps = Step.query.filter_by(section_id=section_id, deleted_ind='N').order_by(Step.step_seq).all()
            return render_template("upd_section.html", form=form, checklist_id=checklist_id,
                                   name=sect.section_name, desc=sect.section_detail, steps=steps)
        else:
            flash("L'information n'a pas pu être retrouvée.")
            return redirect(url_for('upd_checklist', checklist_id=checklist_id))


@app.route('/del_section/<int:section_id>', methods=['GET', 'POST'])
def del_section(section_id):
    if not logged_in():
        return redirect(url_for('login'))
    checklist_id = session['checklist_id']
    form = DelSectionForm()
    if form.validate_on_submit():
        app.logger.debug('Deleting a section')
        if db_del_section(section_id, checklist_id):
            flash("La section a été effacée.")
        else:
            flash("Quelque chose n'a pas fonctionné.")
        return redirect(url_for('upd_checklist', checklist_id=checklist_id))
    else:
        sect = Section.query.get(section_id)
        if sect:
            section_name = sect.section_name
            app.logger.debug(section_name)
            has_steps = Step.query.filter_by(section_id=section_id).first()
            if has_steps:
                flash("Cette section contient des étapes. Elle ne peut pas être supprimée.")
                return redirect(url_for('upd_checklist', checklist_id=checklist_id))
            return render_template('del_section.html', form=form, name=section_name, checklist_id=checklist_id)
        else:
            flash("L'information n'a pas pu être retrouvée.")
            return redirect(url_for('upd_checklist', checklist_id=checklist_id))


@app.route('/add_step', methods=['GET', 'POST'])
def add_step():
    if not logged_in():
        return redirect(url_for('login'))
    checklist_id = session['checklist_id']
    section_id = session['section_id']
    app.logger.debug('Entering add_step')
    form = AddStepForm()
    if form.validate_on_submit():
        app.logger.debug('Inserting a new step')
        step_seq = request.form['step_seq']
        step_short = request.form['step_short']
        step_detail = request.form['step_detail']
        step_user = request.form['step_user']
        step_code = request.form['step_code']
        if db_add_step(checklist_id, section_id, step_seq, step_short, step_detail, step_user, step_code):
            flash('Le nouveau step est ajouté.')
            return redirect(url_for('upd_section', section_id=section_id))
        else:
            flash('Une erreur de base de données est survenue.')
            abort(500)
    return render_template('add_step.html', form=form, checklist_id=checklist_id, section_id=section_id)


@app.route('/del_step/<int:step_id>', methods=['GET', 'POST'])
def del_step(step_id):
    if not logged_in():
        return redirect(url_for('login'))
    section_id = session['section_id']
    form = DelStepForm()
    if form.validate_on_submit():
        app.logger.debug('Deleting a step')
        if db_del_step(step_id, section_id):
            flash("Le step a été effacé.")
        else:
            flash("Quelque chose n'a pas fonctionné.")
        return redirect(url_for('upd_section', section_id=section_id))
    else:
        st = Step.query.get(step_id)
        if st:
            step_short = st.step_short
            return render_template('del_step.html', form=form, name=step_short, section_id=section_id)
        else:
            flash("L'information n'a pas pu être retrouvée.")
            return redirect(url_for('upd_section', section_id=section_id))


@app.route('/upd_step/<int:step_id>', methods=['GET', 'POST'])
def upd_step(step_id):
    if not logged_in():
        return redirect(url_for('login'))
    session['step_id'] = step_id
    section_id = session['section_id']
    form = UpdStepForm()
    if form.validate_on_submit():
        app.logger.debug('Updating a step')
        step_seq = form.step_seq.data
        step_short = form.step_short.data
        step_detail = form.step_detail.data
        step_user = form.step_user.data
        step_code = form.step_code.data
        if db_upd_step(step_id, step_seq, step_short, step_detail, step_user, step_code, section_id):
            flash("Le step a été modifiée.")
        else:
            flash("Quelque chose n'a pas fonctionné.")
        return redirect(url_for('upd_section', section_id=section_id))
    else:
        st = Step.query.get(step_id)
        if st:
            form.step_seq.data = st.step_seq
            form.step_short.data = st.step_short
            form.step_detail.data = st.step_detail
            form.step_user.data = st.step_user
            form.step_code.data = st.step_code
            return render_template("upd_step.html", form=form, section_id=section_id)
        else:
            flash("L'information n'a pas pu être retrouvée.")
            return redirect(url_for('upd_section', section_id=section_id))


@app.route('/list_vars')
def list_vars():
    if not logged_in():
        return redirect(url_for('login'))
    pred_vars = Predef_Var.query.order_by(Predef_Var.var_name).all()
    return render_template('list_vars.html', pred_vars=pred_vars)


@app.route('/add_var', methods=['GET', 'POST'])
def add_var():
    if not logged_in():
        return redirect(url_for('login'))
    app.logger.debug('Entering add_var')
    form = AddVarForm()
    if form.validate_on_submit():
        app.logger.debug('Inserting a new var')
        var_name = request.form['var_name']
        var_desc = request.form['var_desc']
        if db_add_var(var_name, var_desc):
            flash('La nouvelle variable est ajoutée.')
            return redirect(url_for('list_vars'))
        else:
            flash('Une erreur de base de données est survenue.')
            abort(500)
    return render_template('add_var.html', form=form)


@app.route('/del_var/<int:var_id>', methods=['GET', 'POST'])
def del_var(var_id):
    if not logged_in():
        return redirect(url_for('login'))
    form = DelVarForm()
    if form.validate_on_submit():
        app.logger.debug('Deleting a variable')
        if db_del_var(var_id):
            flash("La variable a été effacée.")
        else:
            flash("Quelque chose n'a pas fonctionné.")
        return redirect(url_for('list_vars'))
    else:
        pre_v = Predef_Var.query.get(var_id)
        if pre_v:
            var_name = pre_v.var_name
            return render_template('del_var.html', form=form, name=var_name)
        else:
            flash("L'information n'a pas pu être retrouvée.")
            return redirect(url_for('list_vars'))


@app.route('/upd_var/<int:var_id>', methods=['GET', 'POST'])
def upd_var(var_id):
    if not logged_in():
        return redirect(url_for('login'))
    form = UpdVarForm()
    if form.validate_on_submit():
        app.logger.debug('Updating a step')
        var_name = form.var_name.data
        var_desc = form.var_desc.data
        if db_upd_var(var_id, var_name, var_desc):
            flash("La variable a été modifiée.")
        else:
            flash("Quelque chose n'a pas fonctionné.")
        return redirect(url_for('list_vars'))
    else:
        pre_v = Predef_Var.query.get(var_id)
        if pre_v:
            form.var_name.data = pre_v.var_name
            form.var_desc.data = pre_v.var_desc
            return render_template("upd_var.html", form=form)
        else:
            flash("L'information n'a pas pu être retrouvée.")
            return redirect(url_for('list_vars'))


@app.route('/add_cl_var/<int:checklist_id>')
def add_cl_var(checklist_id, var_id):
    if not logged_in():
        return redirect(url_for('login'))
    return redirect(url_for('list_cl_vars', checklist_id=checklist_id))


@app.route('/del_cl_var/<int:checklist_id>/<int:var_id>')
def del_cl_var(checklist_id, var_id):
    if not logged_in():
        return redirect(url_for('login'))
    cl_v = Checklist_Var.query.filter_by(checklist_id=checklist_id, var_id=var_id).first()
    if cl_v is None:
        flash("L'information n'a pas pu être retrouvée.")
    else:
        db.session.delete(cl_v)
        db.session.commit()
    return redirect(url_for('upd_checklist', checklist_id=checklist_id))


# Database functions

# Connect to the database and return a db handle
# def connect_db():
#     print(app.config['DATABASE'])
#     return sqlite3.connect(app.config['DATABASE'], detect_types=sqlite3.PARSE_DECLTYPES)


# Utility function to create the database from the schema definition in db.sql
# def init_db():
#     with closing(connect_db()) as dbh:
#         with app.open_resource('data/db.sql', mode='r') as f:
#            dbh.cursor().executescript(f.read())
#        dbh.commit()


# Execute a query
# def db_query(query, args=(), one=False):
#    cur = g.dbh.execute(query, args)
#    rv = cur.fetchall()
#    cur.close()
#    return (rv[0] if rv else None) if one else rv


def user_exists(user_email):
    app.logger.debug('Entering user_exists with: ' + user_email)
    user = Admin_User.query.filter_by(user_email=user_email).first()
    if user is None:
        app.logger.debug('user_exists returns False')
        return False
    else:
        app.logger.debug('user_exists returns True' + user[0])
        return True


# Validate if a user is defined in tadmin_user with the proper password.
def db_validate_user(user_email, password):
    user = Admin_User.query.filter_by(user_email=user_email).first()
    if user is None:
        flash("L'usager n'existe pas.")
        return False

    if not user.activated:
        flash("L'usager n'est pas activé.")
        return False

    if check_password_hash(user.user_pass, password):
        session['user_email'] = user.user_email
        session['first_name'] = user.first_name
        session['last_name'] = user.last_name
        return True
    else:
        flash("Mauvais mot de passe!")
        return False


def change_password(user_email, new_password):
    user = Admin_User.query.filter_by(user_email=user_email).first()
    if user is None:
        flash("Mot de passe inchangé. L'usager n'a pas été retrouvé.")
    else:
        user.user_pass = generate_password_hash(new_password)
        db.session.commit()
        flash("Mot de passe changé.")


def db_add_checklist(checklist_name, checklist_desc):
    audit_crt_user = session.get('user_email', None)
    audit_crt_ts = datetime.now()
    cl = Checklist(checklist_name, checklist_desc, audit_crt_user, audit_crt_ts)
    try:
        db.session.add(cl)
        db.session.commit()
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_del_checklist(checklist_id):
    audit_user = session.get('user_email', None)
    try:
        cl = Checklist.query.get(checklist_id)
        cl.deleted_ind = 'Y'
        cl.audit_upd_user = audit_user
        cl.audit_upd_ts = datetime.now()

        sections = Section.query.filter_by(checklist_id=checklist_id).all()
        for section in sections:
            section.deleted_ind = 'Y'

        steps = Step.query.filter_by(checklist_id=checklist_id).all()
        for step in steps:
            step.deleted_ind = 'Y'

        db.session.commit()
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_upd_checklist(checklist_id, checklist_name, checklist_desc):
    audit_user = session.get('user_email', None)
    try:
        cl = Checklist.query.get(checklist_id)
        cl.checklist_desc = checklist_name
        cl.checklist_desc = checklist_desc
        cl.audit_upd_user = audit_user
        cl.audit_upd_ts = datetime.now()
        db.session.commit()
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_add_section(checklist_id, section_seq, section_name, section_detail):
    sect = Section(checklist_id, section_seq, section_name, section_detail)
    try:
        db.session.add(sect)
        if db_renum_section(checklist_id):
            db.session.commit()
        else:
            db.session.rollback()
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_del_section(section_id, checklist_id):
    sect = Section.query.get(section_id)
    try:
        db.session.delete(sect)
        if db_renum_section(checklist_id):
            db.session.commit()
        else:
            db.session.rollback()
            return False
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_upd_section(section_id, section_seq, section_name, section_detail, checklist_id):
    sect = Section.query.get(section_id)
    sect.section_seq = section_seq
    sect.section_name = section_name
    sect.section_detail = section_detail
    try:
        if db_renum_section(checklist_id):
            db.session.commit()
        else:
            db.session.rollback()
            return False
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_renum_section(checklist_id):
    try:
        sections = Section.query.filter_by(checklist_id=checklist_id, deleted_ind='N') \
            .order_by(Section.section_seq).all()
        new_seq = 0
        for section in sections:
            new_seq += 10
            section.section_seq = new_seq
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_add_step(checklist_id, section_id, step_seq, step_short, step_detail, step_user, step_code):
    step = Step(checklist_id, section_id, step_seq, step_short, step_detail, step_user, step_code)
    try:
        db.session.add(step)
        if db_renum_step(section_id):
            db.session.commit()
        else:
            db.session.rollback()
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_del_step(step_id, section_id):
    step = Step.query.get(step_id)
    try:
        db.session.delete(step)
        if db_renum_step(section_id):
            db.session.commit()
        else:
            db.session.rollback()
            return False
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_upd_step(step_id, step_seq, step_short, step_detail, step_user, step_code, section_id):
    step = Step.query.get(step_id)
    step.step_seq = step_seq
    step.step_short = step_short
    step.step_detail = step_detail
    step.step_user = step_user
    step.step_code = step_code
    try:
        if db_renum_step(section_id):
            db.session.commit()
        else:
            db.session.rollback()
            return False
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_renum_step(section_id):
    try:
        steps = Step.query.filter_by(section_id=section_id, deleted_ind='N').order_by(Step.step_seq).all()
        new_seq = 0
        for step in steps:
            new_seq += 10
            step.step_seq = new_seq
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_add_var(var_name, var_desc):
    var = Predef_Var(var_name, var_desc)
    try:
        db.session.add(var)
        db.session.commit()
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_del_var(var_id):
    pre_v = Predef_Var.query.get(var_id)
    try:
        db.session.delete(pre_v)
        db.session.commit()
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_upd_var(var_id, var_name, var_desc):
    pre_v = Predef_Var.query.get(var_id)
    pre_v.var_name = var_name
    pre_v.var_desc = var_desc
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True

# Start the server for the application
if __name__ == '__main__':
    manager.run()
