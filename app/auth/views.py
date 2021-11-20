from flask import Flask, render_template, request, session, redirect, url_for, flash, abort, make_response, current_app, g
from flask_login import login_user, login_required, logout_user
from itsdangerous.signer import SigningAlgorithm
from . import auth
from .. import db
from ..models import  User, Entry, Role, Permission
from .forms import LoginForm, RegisterForm, ChangePasswordForm, PasswordResetRequestForm, PasswordResetForm, ChangeEmailForm, EditProfileForm, EditProfileAdminForm,UnsubscribeForm,EditBillEntryForm
from datetime import datetime
from ..email import send_email
from flask_login import current_user
from ..__init__ import flask_bcrypt
from ..decorators import admin_required
import os
from werkzeug.utils import secure_filename
@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate:
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            if flask_bcrypt.check_password_hash(user.password, form.password.data):
                session['logged_in'] = True
                session['email'] = user.email
                session['username'] = user.username
                session['name'] = user.name
                session['phone'] = user.phoneNo
                flash('You have successfully logged in.', "success")
                login_user(user)
                next = request.args.get('next')
                if next is None or not next.startswith('/'):
                    next = url_for('main.home')
                return redirect(next)
            else:
                # if password is incorrect , redirect to login page
                flash('Username or Password Incorrect', "Danger")
                return redirect(url_for('auth.login'))
        else:
            flash('You are not registered, please register first', "Danger")
            return redirect(url_for('auth.login'))
    else:
        return render_template('auth/login.html', form=form, current_time=datetime.utcnow(), user=current_user)




@auth.route("/bill-paid/<int:id>", methods=['GET', 'POST'])
def bill_paid(id):
    paid_entry = Entry.query.filter_by(id=id).first()
    paid_entry.paidUnpaid = 'Paid'
    db.session.add(paid_entry)
    db.session.commit()
    return redirect(url_for('main.show_reminders'))

@auth.route("/bill-unpaid/<int:id>", methods=['GET', 'POST'])
def bill_unpaid(id):
    paid_entry = Entry.query.filter_by(id=id).first()
    paid_entry.paidUnpaid = 'Unpaid'
    db.session.add(paid_entry)
    db.session.commit()
    return redirect(url_for('main.show_reminders'))





@auth.route("/edit-bill-entry/<int:id>", methods=['GET', 'POST'])
def edit_bill_entry(id):
    entry = Entry.query.filter_by(id=id).first()
    form = EditBillEntryForm()
    if  request.method == 'POST':
        if form.submit.data :
            entry.billName = form.bill_name.data
            entry.amount = form.amount.data
            entry.note = form.note.data
            db.session.add(entry)
            db.session.commit()
            flash('Changes Saved')
            return redirect(url_for('main.show_reminders'))   
        elif form.discard.data : 
            flash('Changes Discarded')
            return redirect(url_for('main.show_reminders'))   
    form.bill_name.data = entry.billName
    form.amount.data = entry.amount
    form.note.data = entry.note
    return render_template('edit_bill_entry.html',form=form)
   



# To run ping function (update last seen) each time a request from a user is received
@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint \
                and request.blueprint != 'auth' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous:
        return redirect(url_for('main.home'))
    return render_template('auth/unconfirmed.html')
# @auth.route('/unconfirmed')
# def unconfirmed():
#     if current_user.is_anonymous or current_user.confirmed:
#         return redirect(url_for('main.home'))
#     return render_template('auth/unconfirmed.html')



@auth.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():

    form = EditProfileForm()
    if request.method == 'POST' and form.validate:
        if form.submit.data:
            current_user.name = form.name.data
            current_user.location = form.location.data
            current_user.about_me = form.about_me.data
            current_user.designation = form.designation.data

         
            if form.photo.data!=None:
                form.photo.data.save( os.path.join(current_app.config['UPLOAD_FOLDER'] , str(current_user.get_id())+'.jpg'))
            current_user.photo = 'img/user-profile-pic/'+ str(current_user.get_id())+'.jpg'
            db.session.add(current_user._get_current_object())
            db.session.commit()
            flash('Your profile has been updated.')
            return redirect(url_for('main.user',username=current_user.username))
        
        
        elif form.delete.data:
            User.query.filter_by(username=current_user.username).delete()
            db.session.commit()
            flash('Your profile has been deleted.')
            return redirect(url_for('main.home'))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    form.designation.data = current_user.designation
    user_id = str(current_user.get_id())
    return render_template('auth/edit_profile.html', form=form, user_id=user_id)


@auth.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if request.method == 'POST' and form.validate:
        if form.submit.data:
            user.email = form.email.data
            user.username = form.username.data
            user.confirmed = form.confirmed.data
            user.role = Role.query.get(form.role.data)
            user.name = form.name.data
            user.location = form.location.data
            user.about_me = form.about_me.data
            user.designation = form.designation.data
            db.session.add(user)
            db.session.commit()
            flash('The profile has been updated.')
            return redirect(url_for('main.user', username=user.username))
        elif form.delete.data:
            User.query.filter_by(id=user.id).delete()
            db.session.commit()
            flash('The profile has been Deleted.')
            return redirect(url_for('main.home'))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    form.designation.data = user.designation
    return render_template('auth/edit_profile_admin.html', form=form, user=user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.home'))


# User Registration Api End Point
@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        pw_hash = flask_bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(
            name=form.name.data,
            username=form.username.data,
            email=form.email.data,
            phoneNo=form.phone.data,
            password=pw_hash)
        db.session.add(new_user)
        db.session.commit()
        token = new_user.generate_confirmation_token()
        send_email(new_user.email, 'Confirm Your Account',
                   'auth/email/confirm', user=new_user, token=token)
        flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('main.home'))
    else:
        return render_template('auth/register.html', form=form, current_time=datetime.utcnow())


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account',
               'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('main.home'))


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.home'))
    if current_user.confirm(token):
        db.session.commit()
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.home'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=current_user.email).first()
        if user:
            if flask_bcrypt.check_password_hash(user.password, form.old_password.data):
                if flask_bcrypt.check_password_hash(user.password, form.password.data):
                    flash('You are entering old password, please enter a new one')
                    return render_template("auth/change_password.html", form=form)
                else:
                    hash_pass = flask_bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                    current_user.password = hash_pass
                    db.session.add(current_user)
                    db.session.commit()
                    flash('Your password has been updated.')
                    return redirect(url_for('main.home'))
            else:
                flash('Invalid password.')
    return render_template("auth/change_password.html", form=form)


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.home'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, 'Reset Your Password',
                       'auth/email/reset_password',
                       user=user, token=token)
        flash('An email with instructions to reset your password has been '
              'sent to you.')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.home'))
    form = PasswordResetForm()

    if form.validate_on_submit():
        pw_hash = flask_bcrypt.generate_password_hash(form.password.data).decode('utf8')
        if User.reset_password(token,   pw_hash):

            db.session.commit()
            flash('Your password has been updated.')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.home'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=current_user.email).first()
        if user:
            if flask_bcrypt.check_password_hash(user.password, form.password.data):
                new_email = form.email.data.lower()
                token = current_user.generate_email_change_token(new_email)
                send_email(new_email, 'Confirm your email address', 'auth/email/change_email',
                           user=current_user, token=token)
                flash('An email with instructions to confirm your new email '
                      'address has been sent to you.')
                return redirect(url_for('main.home'))
            else:
                flash('Invalid email or password.')
    return render_template("auth/change_email.html", form=form)


@auth.route('/change_email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        db.session.commit()
        flash('Your email address has been updated.')
    else:
        flash('Invalid request.')
    return redirect(url_for('main.home'))


@auth.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    form = UnsubscribeForm()
    if form.validate_on_submit():
        User.query.filter_by(email=form.email.data).delete()
        db.session.commit()
        flash('You have been unsubscribed successfully.')
        return redirect(url_for('main.home'))
    else:
        flash('Invalid Email')
    return render_template("auth/unsubscribe.html", form=form)