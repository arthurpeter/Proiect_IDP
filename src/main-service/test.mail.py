import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

print(f"--- DEBUG INFO ---")
print(f"User: {os.getenv('SMTP_USER')}")
print(f"Pass exists: {'YES' if os.getenv('SMTP_PASS') else 'NO'}")
print(f"Pass starts with xsmtpsib: {'YES' if str(os.getenv('SMTP_PASS')).startswith('xsmtpsib') else 'NO'}")
print(f"------------------")

def send_test_email():
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    sender = os.getenv("SMTP_SENDER")
    
    to_email = "arthurcristian.peter@gmail.com" 

    message = MIMEMultipart()
    message["From"] = f"Remailder Test <{sender}>"
    message["To"] = to_email
    message["Subject"] = "🚀 Remailder: Test Connection Successful!"
    
    body = "Dacă primești acest mesaj, înseamnă că setup-ul tău Brevo + Outlook funcționează perfect pentru proiectul IDP!"
    message.attach(MIMEText(body, "plain"))

    try:
        print(f"Conectare la {host}...")
        server = smtplib.SMTP(host, port)
        server.starttls()
        server.login(user, password)
        
        print("Trimitere mail...")
        server.send_message(message)
        server.quit()
        
        print("✅ Succes! Mail trimis cu succes!")
    except Exception as e:
        print(f"❌ Eroare: {e}")

if __name__ == "__main__":
    send_test_email()