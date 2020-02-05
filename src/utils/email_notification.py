import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import html.parser


_template = """\
<html>
    <head></head>
    <body>
    <p><strong>{subject}:</strong></p>
    {msg}
    </body>
</html>
"""


class EmailNotifier:
    """
    this implements a basic Email notification system. It can be used to send
    multi-part email messages that contain an html and text version of the
    message.  The text version is automatically generated from the message body,
    which can contain html tags, that is passed to the send() method.
    """

    def __init__(self, smtp_server, admin_email, reply_to=None, template=_template):
        self.smtp_server = smtp_server
        self.admin_email = admin_email
        self.template = template
        self.reply_to = reply_to if reply_to else self.admin_email

    def __strip_html_tags(self, content):
        """
        this method will process html content and return a plain text version.
        It is used to take the message body passed into the send() method and
        generate a basic plain text representation. It does this by extending
        the HTMLParser class.
        :param content: text that can contain html tags
        :return: plain text representation of that content
        """

        class HTMLStripper(html.parser.HTMLParser, object):
            """
            private class used to parse html and strip out tags.  can
            reformat plain text, currently just removes tags other than
            generating a plain text version of a link
            """
            def __init__(self):
                super(HTMLStripper, self).__init__()
                self.reset()
                self.fed = []
                self.processing_link = False
                self.href = ""

            def handle_starttag(self, tag, attributes):
                """
                   override html.parser.HTMLParser's handle_starttag method
                   this is called to process an opening HTML tag. In our case
                   we are stripping out tags and just keeping the text within
                   them, except for <a> tags where we are saving the value of
                   the href attribute

                   :param tag: html tag (e.g. 'a', 'p', 'h1', etc)
                   :param attributes: attributes of the tag, for example an <a>
                   tag would have an href attribute
                """
                if tag == 'a':
                    # if it is an anchor tag, pull the href out of the
                    # attributes. We also need to set a flag so that when
                    # handle_data() is called it knows it is processing the
                    # content of an <a> tag
                    self.processing_link = True
                    for name, value in attributes:
                        if name == 'href':
                            self.href = value
                else:
                    # for every other tag, we just strip it out without
                    # doing anything
                    return

            def handle_endtag(self, tag):
                return

            def handle_data(self, d):
                if not self.processing_link:
                    self.fed.append(d)
                else:
                    self.fed.append("{}:[{}]".format(d, self.href))
                    self.processing_link = False

            def get_data(self):
                return ''.join(self.fed)

        # first unescape html entities like $amp; (otherwise these get stripped
        # too)
        escaped_content = html.unescape(content)

        # now generate the plain text version of the message using HTMLStripper
        stripper = HTMLStripper()
        stripper.feed(escaped_content)
        return stripper.get_data()

    def send(self, to, subject, message):
        """
        send an email message
        :param to: recipient email address
        :param subject: email subject
        :param message: message body
        :return:
        """

        msg = MIMEMultipart('alternative')
        msg['From'] = self.admin_email
        msg['To'] = to
        msg['Subject'] = subject

        # generate plain text version of message
        text_content = self.__strip_html_tags(message)

        html_content = self.template.format(msg=message, subject=subject)

        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')

        msg.attach(part1)
        msg.attach(part2)

        with smtplib.SMTP(self.smtp_server) as smtp:
            smtp.sendmail(self.reply_to, to, msg.as_string())

