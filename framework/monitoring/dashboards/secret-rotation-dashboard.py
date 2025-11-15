#!/usr/bin/env python3
"""
TTA.dev Secret Rotation Monitoring Dashboard

Real-time monitoring and visualization of secret rotation activities.
Provides comprehensive visibility into rotation status, success metrics,
and security compliance.

Features:
- Live rotation status monitoring
- Success/failure rate tracking
- Audit log analysis and reporting
- Alert generation for failures
- Team notifications (Slack/PagerDuty integration)
- Compliance reporting and visualization
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
import requests

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RotationDashboard:
    """Real-time monitoring dashboard for secret rotation activities"""

    def __init__(self):
        self.audit_dir = Path(project_root / 'audit-logs')
        self.dashboard_cache = {}
        self.cache_timeout = 300  # 5 minutes

        # Slack/PagerDuty integration settings
        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.pagerduty_integration_key = os.getenv('PAGERDUTY_INTEGRATION_KEY')

        # Dashboard metrics
        self.metrics = {
            'total_rotations': 0,
            'successful_rotations': 0,
            'failed_rotations': 0,
            'avg_rotation_time': 0.0,
            'services_rotated': set(),
            'active_rotations': 0
        }

    def get_rotation_status(self) -> Dict[str, Any]:
        """Get comprehensive rotation status overview"""
        now = datetime.now(timezone.utc)

        # Check for cache validity
        if 'status' in self.dashboard_cache:
            cache_time = self.dashboard_cache['status']['last_updated']
            if (now - cache_time).seconds < self.cache_timeout:
                return self.dashboard_cache['status']

        # Calculate metrics from audit logs
        status = {
            'summary': self._calculate_summary_metrics(),
            'recent_activity': self._get_recent_activity(10),
            'service_health': self._calculate_service_health(),
            'compliance_status': self._check_compliance_status(),
            'active_alerts': self._get_active_alerts(),
            'last_updated': now,
            'dashboard_version': '1.0.0'
        }

        self.dashboard_cache['status'] = status
        return status

    def _calculate_summary_metrics(self) -> Dict[str, Any]:
        """Calculate high-level rotation summary metrics"""
        rotation_logs = self._get_all_rotation_logs()

        total_rotations = len(rotation_logs)
        successful_rotations = sum(1 for log in rotation_logs if log['success'])
        failed_rotations = total_rotations - successful_rotations

        # Calculate success rate
        success_rate = (successful_rotations / total_rotations * 100) if total_rotations > 0 else 0

        # Identify services being rotated
        services = set()
        for log in rotation_logs:
            if 'service' in log:
                services.add(log['service'])

        # Calculate average rotation time (if available)
        rotation_times = []
        for log in rotation_logs:
            if 'rotation_time_seconds' in log.get('details', {}):
                rotation_times.append(log['details']['rotation_time_seconds'])

        avg_time = sum(rotation_times) / len(rotation_times) if rotation_times else 0

        return {
            'total_rotations': total_rotations,
            'successful_rotations': successful_rotations,
            'failed_rotations': failed_rotations,
            'success_rate_percent': round(success_rate, 2),
            'services_count': len(services),
            'services_list': list(services),
            'avg_rotation_time_seconds': round(avg_time, 2),
            'last_rotation': self._get_last_rotation_time()
        }

    def _get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent rotation activities"""
        rotation_logs = self._get_all_rotation_logs()

        # Sort by timestamp (most recent first)
        sorted_logs = sorted(
            rotation_logs,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )

        return sorted_logs[:limit]

    def _calculate_service_health(self) -> Dict[str, Any]:
        """Calculate health status for each service"""
        rotation_logs = self._get_all_rotation_logs()
        service_stats = defaultdict(lambda: {'total': 0, 'success': 0, 'recent_failures': 0})

        # Analyze last 24 hours
        one_day_ago = datetime.now(timezone.utc) - timedelta(hours=24)

        for log in rotation_logs:
            service = log.get('service', 'unknown')
            service_stats[service]['total'] += 1

            if log.get('success', False):
                service_stats[service]['success'] += 1

            # Check for recent failures
            if not log.get('success', False) and log.get('timestamp'):
                try:
                    log_time = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                    if log_time > one_day_ago:
                        service_stats[service]['recent_failures'] += 1
                except:
                    pass

        # Calculate health status for each service
        health_status = {}
        for service, stats in service_stats.items():
            success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0

            if stats['recent_failures'] > 2:
                status = 'critical'
            elif success_rate < 90:
                status = 'warning'
            elif success_rate >= 99:
                status = 'healthy'
            else:
                status = 'normal'

            health_status[service] = {
                'status': status,
                'success_rate_percent': round(success_rate, 2),
                'total_rotations': stats['total'],
                'recent_failures': stats['recent_failures']
            }

        return health_status

    def _check_compliance_status(self) -> Dict[str, Any]:
        """Check compliance status against security policies"""
        compliance = {
            'audit_trail_compliant': True,
            'rotation_frequency_compliant': True,
            'access_controls_compliant': True,
            'data_masking_compliant': True,
            'overall_compliant': True,
            'issues': []
        }

        rotation_logs = self._get_all_rotation_logs()

        # Check audit trail compliance
        for log in rotation_logs:
            masked_details = log.get('masked_details', {})
            if any(key in str(masked_details) for key in ['api_key', 'token', 'secret']):
                compliance['data_masking_compliant'] = False
                compliance['issues'].append(f"Unmasked sensitive data in log: {log.get('correlation_id')}")

        # Check rotation frequency (should rotate at least weekly)
        services_last_rotated = {}
        for log in rotation_logs:
            service = log.get('service')
            if service and log.get('success'):
                timestamp = log.get('timestamp')
                services_last_rotated[service] = timestamp

        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        for service, last_rotation in services_last_rotated.items():
            try:
                rotation_time = datetime.fromisoformat(last_rotation.replace('Z', '+00:00'))
                if rotation_time < seven_days_ago:
                    compliance['rotation_frequency_compliant'] = False
                    compliance['issues'].append(f"Service {service} not rotated in last 7 days")
            except:
                pass

        compliance['overall_compliant'] = all([
            compliance['audit_trail_compliant'],
            compliance['rotation_frequency_compliant'],
            compliance['access_controls_compliant'],
            compliance['data_masking_compliant']
        ])

        return compliance

    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get current active alerts"""
        alerts = []
        service_health = self._calculate_service_health()

        for service, health in service_health.items():
            if health['status'] == 'critical':
                alerts.append({
                    'severity': 'critical',
                    'service': service,
                    'message': f"Multiple recent failures ({health['recent_failures']}) for {service}",
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            elif health['status'] == 'warning':
                alerts.append({
                    'severity': 'warning',
                    'service': service,
                    'message': f"Low success rate ({health['success_rate_percent']}%) for {service}",
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })

        return alerts

    def _get_all_rotation_logs(self) -> List[Dict[str, Any]]:
        """Get all rotation logs from audit directory"""
        if 'logs' in self.dashboard_cache:
            return self.dashboard_cache['logs']

        logs = []
        if self.audit_dir.exists():
            for log_file in self.audit_dir.glob('*.json'):
                try:
                    with open(log_file, 'r') as f:
                        data = json.load(f)
                        if 'events' in data:
                            logs.extend(data['events'])
                        else:
                            logs.append(data)
                except Exception as e:
                    logger.warning(f"Failed to parse audit log {log_file}: {e}")

        self.dashboard_cache['logs'] = logs
        return logs

    def _get_last_rotation_time(self) -> Optional[str]:
        """Get timestamp of last successful rotation"""
        rotation_logs = self._get_all_rotation_logs()
        successful_rotations = [log for log in rotation_logs if log.get('success')]

        if not successful_rotations:
            return None

        latest = max(successful_rotations, key=lambda x: x.get('timestamp', ''))
        return latest.get('timestamp')

    def send_slack_notification(self, message: str, channel: str = "#security-alerts") -> bool:
        """Send notification to Slack"""
        if not self.slack_webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False

        payload = {
            "channel": channel,
            "text": f"🔐 Secret Rotation Alert: {message}",
            "username": "Secret Rotation Monitor",
            "icon_emoji": ":lock:"
        }

        try:
            response = requests.post(self.slack_webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

    def send_pagerduty_alert(self, title: str, description: str, severity: str = "error") -> bool:
        """Send alert to PagerDuty"""
        if not self.pagerduty_integration_key:
            logger.warning("PagerDuty integration key not configured")
            return False

        payload = {
            "routing_key": self.pagerduty_integration_key,
            "event_action": "trigger",
            "payload": {
                "summary": title,
                "source": "tta-secret-rotation",
                "severity": severity,
                "component": "secret-rotation-system",
                "group": "security",
                "class": "rotation-failure",
                "custom_details": {
                    "description": description,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
        }

        try:
            response = requests.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload,
                timeout=10
            )
            return response.status_code == 202
        except Exception as e:
            logger.error(f"Failed to send PagerDuty alert: {e}")
            return False

    def display_dashboard(self) -> None:
        """Display beautiful ASCII dashboard"""
        status = self.get_rotation_status()

        print("\n" + "=" * 80)
        print("🔐 TTA.DEV SECRET ROTATION MONITORING DASHBOARD")
        print("=" * 80)

        # Summary metrics
        summary = status['summary']
        print(f"\n📊 SUMMARY METRICS:")
        print(f"  Total Rotations:     {summary['total_rotations']}")
        print(f"  Success Rate:        {summary['success_rate_percent']}%")
        print(f"  Services Covered:    {summary['services_count']}")
        print(f"  Avg Rotation Time:   {summary['avg_rotation_time_seconds']}s")
        print(f"  Last Rotation:       {summary.get('last_rotation', 'Never') or 'Never'}")

        # Service health
        print(f"\n🏥 SERVICE HEALTH:")
        for service, health in status['service_health'].items():
            status_icon = {
                'healthy': '🟢',
                'normal': '🟡',
                'warning': '🟠',
                'critical': '🔴'
            }.get(health['status'], '❓')

            print(f"  {status_icon} {service}: {health['success_rate_percent']}% success "
                  f"({health['total_rotations']} total)")

        # Compliance status
        compliance = status['compliance_status']
        compliance_icon = "✅" if compliance['overall_compliant'] else "❌"
        print(f"\n{compliance_icon} COMPLIANCE STATUS: {'PASS' if compliance['overall_compliant'] else 'FAIL'}")

        if compliance['issues']:
            print("  Issues:")
            for issue in compliance['issues'][:3]:  # Show first 3 issues
                print(f"    • {issue}")

        # Active alerts
        alerts = status['active_alerts']
        if alerts:
            print(f"\n🚨 ACTIVE ALERTS ({len(alerts)}):")
            for alert in alerts[:3]:  # Show first 3 alerts
                severity_icon = {'critical': '🔴', 'warning': '🟠'}.get(alert['severity'], '🟡')
                print(f"  {severity_icon} {alert['service']}: {alert['message']}")

        # Recent activity
        recent = status['recent_activity']
        if recent:
            print(f"\n🔄 RECENT ACTIVITY:")
            for activity in recent[:5]:
                success_icon = "✅" if activity.get('success') else "❌"
                service = activity.get('service', 'unknown')
                event_type = activity.get('event_type', 'unknown')
                timestamp = activity.get('timestamp', '')[:19]  # YYYY-MM-DDTHH:MM:SS

                print(f"  {success_icon} {timestamp} {service}: {event_type}")

        print(f"\n📅 Last Updated: {status['last_updated'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("=" * 80)

    def check_and_alert(self) -> None:
        """Check for issues and send alerts if needed"""
        status = self.get_rotation_status()
        alerts = status['active_alerts']

        for alert in alerts:
            severity = alert['severity']
            service = alert['service']
            message = alert['message']

            # Send Slack notification
            if self.slack_webhook_url:
                slack_message = f"*{severity.upper()}*: {service} - {message}"
                self.send_slack_notification(slack_message)

            # Send PagerDuty alert for critical issues
            if severity == 'critical' and self.pagerduty_integration_key:
                title = f"Critical: Secret Rotation Failure - {service}"
                self.send_pagerduty_alert(title, message, "critical")


def main():
    """Main dashboard function"""
    dashboard = RotationDashboard()

    # Display dashboard
    dashboard.display_dashboard()

    # Check for alerts and send notifications
    dashboard.check_and_alert()

    print("\n💡 Tip: Run 'python monitoring/dashboards/secret-rotation-dashboard.py' for live monitoring")
    print("🔧 Configure SLACK_WEBHOOK_URL and PAGERDUTY_INTEGRATION_KEY for notifications")


if __name__ == "__main__":
    main()
