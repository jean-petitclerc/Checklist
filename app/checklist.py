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

# TODO Categorie et sous-categorie ou des tags
# TODO Reviser les validators dans les formulaires
# TODO Génération de checklists remplies
# TODO Private variables
# TODO Rafraichir une checklist préparée
# TODO Etapes optionelles
# TODO Sélectionner bout de code quand on ajoute une étape
# TODO Modifier le code dans une checklist préparée
# TODO print pdf

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
    snippets = db.relationship('Code_Snippet_Var', backref='tpredef_var', lazy='dynamic')


    def __init__(self, var_name, var_desc):
        self.var_name = var_name
        self.var_desc = var_desc

    def __repr__(self):
        return '<var: {}>'.format(self.var_name)


class Checklist_Var(db.Model):
    __tablename__ = 'tcl_var'
    cl_v_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    checklist_id = db.Column(db.Integer, db.ForeignKey('tchecklist.checklist_id'))
    var_id = db.Column(db.Integer, db.ForeignKey('tpredef_var.var_id'))

    def __init__(self, checklist_id, var_id):
        self.checklist_id = checklist_id
        self.var_id = var_id

    def __repr__(self):
        return '<checklist_var: {}:{}>'.format(self.checklist_id, self.var_id)


class Code_Snippet(db.Model):
    __tablename__ = 'tcode_snippet'
    snip_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    snip_name = db.Column(db.String(100), nullable=False, unique=True)
    snip_desc = db.Column(db.Text(), nullable=False, default='')
    snip_code = db.Column(db.Text)
    audit_crt_user = db.Column(db.String(80), nullable=False)
    audit_crt_ts = db.Column(db.DateTime(), nullable=False)
    audit_upd_user = db.Column(db.String(80), nullable=True)
    audit_upd_ts = db.Column(db.DateTime(), nullable=True)
    deleted_ind = db.Column(db.String(1), nullable=False, default='N')
    snip_vars = db.relationship('Code_Snippet_Var', backref='tcode_snippet', lazy='dynamic')

    def __init__(self, snip_name, snip_desc, snip_code, audit_crt_user, audit_crt_ts):
        self.snip_name = snip_name
        self.snip_desc = snip_desc
        self.snip_code = snip_code
        self.audit_crt_user = audit_crt_user
        self.audit_crt_ts = audit_crt_ts

    def __repr__(self):
        return '<code_snippet: {}>'.format(self.snip_name)


class Code_Snippet_Var(db.Model):
    __tablename__ = 'tcode_snippet_var'
    snip_var_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    snip_id = db.Column(db.Integer, db.ForeignKey('tcode_snippet.snip_id'))
    var_id = db.Column(db.Integer, db.ForeignKey('tpredef_var.var_id'))

    def __init__(self, snip_id, var_id):
        self.snip_id = snip_id
        self.var_id = var_id

    def __repr__(self):
        return '<code_snippet_var: {}:{}>'.format(self.snip_id, self.var_id)


class Prepared_Checklist(db.Model):
    __tablename__ = 'tprep_checklist'
    prep_cl_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prep_cl_name = db.Column(db.String(80), nullable=False, unique=True)
    prep_cl_desc = db.Column(db.Text)
    checklist_id = db.Column(db.Integer)
    audit_crt_user = db.Column(db.String(80), nullable=False)
    audit_crt_ts = db.Column(db.DateTime(), nullable=False)
    cl_vars = db.relationship('Prepared_Checklist_Var', backref='tprep_checklist', lazy='dynamic')

    def __init__(self, prep_cl_name, prep_cl_desc, checklist_id, audit_crt_user, audit_crt_ts):
        self.prep_cl_name = prep_cl_name
        self.prep_cl_desc = prep_cl_desc
        self.checklist_id = checklist_id
        self.audit_crt_user = audit_crt_user
        self.audit_crt_ts = audit_crt_ts


class Prepared_Checklist_Var(db.Model):
    __tablename__ = 'tprep_cl_var'
    prep_cl_var_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prep_cl_id = db.Column(db.Integer, db.ForeignKey('tprep_checklist.prep_cl_id'))
    var_id = db.Column(db.Integer)
    var_name = db.Column(db.String(16), nullable=False)
    var_value = db.Column(db.String(80), nullable=False, default='')

    def __init__(self, prep_cl_id, var_id, var_name, var_value):
        self.prep_cl_id = prep_cl_id
        self.var_id = var_id
        self.var_name = var_name
        self.var_value = var_value


class Prepared_CL_Section(db.Model):
    __tablename__ = 'tprep_cl_section'
    prep_cl_sect_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    prep_cl_id = db.Column(db.Integer(), db.ForeignKey('tprep_checklist.prep_cl_id'))
    section_id = db.Column(db.Integer(), nullable=False)
    section_seq = db.Column(db.Integer(), nullable=False)
    section_name = db.Column(db.String(100), nullable=False, default='')
    section_detail = db.Column(db.Text(), nullable=False, default='')
    steps = db.relationship('Prepared_CL_Step', backref='tprep_cl_section', lazy='dynamic')

    def __init__(self, prep_cl_id, section_id, section_seq, section_name, section_detail):
        self.prep_cl_id = prep_cl_id
        self.section_id = section_id
        self.section_seq = section_seq
        self.section_name = section_name
        self.section_detail = section_detail

    def __repr__(self):
        return '<prep_section {}>'.format(self.section_name)


class Prepared_CL_Step(db.Model):
    __tablename__ = 'tprep_cl_step'
    prep_cl_step_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    prep_cl_sect_id = db.Column(db.Integer(), db.ForeignKey('tprep_cl_section.prep_cl_sect_id'))
    step_id = db.Column(db.Integer(), nullable=False)
    step_seq = db.Column(db.Integer(), nullable=False)
    step_short = db.Column(db.String(100), nullable=False, default='')
    step_detail = db.Column(db.Text(), nullable=True)
    step_user = db.Column(db.String(16), nullable=True)
    step_code = db.Column(db.Text(), nullable=True)
    status_ind = db.Column(db.String(1), nullable=False, default='N')

    def __init__(self, prep_cl_sect_id, step_id, step_seq, step_short, step_detail, step_user, step_code):
        self.prep_cl_sect_id = prep_cl_sect_id
        self.step_id = step_id
        self.step_seq = step_seq
        self.step_short = step_short
        self.step_detail = step_detail
        self.step_user = step_user
        self.step_code = step_code

    def __repr__(self):
        return '<prep_step {}>'.format(self.step_short)


class Prepared_Snippet(db.Model):
    __tablename__ = 'tprep_snippet'
    prep_snip_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prep_snip_name = db.Column(db.String(80), nullable=False, unique=True)
    prep_snip_desc = db.Column(db.Text)
    prep_snip_code = db.Column(db.Text)
    snip_id = db.Column(db.Integer)
    audit_crt_user = db.Column(db.String(80), nullable=False)
    audit_crt_ts = db.Column(db.DateTime(), nullable=False)
    snip_vars = db.relationship('Prepared_Snippet_Var', backref='tprep_snippet', lazy='dynamic')

    def __init__(self, prep_snip_name, prep_snip_desc, prep_snip_code, snip_id, audit_crt_user, audit_crt_ts):
        self.prep_snip_name = prep_snip_name
        self.prep_snip_desc = prep_snip_desc
        self.prep_snip_code = prep_snip_code
        self.snip_id = snip_id
        self.audit_crt_user = audit_crt_user
        self.audit_crt_ts = audit_crt_ts

    def __repr__(self):
        return '<prep_snippet {}>'.format(self.prep_snip_name)


class Prepared_Snippet_Var(db.Model):
    __tablename__ = 'tprep_snip_var'
    prep_snip_var_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prep_snip_id = db.Column(db.Integer, db.ForeignKey('tprep_snippet.prep_snip_id'))
    var_id = db.Column(db.Integer)
    var_name = db.Column(db.String(16), nullable=False)
    var_value = db.Column(db.String(80), nullable=False, default='')

    def __init__(self, prep_snip_id, var_id, var_name, var_value):
        self.prep_snip_id = prep_snip_id
        self.var_id = var_id
        self.var_name = var_name
        self.var_value = var_value


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
    checklist_name = StringField('Nom de la checklist', validators=[DataRequired(message='Le nom est requis.')])
    checklist_desc = TextAreaField('Description')
    submit = SubmitField('Ajouter')


# Formulaire d'ajout d'une checklist
class UpdChecklistForm(FlaskForm):
    checklist_name = StringField('Nom de la checklist', validators=[DataRequired(message='Le nom est requis.')])
    checklist_desc = TextAreaField('Description')
    submit = SubmitField('Modifier')


# Formulaire pour confirmer la suppression d'une checklist
class DelChecklistForm(FlaskForm):
    submit = SubmitField('Supprimer')


# Formulaire pour ajouter une checklist préparée
class AddPrepChecklistForm(FlaskForm):
    prep_cl_name = StringField('Nom', validators=[DataRequired(message='Le nom est requis.')])
    prep_cl_desc = TextAreaField('Description')
    submit = SubmitField('Créer')


# Formulaire pour modifier une checklist préparée
class UpdPrepChecklistForm(FlaskForm):
    prep_cl_name = StringField('Nom', validators=[DataRequired(message='Le nom est requis.')])
    prep_cl_desc = TextAreaField('Description')
    submit = SubmitField('Modifier')


# Formulaire pour confirmer la suppression d'une checklist préparée
class DelPrepChecklistForm(FlaskForm):
    submit = SubmitField('Supprimer')


# Formulaire pour confirmer la suppression d'une checklist préparée
class DelPrepSnippetForm(FlaskForm):
    submit = SubmitField('Supprimer')


# Formulaire pour assigner une valeur à une Prepared_Checklist_var
class UpdPrepChecklistVarForm(FlaskForm):
    var_value = StringField('Fournir une valeur')
    submit = SubmitField('Assigner')


# Formulaire pour ajouter une checklist préparée
class AddPrepSnippettForm(FlaskForm):
    prep_snip_name = StringField('Nom', validators=[DataRequired(message='Le nom est requis.')])
    prep_snip_desc = TextAreaField('Description')
    submit = SubmitField('Créer')


# Formulaire pour modifier une checklist préparée
class UpdPrepSnippetForm(FlaskForm):
    prep_snip_name = StringField('Nom', validators=[DataRequired(message='Le nom est requis.')])
    prep_snip_desc = TextAreaField('Description')
    prep_snip_code = TextAreaField('Code Préparé')
    submit = SubmitField('Modifier')


# Formulaire pour assigner une valeur à une Prepared_Checklist_var
class UpdPrepSnippetVarForm(FlaskForm):
    var_value = StringField('Fournir une valeur')
    submit = SubmitField('Assigner')


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


# Formulaire pour ajouter un bout de code
class AddSnippetForm(FlaskForm):
    snip_name = StringField('Nom')
    snip_desc = TextAreaField('Courte description')
    snip_code = TextAreaField('Code')
    submit = SubmitField('Ajouter')


# Formulaire pour ajouter un bout de code
class UpdSnippetForm(FlaskForm):
    snip_name = StringField('Nom')
    snip_desc = TextAreaField('Courte description')
    snip_code = TextAreaField('Code')
    submit = SubmitField('Modifier')


# Formulaire pour confirmer la suppression d'un bout de code
class DelSnippetForm(FlaskForm):
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
    if not logged_in():
        return redirect(url_for('login'))
    cl = Checklist.query.get(checklist_id)
    if cl:
        q_sections = Section.query.filter_by(checklist_id=checklist_id, deleted_ind='N') \
            .order_by(Section.section_seq).all()
        q_cl_vars = Checklist_Var.query.filter_by(checklist_id=checklist_id).all()
        cl_vars = []
        for q_cl_v in q_cl_vars:
            cl_var = dict()
            q_p_var = Predef_Var.query.get(q_cl_v.var_id)
            app.logger.debug('var name: ' + q_p_var.var_name)
            cl_var['name'] = q_p_var.var_name
            cl_var['desc'] = q_p_var.var_desc
            cl_vars.append(cl_var)

        # l_sections = [ [section_name, [step 1, step 2,...]], [section_name, [step 1, step 2, step 3,...]],...]
        sections = []
        for q_section in q_sections:
            section = dict()
            section['id'] = q_section.section_id
            section['seq'] = q_section.section_seq
            section['name'] = q_section.section_name
            section['detail'] = q_section.section_detail
            q_steps = Step.query.filter_by(checklist_id=checklist_id, section_id=section['id'], deleted_ind='N') \
                .order_by(Step.step_seq).all()
            steps = []
            for q_step in q_steps:
                step = dict()
                step['id'] = q_step.step_id
                step['seq'] = q_step.step_seq
                step['short'] = q_step.step_short
                step['detail'] = q_step.step_detail
                step['user'] = q_step.step_user
                step['code'] = q_step.step_code
                steps.append(step)
            section['steps'] = steps
            sections.append(section)
        return render_template("show_checklist.html", cl=cl, cl_vars=cl_vars, sections=sections)

    else:
        flash("L'information n'a pas pu être retrouvée.")
        return redirect(url_for('list_checklists'))


@app.route('/list_prep_checklists')
def list_prep_checklists():
    if not logged_in():
        return redirect(url_for('login'))
    checklists = Prepared_Checklist.query.order_by(Prepared_Checklist.prep_cl_name).all()
    return render_template('list_prep_checklists.html', checklists=checklists)


@app.route('/add_prep_cl/<int:checklist_id>', methods=['GET', 'POST'])
def add_prep_cl(checklist_id):
    if not logged_in():
        return redirect(url_for('login'))
    app.logger.debug('Entering add_prep_cl')
    form = AddPrepChecklistForm()
    if form.validate_on_submit():
        prep_cl_name = request.form['prep_cl_name']
        prep_cl_desc = request.form['prep_cl_desc']
        prep_cl_id = db_add_prep_cl(prep_cl_name, prep_cl_desc, checklist_id)
        if prep_cl_id is not None:
            flash('La nouvelle checklist est ajoutée.')
            return redirect(url_for('upd_prep_cl', prep_cl_id=prep_cl_id))
        else:
            flash('Une erreur de base de données est survenue.')
            abort(500)
    else:
        cl = Checklist.query.get(checklist_id)
        form.prep_cl_name.data = cl.checklist_name + ' - <Object> - ...'
        return render_template('add_prep_cl.html', form=form)


@app.route('/list_prep_snippets')
def list_prep_snippets():
    if not logged_in():
        return redirect(url_for('login'))
    snippets = Prepared_Snippet.query.order_by(Prepared_Snippet.prep_snip_name).all()
    return render_template('list_prep_snippets.html', snippets=snippets)


@app.route('/add_prep_snippet/<int:snip_id>', methods=['GET', 'POST'])
def add_prep_snippet(snip_id):
    if not logged_in():
        return redirect(url_for('login'))
    app.logger.debug('Entering add_prep_snip')
    form = AddPrepSnippettForm()
    if form.validate_on_submit():
        prep_snip_name = request.form['prep_snip_name']
        prep_snip_desc = request.form['prep_snip_desc']
        snippet = Code_Snippet.query.get(snip_id)
        if snippet:
            prep_snip_code = snippet.snip_code
        else:
            prep_snip_code = " "
        prep_snip_id = db_add_prep_snip(prep_snip_name, prep_snip_desc, prep_snip_code, snip_id)
        if prep_snip_id is not None:
            flash('Le nouveau snippet est ajouté.')
            return redirect(url_for('upd_prep_snippet', prep_snip_id=prep_snip_id))
        else:
            flash('Une erreur de base de données est survenue.')
            abort(500)
    else:
        snippet = Code_Snippet.query.get(snip_id)
        form.prep_snip_name.data = snippet.snip_name + ' - <Object> - ...'
        form.prep_snip_desc.data = snippet.snip_desc
        return render_template('add_prep_snip.html', form=form)


@app.route('/upd_prep_snippet/<int:prep_snip_id>', methods=['GET', 'POST'])
def upd_prep_snippet(prep_snip_id):
    if not logged_in():
        return redirect(url_for('login'))
    app.logger.debug('Entering upd_prep_snippet')
    session['prep_snip_id'] = prep_snip_id
    form = UpdPrepSnippetForm()
    if form.validate_on_submit():
        app.logger.debug('Updating a prepared snippet')
        prep_snip_name = form.prep_snip_name.data
        prep_snip_desc = form.prep_snip_desc.data
        prep_snip_code = form.prep_snip_code.data
        if db_upd_prep_snip(prep_snip_id, prep_snip_name, prep_snip_desc, prep_snip_code):
            flash("Le snippet a été modifié.")
        else:
            flash("Quelque chose n'a pas fonctionné.")
        return redirect(url_for('upd_prep_snippet', prep_snip_id=prep_snip_id))
    else:
        p_snip = Prepared_Snippet.query.get(prep_snip_id)
        if p_snip:
            snippet = Code_Snippet.query.get(p_snip.snip_id)
            form.prep_snip_name.data = p_snip.prep_snip_name
            form.prep_snip_desc.data = p_snip.prep_snip_desc
            form.prep_snip_code.data = p_snip.prep_snip_code
            p_snip_vars = Prepared_Snippet_Var.query.filter_by(prep_snip_id=prep_snip_id) \
                .order_by(Prepared_Snippet_Var.var_name).all()
            return render_template("upd_prep_snip.html", form=form, p_snip_vars=p_snip_vars, snippet=snippet)
        else:
            flash("L'information n'a pas pu être retrouvée.")
            return redirect(url_for('list_snippets_short'))


@app.route('/upd_prep_snippet_var/<int:prep_snip_var_id>', methods=['GET', 'POST'])
def upd_prep_snippet_var(prep_snip_var_id):
    if not logged_in():
        return redirect(url_for('login'))
    prep_snip_id = session['prep_snip_id']
    form = UpdPrepSnippetVarForm()
    if form.validate_on_submit():
        app.logger.debug('Updating a prepared snippet var')
        var_value = form.var_value.data
        if db_upd_prep_snip_var(prep_snip_var_id, var_value, prep_snip_id):
            flash("La valeur a été assignée.")
        else:
            flash("Quelque chose n'a pas fonctionné.")
        return redirect(url_for('upd_prep_snippet', prep_snip_id=prep_snip_id))
    else:
        p_snip_var = Prepared_Snippet_Var.query.get(prep_snip_var_id)
        var_name = p_snip_var.var_name
        pred_var = Predef_Var.query.get(p_snip_var.var_id)
        if pred_var:
            var_desc = pred_var.var_desc
            form.var_value.data = p_snip_var.var_value
            return render_template("upd_prep_snip_var.html", form=form, var_name=var_name, var_desc=var_desc,
                                   prep_snip_id=prep_snip_id)
        else:
            flash("L'information n'a pas pu être retrouvée.")
            return redirect(url_for('upd_prep_snippet', prep_snip_id=prep_snip_id))


@app.route('/del_prep_snippet/<int:prep_snip_id>', methods=['GET', 'POST'])
def del_prep_snippet(prep_snip_id):
    if not logged_in():
        return redirect(url_for('login'))
    form = DelPrepSnippetForm()
    if form.validate_on_submit():
        app.logger.debug('Deleting a prepared snippet')
        if db_del_prep_snip(prep_snip_id):
            flash("Le snippet a été effacé.")
        else:
            flash("Quelque chose n'a pas fonctionné.")
        return redirect(url_for('list_prep_snippets'))
    else:
        p_snip = Prepared_Snippet.query.get(prep_snip_id)
        if p_snip:
            return render_template('del_prep_snip.html', form=form, name=p_snip.prep_snip_name)
        else:
            flash("L'information n'a pas pu être retrouvée.")
            return redirect(url_for('list_prep_snippets'))


@app.route('/show_prep_snippet/<int:prep_snip_id>', methods=['GET', 'POST'])
def show_prep_snippet(prep_snip_id):
    if not logged_in():
        return redirect(url_for('login'))
    p_snip = Prepared_Snippet.query.get(prep_snip_id)
    #app.logger.debug('Prep_Snippet: ' + str(p_snip))
    if p_snip:
        q_snip_vars = Prepared_Snippet_Var.query.filter_by(prep_snip_id=prep_snip_id).all()
        p_snip_vars = []
        for q_snip_var in q_snip_vars:
            app.logger.debug('q_snip_var:' + str(q_snip_var.var_id))
            p_snip_var = dict()
            q_p_var = Predef_Var.query.get(q_snip_var.var_id)
            app.logger.debug('var name: ' + q_p_var.var_name)
            p_snip_var['name'] = q_p_var.var_name
            p_snip_var['value'] = q_snip_var.var_value
            p_snip_vars.append(p_snip_var)
        return render_template("show_prep_snippet.html", p_snip=p_snip, p_snip_vars=p_snip_vars)
    else:
        flash("L'information n'a pas pu être retrouvée.")
        return redirect(url_for('list_prep_checklists'))



@app.route('/del_prep_cl/<int:prep_cl_id>', methods=['GET', 'POST'])
def del_prep_cl(prep_cl_id):
    if not logged_in():
        return redirect(url_for('login'))
    form = DelPrepChecklistForm()
    if form.validate_on_submit():
        app.logger.debug('Deleting a prepared checklist')
        if db_del_prep_cl(prep_cl_id):
            flash("La checklist a été effacée.")
        else:
            flash("Quelque chose n'a pas fonctionné.")
        return redirect(url_for('list_prep_checklists'))
    else:
        cl = Prepared_Checklist.query.get(prep_cl_id)
        if cl:
            return render_template('del_prep_cl.html', form=form, name=cl.prep_cl_name)
        else:
            flash("L'information n'a pas pu être retrouvée.")
            return redirect(url_for('list_prep_checklists'))


@app.route('/show_prep_checklist/<int:prep_cl_id>')
def show_prep_checklist(prep_cl_id):
    if not logged_in():
        return redirect(url_for('login'))
    cl = Prepared_Checklist.query.get(prep_cl_id)
    if cl:
        q_sections = Section.query.filter_by(checklist_id=cl.checklist_id, deleted_ind='N') \
            .order_by(Section.section_seq).all()
        q_cl_vars = Prepared_Checklist_Var.query.filter_by(prep_cl_id=prep_cl_id).all()
        cl_vars = []
        for q_cl_v in q_cl_vars:
            cl_var = dict()
            q_p_var = Predef_Var.query.get(q_cl_v.var_id)
            app.logger.debug('var name: ' + q_p_var.var_name)
            cl_var['name'] = q_cl_v.var_name
            cl_var['value'] = q_cl_v.var_value
            cl_vars.append(cl_var)

        # l_sections = [ [section_name, [step 1, step 2,...]], [section_name, [step 1, step 2, step 3,...]],...]
        sections = []
        for q_section in q_sections:
            section = dict()
            section['id'] = q_section.section_id
            section['seq'] = q_section.section_seq
            section['name'] = q_section.section_name
            section['detail'] = q_section.section_detail
            q_steps = Step.query.filter_by(checklist_id=cl.checklist_id, section_id=section['id'], deleted_ind='N') \
                .order_by(Step.step_seq).all()
            steps = []
            for q_step in q_steps:
                step = dict()
                step['id'] = q_step.step_id
                step['seq'] = q_step.step_seq
                step['short'] = q_step.step_short
                step['detail'] = q_step.step_detail
                step['user'] = q_step.step_user
                step['code'] = replace_vars_in_code(q_step.step_code, cl_vars)
                steps.append(step)
            section['steps'] = steps
            sections.append(section)
        return render_template("show_prep_checklist.html", cl=cl, cl_vars=cl_vars, sections=sections)
    else:
        flash("L'information n'a pas pu être retrouvée.")
        return redirect(url_for('list_prep_checklists'))


def replace_vars_in_code(code, vars):
    for cl_v in vars:
        if cl_v['value'] is not None:
            code = code.replace(cl_v['name'], cl_v['value'])
    return code


@app.route('/upd_prep_cl/<int:prep_cl_id>', methods=['GET', 'POST'])
def upd_prep_cl(prep_cl_id):
    if not logged_in():
        return redirect(url_for('login'))
    app.logger.debug('Entering upd_prep_cl')
    session['prep_cl_id'] = prep_cl_id
    form = UpdPrepChecklistForm()
    if form.validate_on_submit():
        app.logger.debug('Updating a prepared checklist')
        prep_cl_name = form.prep_cl_name.data
        prep_cl_desc = form.prep_cl_desc.data
        if db_upd_prep_cl(prep_cl_id, prep_cl_name, prep_cl_desc):
            flash("La checklist a été modifiée.")
        else:
            flash("Quelque chose n'a pas fonctionné.")
        return redirect(url_for('upd_prep_cl', prep_cl_id=prep_cl_id))
    else:
        p_cl = Prepared_Checklist.query.get(prep_cl_id)
        if p_cl:
            form.prep_cl_name.data = p_cl.prep_cl_name
            form.prep_cl_desc.data = p_cl.prep_cl_desc
            cl_vars = Prepared_Checklist_Var.query.filter_by(prep_cl_id=prep_cl_id) \
                .order_by(Prepared_Checklist_Var.var_name).all()
            return render_template("upd_prep_cl.html", form=form, cl_vars=cl_vars)
        else:
            flash("L'information n'a pas pu être retrouvée.")
            return redirect(url_for('list_checklists'))


@app.route('/upd_prep_cl_var/<int:prep_cl_var_id>', methods=['GET', 'POST'])
def upd_prep_cl_var(prep_cl_var_id):
    if not logged_in():
        return redirect(url_for('login'))
    prep_cl_id = session['prep_cl_id']
    form = UpdPrepChecklistVarForm()
    if form.validate_on_submit():
        app.logger.debug('Updating a prepared checklist var')
        var_value = form.var_value.data
        if db_upd_prep_cl_var(prep_cl_var_id, var_value):
            flash("La valeur a été assignée.")
        else:
            flash("Quelque chose n'a pas fonctionné.")
        return redirect(url_for('upd_prep_cl', prep_cl_id=prep_cl_id))
    else:
        cl_v = Prepared_Checklist_Var.query.get(prep_cl_var_id)
        var_name = cl_v.var_name
        pre_v = Predef_Var.query.get(cl_v.var_id)
        if pre_v:
            var_desc = pre_v.var_desc
            form.var_value.data = cl_v.var_value
            return render_template("upd_prep_cl_var.html", form=form, var_name=var_name, var_desc=var_desc,
                                   prep_cl_id=prep_cl_id)
        else:
            flash("L'information n'a pas pu être retrouvée.")
            return redirect(url_for('upd_prep_cl', prep_cl_id=prep_cl_id))


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
    checklist_id = session['checklist_id']
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
            cl_vars = Checklist_Var.query.filter_by(checklist_id=checklist_id).all()
            for cl_v in cl_vars:
                p_var = Predef_Var.query.get(cl_v.var_id)
                cl_v.var_name = p_var.var_name
            return render_template("upd_step.html", form=form, section_id=section_id, step_id=step_id, cl_vars=cl_vars)
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


@app.route('/sel_cl_vars/<int:checklist_id>')
def sel_cl_vars(checklist_id):
    if not logged_in():
        return redirect(url_for('login'))
    l_vars = Predef_Var.query.order_by(Predef_Var.var_name).all()
    s_vars = []
    for p_var in l_vars:
        c_var = Checklist_Var.query.filter_by(checklist_id=checklist_id, var_id=p_var.var_id).first()
        if c_var is None:
            s_vars.append(p_var)
    return render_template('sel_cl_vars.html', checklist_id=checklist_id, s_vars=s_vars)


@app.route('/sel_snip_vars/<int:snip_id>')
def sel_snip_vars(snip_id):
    if not logged_in():
        return redirect(url_for('login'))
    l_vars = Predef_Var.query.order_by(Predef_Var.var_name).all()
    s_vars = []
    for p_var in l_vars:
        c_var = Code_Snippet_Var.query.filter_by(snip_id=snip_id, var_id=p_var.var_id).first()
        if c_var is None:
            s_vars.append(p_var)
    return render_template('sel_snip_vars.html', snip_id=snip_id, s_vars=s_vars)


@app.route('/add_cl_var/<int:checklist_id>/<int:var_id>')
def add_cl_var(checklist_id, var_id):
    if not logged_in():
        return redirect(url_for('login'))
    if db_add_cl_var(checklist_id, var_id):
        flash('La nouvelle variable est ajoutée à la checklist.')
    else:
        flash('Une erreur de base de données est survenue.')
        abort(500)
    return redirect(url_for('upd_checklist', checklist_id=checklist_id))


@app.route('/add_snip_var/<int:snip_id>/<int:var_id>')
def add_snip_var(snip_id, var_id):
    if not logged_in():
        return redirect(url_for('login'))
    if db_add_snip_var(snip_id, var_id):
        flash('La nouvelle variable est ajoutée au snippet.')
    else:
        flash('Une erreur de base de données est survenue.')
        abort(500)
    return redirect(url_for('upd_snippet', snip_id=snip_id))


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


@app.route('/del_snip_var/<int:snip_id>/<int:var_id>')
def del_snip_var(snip_id, var_id):
    if not logged_in():
        return redirect(url_for('login'))
    snip_var = Code_Snippet_Var.query.filter_by(snip_id=snip_id, var_id=var_id).first()
    if snip_var is None:
        flash("L'information n'a pas pu être retrouvée.")
    else:
        db.session.delete(snip_var)
        db.session.commit()
    return redirect(url_for('upd_snippet', snip_id=snip_id))


@app.route('/list_snippets')
def list_snippets():
    if not logged_in():
        return redirect(url_for('login'))
    snippets = Code_Snippet.query.order_by(Code_Snippet.snip_name).all()
    return render_template('list_snippets.html', snippets=snippets)


@app.route('/list_snippets_short')
def list_snippets_short():
    if not logged_in():
        return redirect(url_for('login'))
    snippets = Code_Snippet.query.order_by(Code_Snippet.snip_name).all()
    return render_template('list_snippets_short.html', snippets=snippets)


@app.route('/show_snippet/<int:snip_id>')
def show_snippet(snip_id):
    if not logged_in():
        return redirect(url_for('login'))

    snippet = Code_Snippet.query.filter_by(snip_id=snip_id).first()
    if snippet:
        q_snip_vars = Code_Snippet_Var.query.filter_by(snip_id=snip_id).all()
        snip_vars = []
        for q_snip_var in q_snip_vars:
            snip_var = dict()
            q_p_var = Predef_Var.query.get(q_snip_var.var_id)
            #app.logger.debug('var name: ' + q_p_var.var_name)
            snip_var['name'] = q_p_var.var_name
            snip_var['desc'] = q_p_var.var_desc
            snip_vars.append(snip_var)
        return render_template('show_snippet.html', snippet=snippet, snip_id=snip_id, snip_vars=snip_vars)
    else:
        flash("L'information n'a pas pu être retrouvée.")
        return redirect(url_for('list_snippets_short'))


@app.route('/add_snippet', methods=['GET', 'POST'])
def add_snippet():
    if not logged_in():
        return redirect(url_for('login'))
    app.logger.debug('Entering add_snippet')
    form = AddSnippetForm()
    if form.validate_on_submit():
        snip_name = request.form['snip_name']
        snip_desc = request.form['snip_desc']
        snip_code = request.form['snip_code']
        if db_add_snippet(snip_name, snip_desc, snip_code):
            flash('Le nouveau bout de code est ajouté.')
            return redirect(url_for('list_snippets'))
        else:
            flash('Une erreur de base de données est survenue.')
            abort(500)
    return render_template('add_snippet.html', form=form)


@app.route('/upd_snippet/<int:snip_id>', methods=['GET', 'POST'])
def upd_snippet(snip_id):
    if not logged_in():
        return redirect(url_for('login'))
    form = UpdSnippetForm()
    if form.validate_on_submit():
        app.logger.debug('Updating a snippet')
        snip_name = form.snip_name.data
        snip_desc = form.snip_desc.data
        snip_code = form.snip_code.data
        if db_upd_snippet(snip_id, snip_name, snip_desc, snip_code):
            flash("Le bout de code a été modifié.")
        else:
            flash("Quelque chose n'a pas fonctionné.")
        return redirect(url_for('list_snippets'))
    else:
        snippet = Code_Snippet.query.get(snip_id)
        if snippet:
            form.snip_name.data = snippet.snip_name
            form.snip_desc.data = snippet.snip_desc
            form.snip_code.data = snippet.snip_code
            snip_vars = Code_Snippet_Var.query.filter_by(snip_id=snip_id).order_by(Code_Snippet_Var.var_id).all()
            for snip_var in snip_vars:
                pr_v = Predef_Var.query.get(snip_var.var_id)
                snip_var.var_name = pr_v.var_name
                snip_var.var_desc = pr_v.var_desc
            return render_template("upd_snippet.html", form=form, snip_id=snip_id, snip_vars=snip_vars)
        else:
            flash("L'information n'a pas pu être retrouvée.")
            return redirect(url_for('list_snippets'))


@app.route('/del_snippet/<int:snip_id>', methods=['GET', 'POST'])
def del_snippet(snip_id):
    if not logged_in():
        return redirect(url_for('login'))
    form = DelSnippetForm()
    if form.validate_on_submit():
        app.logger.debug('Deleting a snippet')
        if db_del_snippet(snip_id):
            flash("Le bout de code a été effacé.")
        else:
            flash("Quelque chose n'a pas fonctionné.")
        return redirect(url_for('list_snippets'))
    else:
        snippet = Code_Snippet.query.get(snip_id)
        if snippet:
            snip_name = snippet.snip_name
            return render_template('del_snippet.html', form=form, name=snip_name)
        else:
            flash("L'information n'a pas pu être retrouvée.")
            return redirect(url_for('list_snippets'))


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


def db_add_prep_cl(prep_cl_name, prep_cl_desc, checklist_id):
    audit_crt_user = session.get('user_email', None)
    audit_crt_ts = datetime.now()
    p_cl = Prepared_Checklist(prep_cl_name, prep_cl_desc, checklist_id, audit_crt_user, audit_crt_ts)
    try:
        db.session.add(p_cl)
        cl_vars = Checklist_Var.query.filter_by(checklist_id=checklist_id).all()
        for cl_v in cl_vars:
            pred_var = Predef_Var.query.filter_by(var_id=cl_v.var_id).first()
            var_name = pred_var.var_name
            app.logger.debug(var_name)
            p_cl_var = Prepared_Checklist_Var(p_cl.prep_cl_id, cl_v.var_id, var_name, None)
            db.session.add(p_cl_var)
        db.session.commit()
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return None
    return p_cl.prep_cl_id


def db_upd_prep_cl(prep_cl_id, prep_cl_name, prep_cl_desc):
    p_cl = Prepared_Checklist.query.get(prep_cl_id)
    p_cl.prep_cl_name = prep_cl_name
    p_cl.prep_cl_desc = prep_cl_desc
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_upd_prep_cl_var(prep_cl_var_id, var_value):
    try:
        cl_v = Prepared_Checklist_Var.query.get(prep_cl_var_id)
        cl_v.var_value = var_value
        db.session.commit()
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_del_prep_cl(prep_cl_id):
    try:
        p_cl = Prepared_Checklist.query.get(prep_cl_id)
        p_cl_vars = Prepared_Checklist_Var.query.filter_by(prep_cl_id=prep_cl_id).all()
        # TODO Autres deletes pour les sections et les steps
        for p_cl_v in p_cl_vars:
            db.session.delete(p_cl_v)
        db.session.delete(p_cl)
        db.session.commit()
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


def db_add_cl_var(checklist_id, var_id):
    cl_v = Checklist_Var(checklist_id, var_id)
    try:
        db.session.add(cl_v)
        db.session.commit()
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_add_snip_var(snip_id, var_id):
    snip_var = Code_Snippet_Var(snip_id, var_id)
    try:
        db.session.add(snip_var)
        db.session.commit()
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_del_cl_var(checklist_id, var_id):
    cl_v = Checklist_Var.query.filter_by(checklist_id=checklist_id, var_id=var_id).first()
    try:
        db.session.delete(cl_v)
        db.session.commit()
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_add_snippet(snip_name, snip_desc, snip_code):
    audit_crt_user = session.get('user_email', None)
    audit_crt_ts = datetime.now()
    snippet = Code_Snippet(snip_name, snip_desc, snip_code, audit_crt_user, audit_crt_ts)
    try:
        db.session.add(snippet)
        db.session.commit()
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_del_snippet(snip_id):
    snippet = Code_Snippet.query.get(snip_id)
    snip_vars = Code_Snippet_Var.query.filter_by(snip_id=snip_id).order_by(Code_Snippet_Var.var_id).all()
    try:
        for snip_var in snip_vars:
            db.session.delete(snip_var)
        db.session.delete(snippet)
        db.session.commit()
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_upd_snippet(snip_id, snip_name, snip_desc, snip_code):
    audit_user = session.get('user_email', None)
    snippet = Code_Snippet.query.get(snip_id)
    snippet.snip_name = snip_name
    snippet.snip_desc = snip_desc
    snippet.snip_code = snip_code
    snippet.audit_upd_user = audit_user
    snippet.audit_upd_ts = datetime.now()
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_add_prep_snip(prep_snip_name, prep_snip_desc, prep_snip_code, snip_id):
    audit_crt_user = session.get('user_email', None)
    audit_crt_ts = datetime.now()
    p_snip = Prepared_Snippet(prep_snip_name, prep_snip_desc, prep_snip_code, snip_id, audit_crt_user, audit_crt_ts)
    try:
        db.session.add(p_snip)
        snip_vars = Code_Snippet_Var.query.filter_by(snip_id=snip_id).all()
        for snip_var in snip_vars:
            pred_var = Predef_Var.query.filter_by(var_id=snip_var.var_id).first()
            var_name = pred_var.var_name
            app.logger.debug(var_name)
            p_snip_var = Prepared_Snippet_Var(p_snip.prep_snip_id, snip_var.var_id, var_name, None)
            db.session.add(p_snip_var)
        db.session.commit()
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return None
    return p_snip.prep_snip_id


def db_upd_prep_snip(prep_snip_id, prep_snip_name, prep_snip_desc, prep_snip_code):
    p_snip = Prepared_Snippet.query.get(prep_snip_id)
    p_snip.prep_snip_name = prep_snip_name
    p_snip.prep_snip_desc = prep_snip_desc
    p_snip.prep_snip_code = prep_snip_code
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_upd_prep_snip_var(prep_snip_var_id, var_value, prep_snip_id):
    try:
        p_snip_var = Prepared_Snippet_Var.query.get(prep_snip_var_id)
        p_snip_var.var_value = var_value
        db.session.commit()

        p_snip = Prepared_Snippet.query.get(prep_snip_id)
        snippet = Code_Snippet.query.get(p_snip.snip_id)
        p_snip_vars = Prepared_Snippet_Var.query.filter_by(prep_snip_id=prep_snip_id).all()
        new_code = snippet.snip_code
        new_name = snippet.snip_name
        for p_snip_var in p_snip_vars:
            if p_snip_var.var_value is not None:
                new_code = new_code.replace(p_snip_var.var_name, p_snip_var.var_value)
                new_name = new_name + ' - ' + p_snip_var.var_value
            else:
                new_name = new_name + ' - ' + p_snip_var.var_name
        p_snip.prep_snip_code = new_code + "\n#--Version précédente--------------------\n" + p_snip.prep_snip_code
        p_snip.prep_snip_name = new_name
        db.session.commit()
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


def db_del_prep_snip(prep_snip_id):
    try:
        p_snip = Prepared_Snippet.query.get(prep_snip_id)
        p_snip_vars = Prepared_Snippet_Var.query.filter_by(prep_snip_id=prep_snip_id).all()
        for p_snip_var in p_snip_vars:
            db.session.delete(p_snip_var)
        db.session.delete(p_snip)
        db.session.commit()
    except Exception as e:
        app.logger.error('DB Error' + str(e))
        return False
    return True


# Start the server for the application
if __name__ == '__main__':
    manager.run()
