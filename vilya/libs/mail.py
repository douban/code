# coding: utf-8
import smtplib

from vilya.config import SMTP_SERVER


def send_mail(msg):
    fromaddr = msg["From"]
    toaddrs = []
    if msg['To']:
        toaddrs += [addr.strip() for addr in msg["To"].split(',')]
    if msg["Cc"]:
        toaddrs += [addr.strip() for addr in msg["Cc"].split(',')]

    smtp = smtplib.SMTP(SMTP_SERVER)
    smtp.sendmail(fromaddr, toaddrs, msg.as_string())
    smtp.quit()
