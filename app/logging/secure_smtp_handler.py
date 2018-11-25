#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    An extension of the default SMTP handler.
"""

from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

# noinspection PyProtectedMember
from email.message import EmailMessage
import email.utils
from logging import LogRecord
from logging.handlers import SMTPHandler
from smtplib import SMTP
# noinspection PyProtectedMember
from smtplib import SMTP_PORT
from smtplib import SMTP_SSL
# noinspection PyProtectedMember
from smtplib import SMTP_SSL_PORT


class SecureSMTPHandler(SMTPHandler):
    """
        A handler class which sends an SMTP email with SSL support for each logging event.
    """

    def __init__(self,
                 mailhost: Union[str, Tuple[str, int]],
                 fromaddr: str,
                 toaddrs: List[str],
                 subject: str,
                 credentials: Optional[Tuple[str, str]] = None,
                 secure: Optional[Union[Tuple[()], Tuple[str], Tuple[str, str]]] = None,
                 ssl: bool = False,
                 timeout: float = 5.0
                 ) -> None:
        """
            Initialize the handler.

            :param mailhost: The SMTP server. To specify a non-standard SMTP port, a tuple (host, port) can be used.
            :param fromaddr: Address from which the mails will be sent.
            :param toaddrs: Addresses to which the mails will be sent.
            :param subject: Subject of the mails to send.
            :param credentials: Authentication credentials in the form (username, password) (defaults to ``None``).
            :param secure: If set to a tuple, a TLS connection will be used. The tuple can either be empty, a
                singe-valued tuple with the name of a key file, or a 2-tuple with the names of the key file and
                certificate file (defaults to ``None``).
            :param ssl: If set to True, an SSL connection the SMTP server will be used (defaults to ``False``).
            :param timeout: Timeout in seconds for the SMTP connection (defaults to ``5.0`` seconds).
        """

        self.ssl = ssl
        super().__init__(mailhost, fromaddr, toaddrs, subject, credentials, secure, timeout)

    def emit(self, record: LogRecord) -> None:
        """
            Emit a record.

            Format the record and send it to the specified addresses.

            :param record: The record to send.
            :raise KeyboardInterrupt: If a keyboard interrupt occurs during mail transmission, it will be reraised.
            :raise SystemExit: If a ``sys.exit()`` interrupts the mail transmission, it will be reraised.
        """

        # noinspection PyBroadException
        try:
            port = self.mailport
            if not port:
                port = SMTP_SSL_PORT if self.ssl else SMTP_PORT

            if self.ssl:
                smtp = SMTP_SSL(self.mailhost, port, timeout=self.timeout)
            else:
                smtp = SMTP(self.mailhost, port, timeout=self.timeout)

            msg = EmailMessage()
            msg['From'] = self.fromaddr
            msg['To'] = ','.join(self.toaddrs)
            msg['Subject'] = self.getSubject(record)
            msg['Date'] = email.utils.localtime()
            msg.set_content(self.format(record))

            if self.username:
                if self.secure is not None:
                    smtp.ehlo()
                    smtp.starttls(*self.secure)
                    smtp.ehlo()
                smtp.login(self.username, self.password)

            smtp.send_message(msg)
            smtp.quit()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)
