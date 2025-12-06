"""Email Alert System for Abnormality Detection"""
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import cv2
import os


class AlertSystem:
    """Handles email notifications for detected abnormalities"""
    
    def __init__(self, sender_email, sender_pass, receiver_email, cooldown=90):
        """Initialize alert system with email credentials
        
        Args:
            sender_email (str): Sender's email address (Gmail)
            sender_pass (str): Sender's app password (not regular password)
            receiver_email (str or list): Recipient email(s)
            cooldown (int): Cooldown period between alerts in seconds
        """
        self.sender_email = sender_email
        self.sender_pass = sender_pass
        
        # Handle single or multiple recipients
        if isinstance(receiver_email, str):
            self.receiver_emails = [receiver_email]
        else:
            self.receiver_emails = receiver_email
        
        self.cooldown = cooldown
        self.last_alert = {}  # Track last alert time per detection type
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
    
    def ok_to_send(self, alert_type):
        """Check if enough time has passed since last alert of this type
        
        Args:
            alert_type (str): Type of alert (violence, fire, fall)
            
        Returns:
            bool: True if enough cooldown time has passed
        """
        now = time.time()
        last = self.last_alert.get(alert_type, 0)
        
        if now - last >= self.cooldown:
            self.last_alert[alert_type] = now
            return True
        return False
    
    def send(self, alert_type, frame, confidence):
        """Send email alert with evidence image
        
        Args:
            alert_type (str): Type of abnormality detected
            frame (np.ndarray): Video frame with detected abnormality
            confidence (float): Confidence score (0-100)
            
        Returns:
            bool: True if email sent successfully
        """
        # Check cooldown
        if not self.ok_to_send(alert_type):
            return False
        
        try:
            # Encode frame as JPEG
            success, frame_encoded = cv2.imencode('.jpg', frame)
            if not success:
                print(f'Error encoding frame for {alert_type} alert')
                return False
            
            frame_bytes = frame_encoded.tobytes()
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(self.receiver_emails)
            msg['Subject'] = f'🚨 ALERT: {alert_type.upper()} Detected (Confidence: {confidence:.1f}%)'
            
            # Email body
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            body = f"""Abnormality Detection Alert
            
Detection Type: {alert_type.upper()}
Confidence: {confidence:.2f}%
Timestamp: {timestamp}

Please review the attached evidence image and take appropriate action.

This is an automated alert from the Real-Time Abnormality Detection System.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach image
            image = MIMEImage(frame_bytes, name=f'{alert_type}_{timestamp}.jpg')
            image.add_header('Content-ID', f'<{alert_type}_evidence>')
            msg.attach(image)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_pass)
                server.send_message(msg)
            
            print(f'✓ EMAIL SENT: {alert_type.upper()} alert to {self.receiver_emails}')
            return True
            
        except smtplib.SMTPAuthenticationError:
            print(f'❌ EMAIL ERROR: Authentication failed. Check email and password.')
            print('   Ensure you are using an App Password for Gmail, not your regular password.')
            return False
        except smtplib.SMTPException as e:
            print(f'❌ EMAIL ERROR: SMTP error - {e}')
            return False
        except Exception as e:
            print(f'❌ EMAIL ERROR: {e}')
            return False
