import smtplib
import ssl
from email.message import EmailMessage
from datetime import datetime
import os

# --- EMAIL CONFIGURATION ---
EMAIL_SENDER = "xayari229@gmail.com"
EMAIL_PASSWORD = "rkoa zvwu nqnj nifo"
EMAIL_RECEIVER = "xayari229@gmail.com"


def email_worker(task_queue):
    """
    Background worker that listens for alerts and sends emails.
    """
    print(">>> Email Service Started (Background)")
    context = ssl.create_default_context()

    while True:
        # Wait for a task from the queue
        task = task_queue.get()
        if task is None:  # Stop signal
            break

        image_path, alert_time = task
        timestamp_str = datetime.fromtimestamp(
            alert_time).strftime('%Y-%m-%d %H:%M:%S')

        print(
            f">>> Processing Alert: Sending email for detection at {timestamp_str}...")

        try:
            msg = EmailMessage()
            msg["Subject"] = "🚨 INTRUDER ALERT! - Restricted Area"
            msg["From"] = EMAIL_SENDER
            msg["To"] = EMAIL_RECEIVER
            msg.set_content(
                f"An unauthorized person was detected at the Restricted Area.\n\nTime: {timestamp_str}\n\nSee attached evidence.")

            # Attach the saved image
            if os.path.exists(image_path):
                with open(image_path, "rb") as f:
                    img_data = f.read()
                    msg.add_attachment(
                        img_data, maintype='image', subtype='jpeg', filename="intruder.jpg")

            # Send Email
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
                smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
                smtp.send_message(msg)

            print("✅ Email Alert Sent Successfully!")

        except Exception as e:
            print(f"❌ Error sending email: {e}")

        finally:
            task_queue.task_done()
