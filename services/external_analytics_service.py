import logging
from datetime import datetime, timezone

# This service handles data formatting and synchronization with the external analytics database
# schema provided in earlywarningdb.sql (PostgreSQL)

class ExternalAnalyticsService:
    def __init__(self):
        self.enabled = False # Set to True when DB credentials are provided
        
    def sync_alert(self, alert_data):
        """
        Formats and sends alert data to the external analytics dashboard database.
        Maps internal CAP fields to the analytics_alert table schema.
        """
        # Mapping table 'analytics_alert'
        external_record = {
            "reference_code": alert_data.get('identifier'),
            "headline": alert_data.get('headline'),
            "description": alert_data.get('description'),
            "category": alert_data.get('category', 'other').lower(),
            "status": alert_data.get('status', 'Actual').lower(),
            "acknowledged": False,
            "sent_at": alert_data.get('sent') if alert_data.get('workflow_stage') == 3 else None,
            "valid_from": alert_data.get('sent'), # Default to sent time
            "valid_until": None, # Should be calculated if available
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "agency_id": self._map_agency_id(alert_data.get('sender_agency')),
            "region_id": None, # Internal IDs would need mapping
            "campaign_id": None, # Optional
            "acted_on": False,
            "cap_certainty": alert_data.get('certainty', 'Unknown'),
            "cap_msg_type": alert_data.get('msgType', 'Alert'),
            "cap_scope": alert_data.get('scope', 'Unknown'),
            "cap_severity": alert_data.get('severity', 'Unknown'),
            "cap_urgency": alert_data.get('urgency', 'Unknown'),
            "workflow_stage": alert_data.get('workflow_stage', 1)
        }
        
        logging.info(f"Syncing alert {external_record['reference_code']} to external analytics DB.")
        
        # TODO: Implement actual PostgreSQL insert using psycopg2
        # Example:
        # INSERT INTO public.analytics_alert (...) VALUES (...)
        
        return True

    def _map_agency_id(self, agency_name):
        """Maps internal agency names to external database IDs (from earlywarningdb.sql)"""
        mapping = {
            "NADMO": 1,
            "GMeT": 2,
            "MMDA": 3
        }
        return mapping.get(agency_name, 1)

    def get_unnecessary_fields_report(self):
        """
        Points out unnecessary data in the provided schema for removal request.
        """
        return {
            "tables_for_removal": [
                "django_admin_log",
                "django_content_type",
                "django_migrations",
                "django_session",
                "auth_group",
                "auth_permission"
            ],
            "reason": "These are internal Django framework tables and are not required for raw data analytics or cross-platform alert display."
        }

external_analytics_service = ExternalAnalyticsService()
