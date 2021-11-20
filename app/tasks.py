# from flask import Flask, render_template, request,session,redirect, url_for,flash,abort,make_response,current_app
# from flask_mail import Mail,Message
# from .__init__ import celery



    

# def sendEmail_to_remind_bill(app, msg):
#     with app.app_context():
#         mail.send(msg)

# @celery.task(name="send_email_to_remind")     
# def sendEmail(to, subject, template, **kwargs):
#     app = current_app._get_current_object()
#     msg = Message(subject,sender=app.config['BILL_MAIL_SENDER'], recipients=[to])
#     msg.body = render_template(template + '.txt', **kwargs)
#     msg.html = render_template(template + '.html', **kwargs)
#     mail.send(msg)