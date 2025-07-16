from discord_webhook import DiscordWebhook, DiscordEmbed
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

def send_discord_notification(message, pdf_path=None, webhook_url=None):
    """Send notification via Discord webhook"""
    if not webhook_url:
        print("Discord webhook URL not configured")
        return
    
    try:
        webhook = DiscordWebhook(url=webhook_url)
        
        embed = DiscordEmbed(
            title="📈 Portfolio Analysis Update",
            description=message,
            color=0x00ff00
        )
        embed.set_timestamp()
        
        webhook.add_embed(embed)
        
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                webhook.add_file(file=f.read(), filename=os.path.basename(pdf_path))
        
        response = webhook.execute()
        print("Discord notification sent successfully")
    except Exception as e:
        print(f"Error sending Discord notification: {e}")

def send_slack_notification(message, pdf_path=None, bot_token=None, channel=None):
    """Send notification via Slack"""
    if not bot_token or not channel:
        print("Slack configuration incomplete")
        return
    
    client = WebClient(token=bot_token)
    try:
        client.chat_postMessage(
            channel=channel,
            text=message
        )
        
        if pdf_path and os.path.exists(pdf_path):
            client.files_upload(
                channels=channel,
                file=pdf_path,
                title="Portfolio Report"
            )
        
        print("Slack notification sent successfully")
    except SlackApiError as e:
        print(f"Error sending Slack notification: {e.response['error']}")

def send_email_notification(message, pdf_path=None, smtp_server=None, smtp_port=None, from_email=None, password=None, to_email=None):
    """Send notification via email"""
    if not all([smtp_server, from_email, password, to_email]):
        print("Email configuration incomplete")
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = "📈 Portfolio Analysis Update"
        
        msg.attach(MIMEText(message, 'plain'))
        
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(pdf_path)}'
            )
            msg.attach(part)
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        print("Email notification sent successfully")
    except Exception as e:
        print(f"Error sending email notification: {e}")

def send_notification(notification_type, message, pdf_path=None, **kwargs):
    """Send notification based on configured method"""
    if notification_type == 'discord':
        send_discord_notification(message, pdf_path, webhook_url=kwargs.get('discord_webhook_url'))
    elif notification_type == 'slack':
        send_slack_notification(message, pdf_path, bot_token=kwargs.get('slack_bot_token'), channel=kwargs.get('slack_channel'))
    elif notification_type == 'email':
        send_email_notification(message, pdf_path, smtp_server=kwargs.get('email_smtp_server'), smtp_port=kwargs.get('email_smtp_port'), from_email=kwargs.get('email_from'), password=kwargs.get('email_password'), to_email=kwargs.get('email_to')) 