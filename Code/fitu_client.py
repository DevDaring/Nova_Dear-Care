#!/usr/bin/env python3
"""
fitu_client.py — Fit-U Mobile App Integration for Dear-Care
Fetches fitness data from Fit-U before processing.
Sends SNS push notification to Fit-U after verdict is ready.

This module is designed to work gracefully even if Fit-U app is not present.
All AWS operations fall back to empty responses on failure.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from utils import check_internet

logger = logging.getLogger(__name__)


class FituClient:
    """
    Client for integrating with the Fit-U mobile companion app.

    This client handles:
    1. Fetching health data from Fit-U before encounter analysis
    2. Sending push notifications to Fit-U after verdict is ready

    All methods gracefully handle offline scenarios and missing Fit-U app.
    """

    def __init__(self, config):
        """
        Initialize Fit-U client with configuration.

        Args:
            config: Config object with AWS settings
        """
        self.config = config
        self._s3 = None
        self._dynamodb = None
        self._sns = None

        # Configuration from config object
        self.table_name = getattr(config, 'FITU_DYNAMODB_TABLE', 'dear-care-fitu-health')
        self.bucket = getattr(config, 'S3_BUCKET_NAME', 'dear-care-data')
        self.sns_topic_arn = getattr(config, 'FITU_SNS_TOPIC_ARN', '')
        self.s3_prefix = getattr(config, 'FITU_DATA_S3_PREFIX', 'fitu-companion/')

    def _get_s3(self):
        """Lazy initialization of S3 client."""
        if self._s3 is None and check_internet():
            try:
                import boto3
                self._s3 = boto3.client('s3', region_name=self.config.AWS_REGION)
            except Exception as e:
                logger.warning("[FITU] S3 client init failed: %s", e)
        return self._s3

    def _get_dynamodb(self):
        """Lazy initialization of DynamoDB resource."""
        if self._dynamodb is None and check_internet():
            try:
                import boto3
                self._dynamodb = boto3.resource('dynamodb', region_name=self.config.AWS_REGION)
            except Exception as e:
                logger.warning("[FITU] DynamoDB client init failed: %s", e)
        return self._dynamodb

    def _get_sns(self):
        """Lazy initialization of SNS client."""
        if self._sns is None and check_internet():
            try:
                import boto3
                self._sns = boto3.client('sns', region_name=self.config.AWS_REGION)
            except Exception as e:
                logger.warning("[FITU] SNS client init failed: %s", e)
        return self._sns

    # ------------------------------------------------------------------
    # STEP A: Fetch Fit-U health data BEFORE Dear-Care processing
    # ------------------------------------------------------------------

    def fetch_latest_fitu_data(self, worker_id: str) -> Dict:
        """
        Called at the START of each encounter, before AI analysis.
        Reads the latest Fit-U health snapshot for the given worker from DynamoDB.

        Args:
            worker_id: The health worker ID

        Returns:
            Dict with keys: steps, distance_km, speed_kmh, activity,
            latitude, longitude, heart_rate_estimated, timestamp.
            Returns empty dict if no data found or on error.
        """
        if not check_internet():
            logger.info("[FITU] Offline - skipping Fit-U data fetch")
            return {}

        if not worker_id:
            logger.warning("[FITU] No worker_id provided")
            return {}

        try:
            dynamodb = self._get_dynamodb()
            if dynamodb is None:
                logger.warning("[FITU] DynamoDB not available")
                return {}

            table = dynamodb.Table(self.table_name)
            response = table.get_item(Key={'worker_id': worker_id})
            item = response.get('Item', {})

            if item:
                logger.info(
                    "[FITU] Fetched Fit-U data for worker %s: "
                    "steps=%s, activity=%s",
                    worker_id,
                    item.get('steps', 0),
                    item.get('activity', 'unknown')
                )
            else:
                logger.info("[FITU] No Fit-U data found for worker %s", worker_id)

            return item

        except Exception as e:
            logger.error("[FITU] Failed to fetch Fit-U data: %s", e)
            return {}

    # ------------------------------------------------------------------
    # STEP B: Push notification to Fit-U AFTER verdict is synced to S3
    # ------------------------------------------------------------------

    def notify_fitu_verdict_ready(
        self,
        worker_id: str,
        encounter_id: str,
        triage_level: str,
        summary: str
    ) -> bool:
        """
        Called AFTER the final Dear-Care verdict is saved to S3.
        Publishes an SNS message that triggers a push notification on the Fit-U app.

        Args:
            worker_id: The health worker ID
            encounter_id: The encounter ID
            triage_level: "URGENT" | "FOLLOW_UP" | "ROUTINE"
            summary: 1-2 sentence plain-language summary from Bedrock

        Returns:
            True on success, False on failure or if SNS not configured
        """
        if not check_internet():
            logger.info("[FITU] Offline - will notify Fit-U when online")
            return False

        if not self.sns_topic_arn:
            logger.info("[FITU] SNS topic not configured - skipping Fit-U notification")
            return False

        try:
            sns = self._get_sns()
            if sns is None:
                logger.warning("[FITU] SNS not available")
                return False

            payload = {
                "notification_type": "DEAR_CARE_VERDICT",
                "worker_id": worker_id,
                "encounter_id": encounter_id,
                "triage_level": triage_level,
                "summary": summary[:500],  # Truncate for SNS limits
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "s3_path": f"encounters/{worker_id}/{encounter_id}/verdict.json"
            }

            message = json.dumps(payload)
            sns.publish(
                TopicArn=self.sns_topic_arn,
                Message=message,
                Subject=f"Dear-Care Verdict Ready — {triage_level}",
                MessageAttributes={
                    'worker_id': {
                        'DataType': 'String',
                        'StringValue': worker_id
                    },
                    'triage_level': {
                        'DataType': 'String',
                        'StringValue': triage_level
                    }
                }
            )

            logger.info(
                "[FITU] SNS notification sent for encounter %s, triage=%s",
                encounter_id,
                triage_level
            )
            return True

        except Exception as e:
            logger.error("[FITU] Failed to send SNS notification: %s", e)
            return False

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------

    def format_fitu_for_prompt(self, fitu_data: Dict) -> str:
        """
        Format Fit-U data for inclusion in Bedrock health analysis prompt.

        Args:
            fitu_data: Dict from fetch_latest_fitu_data()

        Returns:
            Formatted string for AI prompt, or empty string if no data
        """
        if not fitu_data:
            return ""

        return (
            f"MOBILITY DATA (from Fit-U companion app):\n"
            f"- Steps today: {fitu_data.get('steps', 'N/A')}\n"
            f"- Distance walked: {fitu_data.get('distance_km', 'N/A')} km\n"
            f"- Current activity: {fitu_data.get('activity', 'N/A')}\n"
            f"- Estimated speed: {fitu_data.get('speed_kmh', 'N/A')} km/h\n"
            f"- Location: {fitu_data.get('latitude', 'N/A')}, {fitu_data.get('longitude', 'N/A')}\n"
        )

    def is_available(self) -> bool:
        """Check if Fit-U integration is available and configured."""
        return check_internet() and bool(self.sns_topic_arn)
