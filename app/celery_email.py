# from flask import current_app, render_template
# from flask_mail import Message
# from . import mail, celery
# from app import celery, create_app
# from app import celery, create_app

# app = create_app('default')
# app.app_context().push()


# from json import JSONEncoder
# class MyEncoder(JSONEncoder):
#     def default(self, o):
#         return o.__dict__   

# @celery.task(name='go_chuuu')
# def email(msg):
#     mail.send(msg)


# def send_email_to_remind(to, subject, template, **kwargs):
#     app = current_app._get_current_object()
#     msg = Message(app.config['BILL_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
#                   sender=app.config['BILL_MAIL_SENDER'], recipients=[to])
#     msg.body = render_template(template + '.txt', **kwargs)
#     msg.html = render_template(template + '.html', **kwargs)
#     msg=MyEncoder().encode(msg)
#     email.apply_async(countdown=2, args=[msg])

