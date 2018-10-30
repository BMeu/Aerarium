#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Email handling functions.
"""

from typing import List

from threading import Thread

from flask import Flask
from flask_mail import Message

from app import get_app
from app import mail


def send_email(subject: str, recipients: List[str], body_plain: str, body_html: str) -> None:
    """
        Send an email.

        :param subject: The mail's subject.
        :param recipients: List of recipient addresses.
        :param body_plain: The actual content in plain text.
        :param body_html: The actual content in HTML.
    """

    application = get_app()
    if application is None:
        return

    if application.config['MAIL_FROM'] is None:
        return

    title = application.config['TITLE_SHORT']
    subject = f'{title} » {subject}'

    message = Message(subject, sender=application.config['MAIL_FROM'], recipients=recipients)
    message.body = body_plain
    message.html = body_html

    Thread(target=_send_email_async, args=(application, message)).start()


def _send_email_async(application: Flask, message: Message) -> None:
    """
        Send the given email asynchronously to avoid latencies.

        :param application: The application in whose context the mail will be sent.
        :param message: The email to send.
    """
    with application.app_context():
        mail.send(message)
