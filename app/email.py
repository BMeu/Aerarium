#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Email handling functions.
"""

from typing import Any
from typing import List
from typing import Optional
from typing import Union

from threading import Thread

from flask import Flask
from flask import render_template
from flask_mail import Message

from app import get_app
from app import mail
from app.exceptions import NoMailSenderError


class Email(object):
    """
        A class for representing single email messages.

        Emails will be sent asynchronously to avoid latencies.
    """

    def __init__(self, subject, body: str, sender: Optional[str] = None) -> None:
        """
            :param subject: The mail's subject line.
            :param body: The path (within the template folder) to the template for this mail's body (without the file
                         extension).
            :param sender: The sender of the mail. If not set, the sender will be taken from the app configuration.
            :raise NoMailSenderError: If no sender is given and none is configured in the app configuration.
        """
        application = get_app()
        title = application.config['TITLE_SHORT']

        self._body_template_base_path: str = body
        self._body_plain: Optional[str] = None
        self._body_html: Optional[str] = None
        self._subject: str = f'{title} » {subject}'

        self._sender: str = sender
        if self._sender is None:
            self._sender = application.config['MAIL_FROM']

        # If the sender is still not known, raise an error.
        if self._sender is None:
            raise NoMailSenderError('No sender given and none configured in the app configuration.')

    def prepare(self, **template_parameters: Any) -> None:
        """
            Prepare the body by rendering their templates.

            :param template_parameters: Parameters that will be passed down to the templates while rendering.
        """
        self._body_plain = render_template(self._body_template_base_path + '.txt', **template_parameters)
        self._body_html = render_template(self._body_template_base_path + '.html', **template_parameters)

    def prepare_and_send(self, recipients: Union[str, List[str]], **template_parameters: Any) -> None:
        """
            Prepare (:meth:`prepare`) and send (:meth:`send`) the mail to the given recipients.

            :param recipients: A single recipient or a list of recipients to which the mail will be send.
            :param template_parameters: Parameters that will be passed down to the templates while rendering.
            :raise TypeError: If the recipients argument is not a string or a list of strings.
        """
        self.prepare(**template_parameters)
        self.send(recipients)

    def send(self, recipient: Union[str, List[str]]) -> None:
        """
            Send the mail to the given recipients.

            :param recipient: A single recipient or a list of recipients to which the mail will be send.
            :raise TypeError: If the recipients argument is not a string or a list of strings.
        """
        if isinstance(recipient, str):
            recipients = [recipient]
        elif isinstance(recipient, list):
            recipients = recipient
        else:
            raise TypeError('Argument "recipients" must be a string or a list of strings.')

        message = Message(self._subject, sender=self._sender, recipients=recipients)
        message.body = self._body_plain
        message.html = self._body_html

        application = get_app()
        thread = Thread(target=self._send, args=(message, application))
        thread.start()

    @staticmethod
    def _send(message: Message, application: Flask) -> None:
        """
            Send the given message asynchronously.

            :param message: The email message to send.
            :param application: A Flask instance.
        """
        with application.app_context():
            mail.send(message)
