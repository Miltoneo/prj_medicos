import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = 'mail.onkoto.com.br'
SMTP_PORT = 587
SMTP_USER = 'user1@onkoto.com.br'
SMTP_PASSWORD = '*mil031212'

FROM = SMTP_USER
TO = SMTP_USER  # Envia para si mesmo para teste

msg = MIMEMultipart()
msg['From'] = FROM
msg['To'] = TO
msg['Subject'] = 'Teste SMTP - prj_medicos'
msg.attach(MIMEText('Este é um teste de envio SMTP via script Python.', 'plain'))

try:
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.ehlo()
    server.starttls()
    server.login(SMTP_USER, SMTP_PASSWORD)
    server.sendmail(FROM, TO, msg.as_string())
    server.quit()
    print('E-mail enviado com sucesso!')
except Exception as e:
    print('Erro ao enviar e-mail:', e)
