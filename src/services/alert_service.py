"""
Alert Service

Business logic service for managing alert generation, prioritization,
and coordination with UI components.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum

from ..domain.models import Alert, AlertPriority, AlertStatus, Manifest, MuteStatus
from ..infrastructure.repositories import MuteRepository
from ..infrastructure.exceptions import AlertProcessingException


class LayoutMode(Enum):
    """UI layout modes for alert display."""
    SINGLE_MAXIMIZED = "single_maximized"
    GRID = "grid"
    COMPACT = "compact"
    MINIMAL = "minimal"


@dataclass
class AlertSummary:
    """Summary of current alert state."""
    total_alerts: int
    active_alerts: int
    high_priority_alerts: int
    medium_priority_alerts: int
    low_priority_alerts: int
    muted_alerts: int
    acknowledged_alerts: int
    layout_mode: LayoutMode
    has_missed_alerts: bool
    oldest_alert_age_minutes: Optional[int] = None
    newest_alert_age_minutes: Optional[int] = None


@dataclass
class AlertConfiguration:
    """Configuration for alert behavior."""
    sound_enabled: bool = True
    visual_flash_enabled: bool = True
    repeat_interval_minutes: int = 5
    auto_dismiss_timeout_minutes: int = 30
    max_alerts_per_manifest: int = 10
    single_alert_scaling: bool = True
    prioritize_high_alerts: bool = True


class AlertService:
    """Service for managing alert generation and display logic.
    
    This service provides core alert functionality including:
    - Alert generation and prioritization
    - Layout mode calculation (single alert scaling)
    - Alert filtering and grouping
    - Mute status integration
    - Alert lifecycle management
    - Performance optimization for UI updates
    """
    
    def __init__(self, mute_repository: MuteRepository):
        """Initialize alert service.
        
        Args:
            mute_repository: Repository for mute status management
        """
        self.mute_repository = mute_repository
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Internal alert storage
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: List[Alert] = []
        self._last_alert_check: Optional[datetime] = None
        
        # Configuration
        self.config = AlertConfiguration()
        
        self.logger.info("AlertService initialized")
    
    def process_alerts(self, manifests: List[Manifest], 
                      configured_times: List[str],
                      configured_carriers: List[str],
                      acknowledgments: List) -> List[Alert]:
        """Process manifests and generate alerts for missing carriers.
        
        Args:
            manifests: List of current manifests
            configured_times: Expected manifest times
            configured_carriers: Expected carrier names
            acknowledgments: List of acknowledgments
            
        Returns:
            List of active alerts
            
        Raises:
            AlertProcessingException: If alert processing fails
        """
        try:
            current_time = datetime.now()
            new_alerts = []
            
            self.logger.debug(f"Processing alerts for {len(manifests)} manifests")
            
            # Get current date
            current_date = current_time.strftime("%Y-%m-%d")
            
            # Process each configured time
            for manifest_time in configured_times:
                # Check if this time has passed
                try:
                    manifest_datetime = datetime.strptime(f"{current_date} {manifest_time}", "%Y-%m-%d %H:%M")
                    
                    # Only generate alerts for past manifest times
                    if manifest_datetime <= current_time:
                        time_alerts = self._process_time_alerts(
                            manifests, manifest_time, configured_carriers, 
                            acknowledgments, current_date, current_time
                        )
                        new_alerts.extend(time_alerts)
                        
                except ValueError:
                    self.logger.warning(f"Invalid manifest time format: {manifest_time}")
                    continue
            
            # Update active alerts
            self._update_active_alerts(new_alerts)
            
            # Apply mute filtering
            filtered_alerts = self._apply_mute_filtering(list(self._active_alerts.values()))
            
            self.logger.info(f"Generated {len(new_alerts)} new alerts, "
                           f"{len(filtered_alerts)} active after filtering")
            
            return filtered_alerts
            
        except Exception as e:
            error_msg = f"Alert processing failed: {e}"
            self.logger.error(error_msg)
            raise AlertProcessingException(error_msg)
    
    def calculate_layout_mode(self, alerts: List[Alert]) -> LayoutMode:
        """Calculate optimal layout mode based on current alerts.
        
        This implements the single alert scaling logic from the original system.
        
        Args:
            alerts: List of current alerts
            
        Returns:
            Recommended layout mode
        """
        try:
            if not alerts:
                return LayoutMode.MINIMAL
            
            # Check for missed alerts (alerts older than repeat interval)
            has_missed_alerts = self._has_missed_alerts(alerts)
            
            # Single alert scaling: maximize single alerts when no missed alerts
            if (len(alerts) == 1 and 
                not has_missed_alerts and 
                self.config.single_alert_scaling):
                return LayoutMode.SINGLE_MAXIMIZED
            
            # Determine grid layout based on alert count
            if len(alerts) <= 4:
                return LayoutMode.GRID
            elif len(alerts) <= 8:
                return LayoutMode.COMPACT
            else:
                return LayoutMode.MINIMAL
                
        except Exception as e:
            self.logger.warning(f"Layout calculation failed: {e}")
            return LayoutMode.GRID
    
    def get_alert_summary(self, alerts: List[Alert]) -> AlertSummary:
        """Get comprehensive summary of current alert state.
        
        Args:
            alerts: List of current alerts
            
        Returns:
            Alert summary with statistics and layout information
        """
        try:
            if not alerts:
                return AlertSummary(
                    total_alerts=0,
                    active_alerts=0,
                    high_priority_alerts=0,
                    medium_priority_alerts=0,
                    low_priority_alerts=0,
                    muted_alerts=0,
                    acknowledged_alerts=0,
                    layout_mode=LayoutMode.MINIMAL,
                    has_missed_alerts=False
                )
            
            # Count alerts by priority
            priority_counts = {
                AlertPriority.HIGH: 0,
                AlertPriority.MEDIUM: 0,
                AlertPriority.LOW: 0
            }
            
            active_count = 0
            acknowledged_count = 0
            
            for alert in alerts:
                if alert.status == AlertStatus.ACTIVE:
                    active_count += 1
                    if alert.priority in priority_counts:
                        priority_counts[alert.priority] += 1
                elif alert.status == AlertStatus.ACKNOWLEDGED:
                    acknowledged_count += 1
            
            # Calculate alert ages
            current_time = datetime.now()
            ages_minutes = []
            for alert in alerts:
                if alert.created_at:
                    age = (current_time - alert.created_at).total_seconds() / 60
                    ages_minutes.append(int(age))
            
            oldest_age = max(ages_minutes) if ages_minutes else None
            newest_age = min(ages_minutes) if ages_minutes else None
            
            # Check mute status
            mute_status = self._get_mute_status()
            muted_count = len(alerts) if mute_status.is_currently_muted() else 0
            
            return AlertSummary(
                total_alerts=len(alerts),
                active_alerts=active_count,
                high_priority_alerts=priority_counts[AlertPriority.HIGH],
                medium_priority_alerts=priority_counts[AlertPriority.MEDIUM],
                low_priority_alerts=priority_counts[AlertPriority.LOW],
                muted_alerts=muted_count,
                acknowledged_alerts=acknowledged_count,
                layout_mode=self.calculate_layout_mode(alerts),
                has_missed_alerts=self._has_missed_alerts(alerts),
                oldest_alert_age_minutes=oldest_age,
                newest_alert_age_minutes=newest_age
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate alert summary: {e}")
            return AlertSummary(
                total_alerts=0,
                active_alerts=0,
                high_priority_alerts=0,
                medium_priority_alerts=0,
                low_priority_alerts=0,
                muted_alerts=0,
                acknowledged_alerts=0,
                layout_mode=LayoutMode.MINIMAL,
                has_missed_alerts=False
            )
    
    def filter_alerts_by_priority(self, alerts: List[Alert], 
                                 min_priority: AlertPriority) -> List[Alert]:
        """Filter alerts by minimum priority level.
        
        Args:
            alerts: List of alerts to filter
            min_priority: Minimum priority level
            
        Returns:
            Filtered list of alerts
        """
        try:
            priority_order = {
                AlertPriority.LOW: 1,
                AlertPriority.MEDIUM: 2,
                AlertPriority.HIGH: 3
            }
            
            min_level = priority_order.get(min_priority, 1)
            
            return [
                alert for alert in alerts
                if priority_order.get(alert.priority, 1) >= min_level
            ]
            
        except Exception as e:
            self.logger.warning(f"Priority filtering failed: {e}")
            return alerts
    
    def group_alerts_by_time(self, alerts: List[Alert]) -> Dict[str, List[Alert]]:
        """Group alerts by manifest time.
        
        Args:
            alerts: List of alerts to group
            
        Returns:
            Dictionary mapping manifest times to alert lists
        """
        grouped = {}
        
        for alert in alerts:
            time_key = alert.manifest_time or "unknown"
            if time_key not in grouped:
                grouped[time_key] = []
            grouped[time_key].append(alert)
        
        return grouped
    
    def group_alerts_by_carrier(self, alerts: List[Alert]) -> Dict[str, List[Alert]]:
        """Group alerts by carrier name.
        
        Args:
            alerts: List of alerts to group
            
        Returns:
            Dictionary mapping carrier names to alert lists
        """
        grouped = {}
        
        for alert in alerts:
            carrier_key = alert.carrier_name or "unknown"
            if carrier_key not in grouped:
                grouped[carrier_key] = []
            grouped[carrier_key].append(alert)
        
        return grouped
    
    def should_show_visual_alert(self, alerts: List[Alert]) -> bool:
        """Determine if visual alerts should be shown.
        
        Args:
            alerts: Current alerts
            
        Returns:
            True if visual alerts should be displayed
        """
        try:
            # Check mute status
            mute_status = self._get_mute_status()
            if mute_status.is_currently_muted():
                return False
            
            # Check if there are active alerts
            active_alerts = [a for a in alerts if a.status == AlertStatus.ACTIVE]
            return len(active_alerts) > 0
            
        except Exception as e:
            self.logger.warning(f"Visual alert check failed: {e}")
            return False
    
    def should_play_sound_alert(self, alerts: List[Alert]) -> bool:
        """Determine if sound alerts should be played.
        
        Args:
            alerts: Current alerts
            
        Returns:
            True if sound alerts should be played
        """
        try:
            if not self.config.sound_enabled:
                return False
            
            # Check mute status
            mute_status = self._get_mute_status()
            if mute_status.is_currently_muted():
                return False
            
            # Check for new or high priority alerts
            current_time = datetime.now()
            recent_threshold = current_time - timedelta(minutes=1)
            
            for alert in alerts:
                if (alert.status == AlertStatus.ACTIVE and
                    alert.priority == AlertPriority.HIGH and
                    alert.created_at and alert.created_at >= recent_threshold):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Sound alert check failed: {e}")
            return False
    
    def get_alert_by_id(self, alert_id: str) -> Optional[Alert]:
        """Get a specific alert by ID.
        
        Args:
            alert_id: Unique alert identifier
            
        Returns:
            Alert object or None if not found
        """
        return self._active_alerts.get(alert_id)
    
    def dismiss_alert(self, alert_id: str) -> bool:
        """Dismiss a specific alert.
        
        Args:
            alert_id: Unique alert identifier
            
        Returns:
            True if alert was dismissed
        """
        try:
            if alert_id in self._active_alerts:
                alert = self._active_alerts[alert_id]
                alert.status = AlertStatus.DISMISSED
                alert.dismissed_at = datetime.now()
                
                # Move to history
                self._alert_history.append(alert)
                del self._active_alerts[alert_id]
                
                self.logger.debug(f"Alert dismissed: {alert_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to dismiss alert {alert_id}: {e}")
            return False
    
    def clear_all_alerts(self) -> int:
        """Clear all active alerts.
        
        Returns:
            Number of alerts cleared
        """
        try:
            count = len(self._active_alerts)
            
            # Move all to history
            for alert in self._active_alerts.values():
                alert.status = AlertStatus.DISMISSED
                alert.dismissed_at = datetime.now()
                self._alert_history.append(alert)
            
            self._active_alerts.clear()
            
            self.logger.info(f"Cleared {count} alerts")
            return count
            
        except Exception as e:
            self.logger.error(f"Failed to clear alerts: {e}")
            return 0
    
    def update_configuration(self, config: AlertConfiguration) -> None:
        """Update alert configuration.
        
        Args:
            config: New alert configuration
        """
        self.config = config
        self.logger.info("Alert configuration updated")
    
    def _process_time_alerts(self, manifests: List[Manifest], manifest_time: str,
                           configured_carriers: List[str], acknowledgments: List,
                           date: str, current_time: datetime) -> List[Alert]:
        """Process alerts for a specific manifest time."""
        alerts = []
        
        # Get manifests for this time
        time_manifests = [m for m in manifests if m.time == manifest_time]
        present_carriers = {m.get_primary_carrier().name for m in time_manifests}
        
        # Get acknowledged carriers for this time
        acknowledged_carriers = {
            ack.carrier for ack in acknowledgments
            if ack.manifest_time == manifest_time
        }
        
        # Check for missing carriers
        for carrier_name in configured_carriers:
            if (carrier_name not in present_carriers and
                carrier_name not in acknowledged_carriers):
                
                # Create alert for missing carrier
                alert_id = f"missing_{carrier_name}_{date}_{manifest_time}"
                
                # Don't create duplicate alerts
                if alert_id not in self._active_alerts:
                    alert = Alert(
                        id=alert_id,
                        title=f"Missing Manifest: {carrier_name}",
                        message=f"{carrier_name} manifest is missing for {manifest_time}",
                        priority=self._calculate_alert_priority(manifest_time, current_time),
                        status=AlertStatus.ACTIVE,
                        created_at=current_time,
                        manifest_date=date,
                        manifest_time=manifest_time,
                        carrier_name=carrier_name,
                        requires_acknowledgment=True
                    )
                    alerts.append(alert)
        
        return alerts
    
    def _calculate_alert_priority(self, manifest_time: str, current_time: datetime) -> AlertPriority:
        """Calculate alert priority based on how overdue the manifest is."""
        try:
            current_date = current_time.strftime("%Y-%m-%d")
            manifest_datetime = datetime.strptime(f"{current_date} {manifest_time}", "%Y-%m-%d %H:%M")
            
            # Calculate how long the manifest is overdue
            overdue_minutes = (current_time - manifest_datetime).total_seconds() / 60
            
            if overdue_minutes > 60:  # More than 1 hour overdue
                return AlertPriority.HIGH
            elif overdue_minutes > 30:  # More than 30 minutes overdue
                return AlertPriority.MEDIUM
            else:
                return AlertPriority.LOW
                
        except ValueError:
            return AlertPriority.MEDIUM
    
    def _update_active_alerts(self, new_alerts: List[Alert]) -> None:
        """Update the active alerts collection."""
        for alert in new_alerts:
            self._active_alerts[alert.id] = alert
        
        # Remove resolved alerts (carriers that now have manifests or acknowledgments)
        # This would need additional logic to check against current state
    
    def _apply_mute_filtering(self, alerts: List[Alert]) -> List[Alert]:
        """Apply mute status filtering to alerts."""
        try:
            mute_status = self._get_mute_status()
            
            if mute_status.is_currently_muted():
                # Return empty list if muted, but keep alerts in memory
                return []
            
            return alerts
            
        except Exception as e:
            self.logger.warning(f"Mute filtering failed: {e}")
            return alerts
    
    def _has_missed_alerts(self, alerts: List[Alert]) -> bool:
        """Check if there are missed alerts (older than repeat interval)."""
        if not alerts:
            return False
        
        current_time = datetime.now()
        threshold = timedelta(minutes=self.config.repeat_interval_minutes)
        
        for alert in alerts:
            if (alert.created_at and 
                current_time - alert.created_at > threshold):
                return True
        
        return False
    
    def _get_mute_status(self) -> MuteStatus:
        """Get current mute status from repository."""
        try:
            return self.mute_repository.load_mute_status()
        except Exception as e:
            self.logger.warning(f"Failed to load mute status: {e}")
            # Return unmuted status as fallback
            from ..domain.models import MuteStatus
            return MuteStatus.create_unmuted()
