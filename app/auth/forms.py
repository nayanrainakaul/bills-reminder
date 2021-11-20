from wtforms import Form, BooleanField, StringField, PasswordField,validators, TextAreaField,SelectField, IntegerField,ValidationError,SubmitField
from wtforms.validators import DataRequired,Length, Email, Regexp, EqualTo
import email_validator
import phonenumbers
from ..models import User,Role
from flask_wtf import FlaskForm
from wtforms import ValidationError
from flask_wtf.file import FileField,FileRequired


# Creating Login Form contains email and password
class LoginForm(Form):
    email = StringField("Email", validators=[validators.Length(min=7, max=50), 
    validators.DataRequired(message="Please Fill This Field"),Email()])
    password = PasswordField("Password", validators=[validators.DataRequired(message="Please Fill This Field")])


# Creating Registration Form contains username, name, email, password and confirm password.
class RegisterForm(Form):

    name = StringField("Name", validators=[validators.Length(min=3, max=25), validators.DataRequired(message="Please Fill This Field")])
    username = StringField("Username", validators=[validators.Length(min=3, max=25), 
    validators.DataRequired(message="Please Fill This Field"),Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
 'Usernames must have only letters, numbers, dots or underscores')])
    email = StringField("Email", validators=[validators.Email(message="Please enter a valid email address")])
    phone = StringField('Phone', validators=[DataRequired(message="Please Fill This Field To Recieve a Whatsapp Reminder")])
    password = PasswordField("Password", validators=[

        validators.DataRequired(message="Please Fill This Field"),

        validators.EqualTo(fieldname="confirm", message="Your Passwords Do Not Match")
    ])
    confirm = PasswordField("Confirm Password", validators=[validators.DataRequired(message="Please Fill This Field")])

    
    # To Validate Phone Number
    # def validate_phone(form, field):
    #         if len(field.data) > 16:
    #             raise ValidationError('Invalid phone number.')
    #         try:
    #             input_number = phonenumbers.parse(field.data)
    #             if not (phonenumbers.is_valid_number(input_number)):
    #                 raise ValidationError('Invalid phone number.')
    #         except:
    #             input_number = phonenumbers.parse("+1"+field.data)
    #             if not (phonenumbers.is_valid_number(input_number)):
    #                 raise ValidationError('Invalid phone number.')




    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')



    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')




class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    password = PasswordField('New password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm new password',
                              validators=[DataRequired()])
    submit = SubmitField('Update Password')


class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    submit = SubmitField('Reset Password')


class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')


class ChangeEmailForm(FlaskForm):
    email = StringField('New Email', validators=[DataRequired(), Length(1, 64),
                                                 Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Update Email Address')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already registered.')



class UnsubscribeForm(FlaskForm):
    email = StringField('Your Email', validators=[DataRequired(), Length(1, 64),Email()])
    submit = SubmitField('Unsubscribe')


class EditProfileForm(FlaskForm):
    name = StringField('Name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About you')
    designation = TextAreaField('Your Designation')
    photo = FileField('Your Profile Photo')
    submit = SubmitField('Submit')
    delete = SubmitField('Delete')


class MoneyManager(FlaskForm):
    type=SelectField(u'Categories', choices=[('cpp', 'C++'), ('py', 'Python'), ('text', 'Plain Text')])


class EditBillEntryForm(FlaskForm):
    bill_name= StringField('Bill Name')
    amount =  StringField('Amount')
    note =  TextAreaField('Note')
    submit = SubmitField('Submit')
    discard = SubmitField('Discard')

    

class EditProfileAdminForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    username = StringField('Username', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Usernames must have only letters, numbers, dots or '
               'underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    designation = TextAreaField('Your Designation')
    photo = FileField('Your Profile Photo')
    submit = SubmitField('Submit')
    delete = SubmitField('Delete')


    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')
