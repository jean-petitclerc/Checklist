from flask import Flask, session, redirect, url_for, request, render_template, flash, g, abort  # escape
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo  # Length, NumberRange
from flask_script import Manager
from contextlib import closing
from datetime import datetime
import sqlite3

app = Flask(__name__)
manager = Manager(app)
bootstrap = Bootstrap(app)


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


# This creates the database connection for each request
@app.before_request
def before_request():
    g.db = connect_db()


# This close the db connection at the end of the requests
@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


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
            insert = '''
            insert into tadmin_user(first_name, last_name, user_email, user_pass)
              values(?, ?, ?, ?)
            '''
            cur = g.db.cursor()
            cur.execute(insert, [first_name, last_name, user_email, user_pass])
            g.db.commit()
            cur.close()
            flash('Come back when your login will be activated.')
            return redirect(url_for('index'))
    return render_template('register.html', form=form)


@app.route('/list_checklists')
def list_checklists():
    if not logged_in():
        return redirect(url_for('login'))
    cur = g.db.execute(
        '''
        select checklist_id, checklist_name, audit_crt_user, audit_crt_ts
          from tchecklist
         where deleted_ind = 'N'
         order by checklist_name
        ''')
    checklists = [dict(checklist_id=row[0], checklist_name=row[1], audit_crt_user=row[2], audit_crt_ts=row[3]) for row in cur.fetchall()]
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


@app.route('/del_checklist/<int:checklist_id>', methods=['GET','POST'])
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


@app.route('/upd_checklist/<int:checklist_id>', methods=['GET','POST'])
def upd_checklist(checklist_id):
    if not logged_in():
        return redirect(url_for('login'))
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
            return render_template("upd_checklist.html", form=form, name=row[0], desc=row[1])
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
        return render_template("show_checklist.html", name=row[0], desc=row[1], crt_user=row[2], crt_ts=row[3],
                               upd_user=row[4], upd_ts=row[5])
    else:
        flash("L'information n'a pas pu être retrouvée.")
        return redirect(url_for('list_checklists'))

# Database functions


# Connect to the database and return a db handle
def connect_db():
    print(app.config['DATABASE'])
    return sqlite3.connect(app.config['DATABASE'], detect_types=sqlite3.PARSE_DECLTYPES)


# Utility function to create the database from the schema definition in db.sql
def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('data/db.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


# Execute a query
def db_query(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def user_exists(user_email):
    app.logger.debug('Entering user_exists with: ' + user_email)
    user = db_query('select first_name from tadmin_user where user_email = ?',
                    [user_email], one=True)
    if user is None:
        app.logger.debug('user_exists returns False')
        return False
    else:
        app.logger.debug('user_exists returns True' + user[0])
        return True


# Validate if a user is defined in tadmin_user with the proper password.
def db_validate_user(user_email, password):
    row = db_query('''
    select first_name, last_name, user_pass, activated from tadmin_user where user_email = ?
    ''', [user_email], one=True)
    if row is None:
        flash("L'usager n'existe pas.")
        return False
    if row[3] != 'Y':
        flash("L'usager n'est pas activé.")
        return False

    if check_password_hash(row[2], password):
        session['user_email'] = user_email
        session['first_name'] = row[0]
        session['last_name'] = row[1]
        return True
    else:
        flash("Mauvais mot de passe!")
        return False


def change_password(user_email, new_password):
    user_pass = generate_password_hash(new_password)
    update = '''
    update tadmin_user
       set user_pass = ?
     where user_email = ?
    '''
    cur = g.db.cursor()
    cur.execute(update, [user_pass, user_email])
    g.db.commit()
    cur.close()
    flash('Password changed.')


def db_add_checklist(checklist_name, checklist_desc):
    audit_user = session.get('user_email', None)
    insert = '''
        insert into tchecklist(checklist_name, checklist_desc, audit_crt_user, audit_crt_ts)
            values(?, ?, ?, ?)
    '''
    try:
        sth = g.db.cursor()
        sth.execute(insert, [checklist_name, checklist_desc, audit_user, datetime.now()])
        g.db.commit()
        sth.close()
    except Exception as e:
        app.logger.error('DB Error' + e.__str__())
        return False
    return True


def db_del_checklist(checklist_id):
    audit_user = session.get('user_email', None)
    update = '''
    update tchecklist
       set deleted_ind = 'Y'
          ,audit_upd_user = ?
          ,audit_upd_ts   = ?
     where checklist_id = ?
    '''
    try:
        sth = g.db.cursor()
        sth.execute(update, [audit_user, datetime.now(), checklist_id])
        g.db.commit()
    except Exception as e:
        app.logger.error('DB Error' + e.__str__())
        return False
    return True


def db_upd_checklist(checklist_id, checklist_name, checklist_desc):
    audit_user = session.get('user_email', None)
    update = '''
    update tchecklist
       set checklist_name = ?
          ,checklist_desc = ?
          ,audit_upd_user = ?
          ,audit_upd_ts   = ?
     where checklist_id = ?
    '''
    try:
        sth = g.db.cursor()
        sth.execute(update, [checklist_name, checklist_desc, audit_user, datetime.now(), checklist_id])
        g.db.commit()
    except Exception as e:
        app.logger.error('DB Error' + e.__str__())
        return False
    return True

# Read the configurations
app.config.from_pyfile('config/config.py')

# Start the server for the application
if __name__ == '__main__':
    manager.run()
