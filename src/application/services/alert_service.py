"""
Alert Service - Core business logic for alert management.

Handles alert triggering, layout calculations, and alert state management.
Implements the single alert scaling feature and alert prioritization logic.
"""

from typing import List, Optional, Dict, Set
from datetime import datetime, timedelta
from enum import Enum
import logging

from ...domain.models.manifest import Manifest, ManifestStatus
from ...domain.models.carrier import Carrier
from ...domain.models.alert import Alert, AlertPriority, AlertType
from ...domain.models.mute_status import MuteStatus
from ...infrastructure.repositories.manifest_repository import ManifestRepository
from ...infrastructure.repositories.mute_repository import MuteRepository
from ...infrastructure.exceptions import BusinessLogicException


class LayoutMode(Enum):
    """Layout modes for the alert display."""
    NORMAL = "normal"           # Standard grid layout
    SINGLE_CARD = "single_card" # Single card maximized mode
    NO_ALERTS = "no_alerts"     # No active alerts


class AlertService:
    """Service for managing alert logic and display calculations.
    
    This service implements the core business logic for:
    - Determining when alerts should be triggered
    - Calculating optimal layout modes (single card scaling)
    - Managing alert priorities and states
    - Coordinating with mute system
    """
    
    def __init__(self, 
                 manifest_repository: ManifestRepository,
                 mute_repository: MuteRepository,
                 logger: Optional[logging.Logger] = None):
        """Initialize the alert service.
        
        Args:
            manifest_repository: Repository for manifest data
            mute_repository: Repository for mute status
            logger: Optional logger instance
        """
        self.manifest_repository = manifest_repository
        self.mute_repository = mute_repository
        self.logger = logger or logging.getLogger(__name__)
        
        # Alert configuration
        self.alert_window_minutes = 30  # How long after manifest time to show alerts
        self.pre_alert_minutes = 2      # How early to start showing alerts
        
        self.logger.info("AlertService initialized")
    
    def calculate_layout_mode(self, manifests: List[Manifest], 
                            current_time: Optional[datetime] = None) -> LayoutMode:
        """Calculate the optimal layout mode based on current alerts.
        
        This implements the single alert scaling feature:
        - If exactly one manifest has active alerts and no missed alerts exist, use single card mode
        - Otherwise use normal grid layout
        
        Args:
            manifests: List of all manifests to evaluate
            current_time: Current time for calculations (defaults to now)
            
        Returns:
            LayoutMode enum indicating optimal layout
        """
        if current_time is None:
            current_time = datetime.now()
        
        try:
            # If system is muted, show no alerts layout
            if self._is_globally_muted():
                return LayoutMode.NO_ALERTS
                
            # Count manifests that would trigger alerts
            active_manifests = []
            missed_manifests = []
            
            for manifest in manifests:
                if self.should_trigger_alert(manifest, current_time):
                    status = manifest.get_status(current_time)
                    if status == ManifestStatus.ACTIVE:
                        active_manifests.append(manifest)
                    elif status == ManifestStatus.MISSED:
                        missed_manifests.append(manifest)
            
            # Single card mode conditions:
            # 1. Exactly one manifest has active alerts
            # 2. No manifests have missed alerts
            
            if len(active_manifests) == 1 and len(missed_manifests) == 0:
                self.logger.debug(f"Single card mode triggered for manifest {active_manifests[0].time}")
                return LayoutMode.SINGLE_CARD
            
            elif len(active_manifests) > 0 or len(missed_manifests) > 0:
                self.logger.debug(f"Normal layout mode - {len(active_manifests)} active, {len(missed_manifests)} missed")
                return LayoutMode.NORMAL
            
            else:
                self.logger.debug("No alerts mode - no active alerts")
                return LayoutMode.NO_ALERTS
                
        except Exception as e:
            self.logger.error(f"Error calculating layout mode: {e}")
            # Fallback to normal mode on error
            return LayoutMode.NORMAL
    
    def should_trigger_alert(self, manifest: Manifest, 
                           current_time: Optional[datetime] = None) -> bool:
        """Determine if a manifest should trigger visual/audio alerts.
        
        Args:
            manifest: Manifest to check
            current_time: Current time for calculations (defaults to now)
            
        Returns:
            True if manifest should show alerts
        """
        if current_time is None:
            current_time = datetime.now()
        
        try:
            # Check if all carriers are acknowledged first
            if manifest.acknowledged:
                return False
            
            # Check if manifest is in alertable state
            if not manifest.is_active(current_time):
                return False
            
            # Check if system is muted
            if self._is_globally_muted():
                return False
            
            # Check if this specific manifest is muted
            if self._is_manifest_muted(manifest):
                return False
            
            self.logger.debug(f"Alert triggered for manifest {manifest.time}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking alert trigger for {manifest.time}: {e}")
            return False
    
    def get_alert_summary(self, manifests: List[Manifest], 
                         current_time: Optional[datetime] = None) -> Dict:
        """Get comprehensive summary of current alert state.
        
        Args:
            manifests: List of manifests to analyze
            current_time: Current time for calculations (defaults to now)
            
        Returns:
            Dictionary containing alert summary statistics
        """
        if current_time is None:
            current_time = datetime.now()
        
        try:
            summary = {
                'total_manifests': len(manifests),
                'active_manifests': [],
                'missed_manifests': [],
                'pending_manifests': [],
                'acknowledged_manifests': [],
                'total_alerts': 0,
                'active_alerts': 0,
                'missed_alerts': 0,
                'muted': self._is_globally_muted(),
                'layout_mode': LayoutMode.NO_ALERTS
            }
            
            for manifest in manifests:
                status = manifest.get_status(current_time)
                
                if status == ManifestStatus.ACTIVE:
                    if not manifest.acknowledged:
                        summary['active_manifests'].append(manifest)
                        summary['active_alerts'] += len(manifest.get_unacknowledged_carriers())
                elif status == ManifestStatus.MISSED:
                    if not manifest.acknowledged:
                        summary['missed_manifests'].append(manifest)
                        summary['missed_alerts'] += len(manifest.get_unacknowledged_carriers())
                elif status == ManifestStatus.PENDING:
                    summary['pending_manifests'].append(manifest)
                elif status == ManifestStatus.ACKNOWLEDGED:
                    summary['acknowledged_manifests'].append(manifest)
            
            summary['total_alerts'] = summary['active_alerts'] + summary['missed_alerts']
            
            # Calculate layout mode based on current state
            if self._is_globally_muted():
                summary['layout_mode'] = LayoutMode.NO_ALERTS
            elif len(summary['active_manifests']) == 1 and len(summary['missed_manifests']) == 0:
                summary['layout_mode'] = LayoutMode.SINGLE_CARD
            elif summary['total_alerts'] > 0:
                summary['layout_mode'] = LayoutMode.NORMAL
            else:
                summary['layout_mode'] = LayoutMode.NO_ALERTS
            
            self.logger.debug(f"Alert summary: {summary['total_alerts']} alerts, "
                            f"{len(summary['active_manifests'])} active, "
                            f"{len(summary['missed_manifests'])} missed")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating alert summary: {e}")
            # Return safe default summary
            return {
                'total_manifests': len(manifests),
                'active_manifests': [],
                'missed_manifests': [],
                'pending_manifests': [],
                'acknowledged_manifests': [],
                'total_alerts': 0,
                'active_alerts': 0,
                'missed_alerts': 0,
                'muted': True,
                'layout_mode': LayoutMode.NO_ALERTS
            }
    
    def create_alert(self, manifest: Manifest, 
                    carrier: Optional[Carrier] = None,
                    alert_type: AlertType = AlertType.VISUAL,
                    current_time: Optional[datetime] = None) -> Alert:
        """Create an alert object for a manifest/carrier.
        
        Args:
            manifest: Manifest triggering the alert
            carrier: Optional specific carrier (None for manifest-level alert)
            alert_type: Type of alert to create
            current_time: Current time for calculations (defaults to now)
            
        Returns:
            Alert object with appropriate priority and metadata
        """
        if current_time is None:
            current_time = datetime.now()
            
        try:
            # Determine priority based on manifest status and timing
            priority = self._calculate_alert_priority(manifest, current_time)
            
            # Generate alert ID
            alert_id = f"manifest_{manifest.date}_{manifest.time}"
            if carrier:
                alert_id += f"_{carrier.name}"
            alert_id = alert_id.replace(":", "").replace("-", "")
            
            # Generate title and message
            title, message = self._generate_alert_title_message(manifest, carrier)
            
            alert = Alert(
                alert_id=alert_id,
                alert_type=alert_type,
                priority=priority,
                title=title,
                message=message,
                manifest=manifest
            )
            
            self.logger.debug(f"Created {priority.value} alert for {manifest.time}")
            return alert
            
        except Exception as e:
            self.logger.error(f"Error creating alert for {manifest.time}: {e}")
            raise BusinessLogicException(f"Failed to create alert: {e}")
    
    def get_prioritized_alerts(self, manifests: List[Manifest],
                              current_time: Optional[datetime] = None) -> List[Alert]:
        """Get all current alerts ordered by priority.
        
        Args:
            manifests: List of manifests to check
            current_time: Current time for calculations (defaults to now)
            
        Returns:
            List of Alert objects ordered by priority (high to low)
        """
        if current_time is None:
            current_time = datetime.now()
        
        alerts = []
        
        try:
            for manifest in manifests:
                if self.should_trigger_alert(manifest, current_time):
                    # Create manifest-level alert
                    alert = self.create_alert(manifest, alert_type=AlertType.VISUAL)
                    alerts.append(alert)
                    
                    # Create carrier-specific alerts for unacknowledged carriers
                    for carrier in manifest.get_unacknowledged_carriers():
                        carrier_alert = self.create_alert(manifest, carrier, AlertType.CARRIER)
                        alerts.append(carrier_alert)
            
            # Sort by priority (high to low) then by time
            alerts.sort(key=lambda a: (a.priority.value, a.manifest.time if a.manifest else ""), reverse=True)
            
            self.logger.debug(f"Generated {len(alerts)} prioritized alerts")
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error generating prioritized alerts: {e}")
            return []
    
    def should_play_audio_alert(self, manifest: Manifest, 
                               current_time: Optional[datetime] = None) -> bool:
        """Determine if audio alert should be played for a manifest.
        
        Args:
            manifest: Manifest to check
            current_time: Current time for calculations (defaults to now)
            
        Returns:
            True if audio alert should be played
        """
        if current_time is None:
            current_time = datetime.now()
        
        try:
            # Basic alert trigger check
            if not self.should_trigger_alert(manifest, current_time):
                return False
            
            # Additional audio-specific checks could go here
            # (e.g., audio mute settings, time-based restrictions)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking audio alert for {manifest.time}: {e}")
            return False
    
    def _calculate_alert_priority(self, manifest: Manifest, 
                                 current_time: Optional[datetime] = None) -> AlertPriority:
        """Calculate alert priority based on manifest status and timing.
        
        Args:
            manifest: Manifest to analyze
            current_time: Current time for calculations (defaults to now)
            
        Returns:
            AlertPriority enum value
        """
        if current_time is None:
            current_time = datetime.now()
            
        status = manifest.get_status(current_time)
        
        if status == ManifestStatus.MISSED:
            return AlertPriority.HIGH
        elif status == ManifestStatus.ACTIVE:
            # Check how close we are to deadline
            manifest_datetime = manifest.get_manifest_datetime()
            deadline = manifest_datetime + timedelta(minutes=self.alert_window_minutes)
            time_until_deadline = deadline - current_time
            
            if time_until_deadline.total_seconds() < 300:  # Less than 5 minutes
                return AlertPriority.HIGH
            else:
                return AlertPriority.MEDIUM
        else:
            return AlertPriority.LOW
    
    def _generate_alert_message(self, manifest: Manifest, 
                               carrier: Optional[Carrier] = None) -> str:
        """Generate human-readable alert message.
        
        Args:
            manifest: Manifest for the alert
            carrier: Optional specific carrier
            
        Returns:
            Alert message string
        """
        status = manifest.get_status()
        
        if carrier:
            if status == ManifestStatus.MISSED:
                return f"MISSED: {manifest.time} - {carrier.name}"
            else:
                return f"ALERT: {manifest.time} - {carrier.name}"
        else:
            unack_count = len(manifest.get_unacknowledged_carriers())
            if status == ManifestStatus.MISSED:
                return f"MISSED: {manifest.time} - {unack_count} carriers"
            else:
                return f"ALERT: {manifest.time} - {unack_count} carriers"
    
    def _generate_alert_title_message(self, manifest: Manifest, 
                                     carrier: Optional[Carrier] = None) -> tuple:
        """Generate alert title and message.
        
        Args:
            manifest: Manifest for the alert
            carrier: Optional specific carrier
            
        Returns:
            Tuple of (title, message)
        """
        status = manifest.get_status()
        
        if carrier:
            if status == ManifestStatus.MISSED:
                title = f"Missed Manifest - {manifest.time}"
                message = f"Carrier {carrier.name} missed manifest time"
            else:
                title = f"Manifest Alert - {manifest.time}"
                message = f"Carrier {carrier.name} requires acknowledgment"
        else:
            unack_count = len(manifest.get_unacknowledged_carriers())
            if status == ManifestStatus.MISSED:
                title = f"Missed Manifest - {manifest.time}"
                message = f"Manifest missed with {unack_count} unacknowledged carriers"
            else:
                title = f"Manifest Alert - {manifest.time}"
                message = f"Manifest active with {unack_count} unacknowledged carriers"
        
        return title, message
    
    def _is_globally_muted(self) -> bool:
        """Check if the system is globally muted.
        
        Returns:
            True if system is muted
        """
        try:
            mute_status = self.mute_repository.get_current_status()
            return mute_status.is_muted if mute_status else False
        except Exception as e:
            self.logger.warning(f"Error checking global mute status: {e}")
            return False
    
    def _is_manifest_muted(self, manifest: Manifest) -> bool:
        """Check if a specific manifest is muted.
        
        Args:
            manifest: Manifest to check
            
        Returns:
            True if manifest is muted
        """
        try:
            # This could be extended to support per-manifest muting
            # For now, just use global mute status
            return self._is_globally_muted()
        except Exception as e:
            self.logger.warning(f"Error checking manifest mute status: {e}")
            return False
