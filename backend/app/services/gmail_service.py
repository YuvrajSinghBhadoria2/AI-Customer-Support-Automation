"""Gmail integration service for fetching and sending emails."""

import logging
import base64
from typing import List, Optional
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle

from app.config import settings
from app.schemas.ticket import TicketCreate

logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


class GmailService:
    """Service for Gmail API integration."""
    
    def __init__(self):
        """Initialize Gmail service."""
        self.service = None
        self.creds = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API.
        
        Returns:
            True if authentication successful
        """
        try:
            # Load credentials from token file if exists
            if os.path.exists(settings.gmail_token_file):
                with open(settings.gmail_token_file, 'rb') as token:
                    self.creds = pickle.load(token)
            
            # Refresh or get new credentials
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists(settings.gmail_credentials_file):
                        logger.error("Gmail credentials file not found")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        settings.gmail_credentials_file, SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)
                
                # Save credentials
                with open(settings.gmail_token_file, 'wb') as token:
                    pickle.dump(self.creds, token)
            
            # Build service
            self.service = build('gmail', 'v1', credentials=self.creds)
            logger.info("Gmail authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Gmail authentication failed: {e}")
            return False
    
    def fetch_unread_emails(self, max_results: int = 10) -> List[TicketCreate]:
        """
        Fetch unread emails from support inbox.
        
        Args:
            max_results: Maximum number of emails to fetch
            
        Returns:
            List of TicketCreate objects
        """
        if not self.service:
            if not self.authenticate():
                return []
        
        try:
            # Query for unread emails
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            tickets = []
            
            for message in messages:
                # Get full message
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()
                
                # Extract headers
                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')
                
                # Extract email address from "Name <email>" format
                if '<' in from_email and '>' in from_email:
                    from_email = from_email.split('<')[1].split('>')[0]
                
                # Extract body
                body = self._get_email_body(msg['payload'])
                
                # Create ticket
                ticket = TicketCreate(
                    customer_email=from_email,
                    subject=subject,
                    body=body,
                    source="gmail"
                )
                tickets.append(ticket)
                
                logger.info(f"Fetched email from {from_email}: {subject}")
            
            return tickets
            
        except Exception as e:
            logger.error(f"Failed to fetch emails: {e}")
            return []
    
    def _get_email_body(self, payload: dict) -> str:
        """Extract email body from payload."""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8')
        elif 'body' in payload:
            data = payload['body'].get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8')
        return ""
    
    def send_email(self, to: str, subject: str, body: str) -> bool:
        """
        Send email reply.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            
        Returns:
            True if sent successfully
        """
        if not self.service:
            if not self.authenticate():
                return False
        
        try:
            # Create message
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = f"Re: {subject}"
            
            # Encode message
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            logger.info(f"Sent email to {to}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def mark_as_read(self, message_id: str) -> bool:
        """Mark email as read."""
        if not self.service:
            return False
        
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to mark as read: {e}")
            return False


# Singleton instance
gmail_service = GmailService()
