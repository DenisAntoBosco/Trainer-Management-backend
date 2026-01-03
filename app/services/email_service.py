import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os
from ..core.config import settings

class EmailService:
    """
    Email service for sending notifications.
    Configure SMTP settings in .env file.
    """
    
    @staticmethod
    async def send_welcome_email(
        to_email: str,
        user_name: str,
        temporary_password: str,
        login_url: str = "http://localhost:8080"
    ) -> bool:
        """
        Send welcome email with temporary credentials to new user.
        Returns True if email sent successfully, False otherwise.
        """
        try:
            # Get SMTP configuration from settings
            smtp_host = settings.smtp_host
            smtp_port = settings.smtp_port or 587
            smtp_user = settings.smtp_user
            smtp_password = settings.smtp_password
            from_email = settings.from_email or smtp_user
            
            # Skip if SMTP not configured
            if not smtp_user or not smtp_password:
                print(f"⚠️  SMTP not configured. Email would be sent to: {to_email}")
                print(f"📧 Temporary Password: {temporary_password}")
                return False
            
            print(f"📤 Attempting to send email to: {to_email}")
            print(f"📧 Using SMTP: {smtp_host}:{smtp_port}")
            print(f"👤 SMTP User: {smtp_user}")
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = "Welcome to Trainer Management System"
            message["From"] = from_email
            message["To"] = to_email
            
            # HTML email body
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2563eb;">Welcome to Trainer Management System! 🎉</h2>
                        
                        <p>Hi <strong>{user_name}</strong>,</p>
                        
                        <p>Your account has been created successfully. Here are your login credentials:</p>
                        
                        <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                            <p style="margin: 5px 0;"><strong>Email:</strong> {to_email}</p>
                            <p style="margin: 5px 0;"><strong>Temporary Password:</strong> <code style="background-color: #e5e7eb; padding: 2px 6px; border-radius: 4px;">{temporary_password}</code></p>
                        </div>
                        
                        <p>
                            <a href="{login_url}" style="display: inline-block; background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0;">
                                Login to Your Account
                            </a>
                        </p>
                        
                        <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px; margin: 20px 0;">
                            <p style="margin: 0;"><strong>⚠️ Important:</strong> You will be required to change your password on first login for security purposes.</p>
                        </div>
                        
                        <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                            If you have any questions, please contact your administrator.
                        </p>
                        
                        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                        
                        <p style="color: #9ca3af; font-size: 12px;">
                            This is an automated message. Please do not reply to this email.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            # Plain text fallback
            text_body = f"""
            Welcome to Trainer Management System!
            
            Hi {user_name},
            
            Your account has been created successfully. Here are your login credentials:
            
            Email: {to_email}
            Temporary Password: {temporary_password}
            
            Login at: {login_url}
            
            ⚠️ IMPORTANT: You will be required to change your password on first login for security purposes.
            
            If you have any questions, please contact your administrator.
            """
            
            # Attach both versions
            part1 = MIMEText(text_body, "plain")
            part2 = MIMEText(html_body, "html")
            message.attach(part1)
            message.attach(part2)
            
            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(message)
            
            print(f"✅ Welcome email sent to: {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False
    
    @staticmethod
    async def send_password_reset_email(
        to_email: str,
        user_name: str,
        reset_token: str,
        reset_url: str = "http://localhost:8080/reset-password"
    ) -> bool:
        """
        Send password reset email with reset link.
        """
        try:
            smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_user = os.getenv("SMTP_USER", "")
            smtp_password = os.getenv("SMTP_PASSWORD", "")
            from_email = os.getenv("FROM_EMAIL", smtp_user)
            
            if not smtp_user or not smtp_password:
                print(f"⚠️  SMTP not configured. Reset link would be sent to: {to_email}")
                return False
            
            message = MIMEMultipart("alternative")
            message["Subject"] = "Password Reset Request"
            message["From"] = from_email
            message["To"] = to_email
            
            reset_link = f"{reset_url}?token={reset_token}"
            
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2563eb;">Password Reset Request</h2>
                        
                        <p>Hi <strong>{user_name}</strong>,</p>
                        
                        <p>We received a request to reset your password. Click the button below to reset it:</p>
                        
                        <p>
                            <a href="{reset_link}" style="display: inline-block; background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0;">
                                Reset Password
                            </a>
                        </p>
                        
                        <p style="color: #6b7280; font-size: 14px;">
                            This link will expire in 1 hour for security reasons.
                        </p>
                        
                        <p style="color: #6b7280; font-size: 14px;">
                            If you didn't request this, please ignore this email.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            text_body = f"""
            Password Reset Request
            
            Hi {user_name},
            
            We received a request to reset your password. Click the link below to reset it:
            
            {reset_link}
            
            This link will expire in 1 hour for security reasons.
            
            If you didn't request this, please ignore this email.
            """
            
            part1 = MIMEText(text_body, "plain")
            part2 = MIMEText(html_body, "html")
            message.attach(part1)
            message.attach(part2)
            
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(message)
            
            print(f"✅ Password reset email sent to: {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send password reset email to {to_email}: {str(e)}")
            return False
