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
    first_name = db.Column(db.String(), nullable=False)
    last_name = db.Column(db.String(), nullable=False)
    user_email = db.Column(db.String(), nullable=False, unique=True)
    user_pass = db.Column(db.String(), nullable=False)
    activated = db.Column(db.Boolean(), nullable=False, default=True)

    def __init__(self, first_name, last_name, user_email, user_pass):
        self.first_name = first_name
        self.last_name = last_name
        self.user_email = user_email
        self.user_pass = user_pass

    def __repr__(self):
        return '<user: {}>'.format(self.user_email)


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
    cur = g.dbh.execute(
        '''
        select checklist_id, checklist_name, audit_crt_user, audit_crt_ts
          from tchecklist
         where deleted_ind = 'N'
         order by checklist_name
        ''')
    checklists = [dict(checklist_id=row[0], checklist_name=row[1], audit_crt_user=row[2], audit_crt_ts=row[3])
                  for row in cur.fetchall()]
    for x in checklists:
        app.logger.debug(x['checklist_name'])
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
        row = db_query(
            '''
            select checklist_name
              from tchecklist
             where checklist_id = ?
            ''',
            [checklist_id], one=True)
        if row:
            return render_template('del_checklist.html', form=form, name=row[0])
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
        row = db_query(
            '''
            select checklist_name, checklist_desc
              from tchecklist
             where checklist_id = ?
            ''',
            [checklist_id], one=True)
        if row:
            form.checklist_name.data = row[0]
            form.checklist_desc.data = row[1]
            sections = g.dbh.execute(
                '''
                select section_id, section_seq, section_name
                  from tcl_section
                 where checklist_id = ?
                   and deleted_ind = 'N'
                  order by section_seq
                ''', (checklist_id, )
            )
            sections = [dict(section_id=sect[0], section_seq=sect[1], section_name=sect[2])
                        for sect in sections.fetchall()]
            return render_template("upd_checklist.html", form=form, checklist_id=checklist_id,
                                   name=row[0], desc=row[1], sections=sections)
        else:
            flash("L'information n'a pas pu être retrouvée.")
            return redirect(url_for('list_checklists'))


@app.route('/show_checklist/<int:checklist_id>')
def show_checklist(checklist_id):
    if not logged_in():
        return redirect(url_for('login'))
    row = db_query(
        '''
        select checklist_name, checklist_desc, audit_crt_user, audit_crt_ts, audit_upd_user, audit_upd_ts
          from tchecklist
         where checklist_id = ?
        ''',
        [checklist_id], one=True)
    if row:
        app.logger.debug(type(row))
        checklist_name = row[0]
        checklist_desc = row[1]
        audit_crt_user = row[2]
        audit_crt_ts = row[3]
        audit_upd_user = row[4]
        audit_upd_ts = row[5]
        cur_section = g.dbh.execute(
            '''
            select section_id, section_name, section_detail
              from tcl_section
             where checklist_id = ?
               and deleted_ind = 'N'
             order by section_seq
            ''',
            (checklist_id,))
        sections = [dict(section_id=row[0], section_name=row[1], section_detail=row[2])
                    for row in cur_section.fetchall()]
        for section in sections:
            section_id = section['section_id']
            app.logger.debug('for section in sections: ' + str(section_id) + section['section_name'])
            cur_step = g.dbh.execute(
                '''
                select step_id, step_short, step_detail
                  from tcl_step
                 where checklist_id = ?
                   and section_id = ?
                   and deleted_ind = 'N'
                 order by step_seq
                ''',
                (checklist_id, section_id,))
            steps = [dict(step_id=row[0], step_short=row[1], step_detail=row[2]) for row in cur_step.fetchall()]
            for step in steps:
                app.logger.debug('    for step in steps: ' + step['step_short'])
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
        row = db_query(
            '''
            select section_seq, section_name, section_detail
              from tcl_section
             where section_id = ?
            ''',
            [section_id], one=True)
        if row:
            form.section_seq.data = row[0]
            form.section_name.data = row[1]
            form.section_detail.data = row[2]
            steps = g.dbh.execute(
                '''
                select step_id, step_seq, step_short
                  from tcl_step
                 where section_id = ?
                   and deleted_ind = 'N'
                 order by step_seq
                ''', (section_id, )
            )
            steps = [dict(step_id=step[0], step_seq=step[1], step_short=step[2])
                     for step in steps.fetchall()]
            return render_template("upd_section.html", form=form, checklist_id=checklist_id,
                                   name=row[0], desc=row[1], steps=steps)
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
        row = db_query(
            '''
            select section_name
              from tcl_section
             where section_id = ?
            ''',
            [section_id], one=True)
        if row:
            section_name = row[0]
            app.logger.debug(section_name)
            count = db_query(
                '''
                select count(*) from tcl_step
                 where section_id = ?
                ''', [section_id], one=True
            )
            app.logger.debug('Nombre de steps pour cette section: ' + str(count[0]))
            if count[0] > 0:
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
        row = db_query(
            '''
            select step_short
              from tcl_step
             where step_id = ?
            ''',
            [step_id], one=True)
        if row:
            step_short = row[0]
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
        row = db_query(
            '''
            select step_seq, step_short, step_detail, step_user, step_code
              from tcl_step
             where step_id = ?
            ''',
            [step_id], one=True)
        if row:
            form.step_seq.data = row[0]
            form.step_short.data = row[1]
            form.step_detail.data = row[2]
            form.step_user.data = row[3]
            form.step_code.data = row[4]
            return render_template("upd_step.html", form=form, section_id=section_id)
        else:
            flash("L'information n'a pas pu être retrouvée.")
            return redirect(url_for('upd_section', section_id=section_id))


# Database functions

# Connect to the database and return a db handle
def connect_db():
    print(app.config['DATABASE'])
    return sqlite3.connect(app.config['DATABASE'], detect_types=sqlite3.PARSE_DECLTYPES)


# Utility function to create the database from the schema definition in db.sql
def init_db():
    with closing(connect_db()) as dbh:
        with app.open_resource('data/db.sql', mode='r') as f:
            dbh.cursor().executescript(f.read())
        dbh.commit()


# Execute a query
def db_query(query, args=(), one=False):
    cur = g.dbh.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


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
    audit_user = session.get('user_email', None)
    st_insert = '''
        insert into tchecklist(checklist_name, checklist_desc, audit_crt_user, audit_crt_ts)
            values(?, ?, ?, ?)
    '''
    try:
        sth = g.dbh.cursor()
        sth.execute(st_insert, [checklist_name, checklist_desc, audit_user, datetime.now()])
        g.dbh.commit()
        sth.close()
    except Exception as e:
        app.logger.error('DB Error' + e.__str__())
        return False
    return True


def db_del_checklist(checklist_id):
    audit_user = session.get('user_email', None)
    st_update = '''
    update tchecklist
       set deleted_ind = 'Y'
          ,audit_upd_user = ?
          ,audit_upd_ts   = ?
     where checklist_id = ?
    '''
    st_upd_sect = '''
    update tcl_section
       set deleted_ind = 'Y'
     where checklist_id = ?
    '''
    st_upd_step = '''
    update tcl_step
       set deleted_ind = 'Y'
     where checklist_id = ?
    '''
    try:
        sth = g.dbh.cursor()
        sth.execute(st_update, [audit_user, datetime.now(), checklist_id])
        sth.execute(st_upd_sect, [checklist_id])
        sth.execute(st_upd_step, [checklist_id])
        g.dbh.commit()
    except Exception as e:
        app.logger.error('DB Error' + e.__str__())
        return False
    return True


def db_upd_checklist(checklist_id, checklist_name, checklist_desc):
    audit_user = session.get('user_email', None)
    st_update = '''
    update tchecklist
       set checklist_name = ?
          ,checklist_desc = ?
          ,audit_upd_user = ?
          ,audit_upd_ts   = ?
     where checklist_id = ?
    '''
    try:
        sth = g.dbh.cursor()
        sth.execute(st_update, [checklist_name, checklist_desc, audit_user, datetime.now(), checklist_id])
        g.dbh.commit()
    except Exception as e:
        app.logger.error('DB Error' + e.__str__())
        return False
    return True


def db_add_section(checklist_id, section_seq, section_name, section_detail):
    st_insert = '''
        insert into tcl_section(checklist_id, section_seq, section_name, section_detail)
            values(?, ?, ?, ?)
    '''
    try:
        sth = g.dbh.cursor()
        sth.execute(st_insert, [checklist_id, section_seq, section_name, section_detail])
        if db_renum_section(checklist_id):
            g.dbh.commit()
        else:
            g.dbh.rollback()
        sth.close()
    except Exception as e:
        app.logger.error('DB Error' + e.__str__())
        return False
    return True


def db_del_section(section_id, checklist_id):
    st_delete = '''
    delete from tcl_section
     where section_id = ?
    '''
    try:
        sth = g.dbh.cursor()
        sth.execute(st_delete, [section_id])
        if db_renum_section(checklist_id):
            g.dbh.commit()
        else:
            g.dbh.rollback()
            return False
    except Exception as e:
        app.logger.error('DB Error' + e.__str__())
        return False
    return True


def db_upd_section(section_id, section_seq, section_name, section_detail, checklist_id):
    st_update = '''
    update tcl_section
       set section_seq = ?
          ,section_name = ?
          ,section_detail = ?
     where section_id = ?
    '''
    try:
        sth = g.dbh.cursor()
        sth.execute(st_update, [section_seq, section_name, section_detail, section_id])
        if db_renum_section(checklist_id):
            g.dbh.commit()
        else:
            g.dbh.rollback()
            return False
    except Exception as e:
        app.logger.error('DB Error' + e.__str__())
        return False
    return True


def db_renum_section(checklist_id):
    st_update = '''
        update tcl_section set section_seq = ?
         where section_id = ?
    '''
    try:
        sth = g.dbh.cursor()
        cur_sect = g.dbh.execute(
            '''
            select section_id
              from tcl_section
             where checklist_id = ?
               and deleted_ind = 'N'
             order by section_seq
            ''',
            (checklist_id, ))
        sections = [dict(section_id=row[0]) for row in cur_sect.fetchall()]
        new_seq = 0
        for section in sections:
            section_id = section['section_id']
            new_seq += 10
            sth.execute(st_update, [new_seq, section_id])
        cur_sect.close()
        sth.close()
    except Exception as e:
        app.logger.error('DB Error' + e.__str__())
        return False
    return True


def db_add_step(checklist_id, section_id, step_seq, step_short, step_detail, step_user, step_code):
    st_insert = '''
        insert into tcl_step(checklist_id, section_id, step_seq, step_short, step_detail, step_user, step_code)
            values(?, ?, ?, ?, ?, ?, ?)
    '''
    try:
        sth = g.dbh.cursor()
        sth.execute(st_insert, [checklist_id, section_id, step_seq, step_short, step_detail, step_user, step_code])
        if db_renum_step(section_id):
            g.dbh.commit()
        else:
            g.dbh.rollback()
        sth.close()
    except Exception as e:
        app.logger.error('DB Error' + e.__str__())
        return False
    return True


def db_del_step(step_id, section_id):
    st_delete = '''
    delete from tcl_step
     where step_id = ?
    '''
    try:
        sth = g.dbh.cursor()
        sth.execute(st_delete, [step_id])
        if db_renum_step(section_id):
            g.dbh.commit()
        else:
            g.dbh.rollback()
            return False
    except Exception as e:
        app.logger.error('DB Error' + e.__str__())
        return False
    return True


def db_upd_step(step_id, step_seq, step_short, step_detail, step_user, step_code, section_id):
    st_update = '''
    update tcl_step
       set step_seq = ?
          ,step_short = ?
          ,step_detail = ?
          ,step_user = ?
          ,step_code = ?
     where step_id = ?
    '''
    try:
        sth = g.dbh.cursor()
        sth.execute(st_update, [step_seq, step_short, step_detail, step_user, step_code, step_id])
        if db_renum_step(section_id):
            g.dbh.commit()
        else:
            g.dbh.rollback()
            return False
    except Exception as e:
        app.logger.error('DB Error' + e.__str__())
        return False
    return True


def db_renum_step(section_id):
    st_update = '''
        update tcl_step set step_seq = ?
         where step_id = ?
    '''
    try:
        sth = g.dbh.cursor()
        cur_step = g.dbh.execute(
            '''
            select step_id
              from tcl_step
             where section_id = ?
               and deleted_ind = 'N'
             order by step_seq
            ''',
            (section_id, ))
        steps = [dict(step_id=row[0]) for row in cur_step.fetchall()]
        new_seq = 0
        for step in steps:
            step_id = step['step_id']
            new_seq += 10
            sth.execute(st_update, [new_seq, step_id])
        cur_step.close()
        sth.close()
    except Exception as e:
        app.logger.error('DB Error' + e.__str__())
        return False
    return True


# Start the server for the application
if __name__ == '__main__':
    manager.run()
