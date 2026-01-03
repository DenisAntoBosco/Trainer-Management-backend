import boto3
import json
import os
from typing import Optional
from botocore.exceptions import ClientError, NoCredentialsError

class SecretsManager:
    def __init__(self):
        try:
            self.client = boto3.client('secretsmanager')
            self.available = True
        except (NoCredentialsError, Exception):
            self.client = None
            self.available = False
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        """
        Retrieve a secret from AWS Secrets Manager
        """
        if not self.available:
            return None
            
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return response['SecretString']
        except ClientError as e:
            print(f"Error retrieving secret {secret_name}: {e}")
            return None
    
    def get_database_url(self) -> Optional[str]:
        """
        Get DATABASE_URL from environment variable or AWS Secrets Manager
        """
        # First try environment variable
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            return database_url
        
        # If not found and AWS is available, try AWS Secrets Manager
        if self.available:
            secret_name = os.getenv('DATABASE_SECRET_NAME', 'trainer-management/database')
            secret_value = self.get_secret(secret_name)
            
            if secret_value:
                try:
                    # If secret is JSON format
                    secret_dict = json.loads(secret_value)
                    return secret_dict.get('DATABASE_URL')
                except json.JSONDecodeError:
                    # If secret is plain text
                    return secret_value
        
        return None

secretsmanager = SecretsManager()