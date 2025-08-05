import firebase_admin
from firebase_admin import credentials, messaging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging
from pathlib import Path

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import DeviceToken, NotificationLog, NotificationSettings, User
from app.models.notification import NotificationStatus

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
cred_path = Path(settings.FIREBASE_CREDENTIALS_PATH)
if not cred_path.is_absolute():
    cred_path = Path(__file__).parent.parent.parent / settings.FIREBASE_CREDENTIALS_PATH

try:
    cred = credentials.Certificate(str(cred_path))
    firebase_admin.initialize_app(cred)
    logger.info("Firebase Admin SDK initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
    raise


class NotificationService:
    """Service for sending push notifications via Firebase Cloud Messaging"""
    
    @staticmethod
    async def send_notification(
        user_id: str,
        body: str,
        title: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        notification_type: str = "daily_recommendation",
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Send a push notification to a specific user"""
        
        # Get active device tokens for the user
        # Convert string user_id to integer for query
        try:
            user_id_int = int(user_id)
        except ValueError:
            logger.error(f"Invalid user_id format: {user_id}")
            return {"success": False, "error": "Invalid user ID format"}
            
        tokens_query = await db.execute(
            select(DeviceToken).where(
                and_(
                    DeviceToken.user_id == user_id_int,
                    DeviceToken.is_active == True
                )
            )
        )
        device_tokens = tokens_query.scalars().all()
        
        if not device_tokens:
            logger.warning(f"No active device tokens found for user {user_id}")
            return {
                "success": False,
                "message": "No active device tokens found",
                "sent_count": 0
            }
        
        # Prepare notification
        notification = None
        if title:
            notification = messaging.Notification(
                title=title,
                body=body
            )
        
        # Prepare data payload
        if data is None:
            data = {}
        data['notification_type'] = notification_type
        data['timestamp'] = datetime.utcnow().isoformat()
        
        # Convert all data values to strings (FCM requirement)
        data_str = {k: str(v) for k, v in data.items()}
        
        # Android specific config for data-only messages
        android_config = messaging.AndroidConfig(
            priority='high',
            data=data_str
        )
        
        # APNS config for iOS
        apns_config = messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    content_available=True,
                    sound='default'
                )
            )
        )
        
        success_count = 0
        failed_count = 0
        
        # Send to each device token
        for device_token in device_tokens:
            # Create notification log
            log_entry = NotificationLog(
                user_id=user_id_int,  # Use integer user_id
                device_token_id=device_token.id,
                title=title,
                body=body,
                data=json.dumps(data),
                notification_type=notification_type,
                status=NotificationStatus.PENDING
            )
            db.add(log_entry)
            await db.flush()
            
            try:
                # Create message
                message = messaging.Message(
                    notification=notification,
                    data=data_str,
                    token=device_token.token,
                    android=android_config,
                    apns=apns_config
                )
                
                # Send message
                response = messaging.send(message)
                
                # Update log entry
                log_entry.status = NotificationStatus.SENT
                log_entry.sent_at = datetime.utcnow()
                log_entry.fcm_message_id = response
                
                # Update device token last used
                device_token.last_used_at = datetime.utcnow()
                
                success_count += 1
                logger.info(f"Notification sent successfully to {device_token.id}: {response}")
                
            except messaging.UnregisteredError:
                # Token is no longer valid
                logger.warning(f"Token {device_token.id} is unregistered, deactivating")
                device_token.is_active = False
                log_entry.status = NotificationStatus.FAILED
                log_entry.error_message = "Token unregistered"
                failed_count += 1
                
            except Exception as e:
                logger.error(f"Failed to send notification to {device_token.id}: {e}")
                log_entry.status = NotificationStatus.FAILED
                log_entry.error_message = str(e)
                failed_count += 1
        
        await db.commit()
        
        return {
            "success": success_count > 0,
            "message": f"Sent to {success_count} devices, {failed_count} failed",
            "sent_count": success_count,
            "failed_count": failed_count
        }
    
    @staticmethod
    async def send_batch_notifications(
        notifications: List[Dict[str, Any]],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Send multiple notifications in batch"""
        
        total_sent = 0
        total_failed = 0
        
        for notif in notifications:
            result = await NotificationService.send_notification(
                user_id=notif['user_id'],
                body=notif['body'],
                title=notif.get('title'),
                data=notif.get('data'),
                notification_type=notif.get('notification_type', 'daily_recommendation'),
                db=db
            )
            
            total_sent += result.get('sent_count', 0)
            total_failed += result.get('failed_count', 0)
        
        return {
            "success": total_sent > 0,
            "total_sent": total_sent,
            "total_failed": total_failed,
            "total_users": len(notifications)
        }
    
    @staticmethod
    async def validate_token(token: str) -> bool:
        """Validate if a FCM token is still valid"""
        try:
            # Create a dry run message
            message = messaging.Message(
                token=token,
                data={'test': 'validation'}
            )
            
            # Send with dry_run=True to validate without actually sending
            messaging.send(message, dry_run=True)
            return True
            
        except Exception as e:
            logger.warning(f"Token validation failed: {e}")
            return False
    
    @staticmethod
    async def cleanup_invalid_tokens(db: AsyncSession) -> int:
        """Cleanup invalid/expired tokens"""
        
        # Get all active tokens
        tokens_query = await db.execute(
            select(DeviceToken).where(DeviceToken.is_active == True)
        )
        tokens = tokens_query.scalars().all()
        
        invalid_count = 0
        
        for token in tokens:
            if not await NotificationService.validate_token(token.token):
                token.is_active = False
                token.updated_at = datetime.utcnow()
                invalid_count += 1
                logger.info(f"Deactivated invalid token: {token.id}")
        
        await db.commit()
        
        return invalid_count