import time
import logging
import os
import smtplib


def send_email(recipient_email, subject, body):
    """
    Отправляет email сообщение с использованием SMTP.
    """
    from email.mime.text import MIMEText
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = os.getenv('SEND_FROM_EMAIL') 
    msg['To'] = recipient_email

    max_tries = 10
    cur_try = 0
    
    try:
        cur_try += 1
        with smtplib.SMTP(os.getenv('EMAIL_SERVER'), os.getenv('EMAIL_SERVER_PORT')) as server:
            server.starttls()
            server.login(os.getenv('SEND_FROM_EMAIL') , os.getenv('SEND_FROM_EMAIL_PASSWORD'))
            server.sendmail(os.getenv('SEND_FROM_EMAIL'), recipient_email, msg.as_string())
            logging.info("Email sent successfully")
    except Exception as e:
        if cur_try >= max_tries:
            logging.error(f"Failed to send email after {max_tries} attempts: {e}")
            raise e
        else:
            logging.error(f"Failed to send email: {e} I`ll try again in 60 seconds")
            time.sleep(60)
            send_email(recipient_email, subject, body)

