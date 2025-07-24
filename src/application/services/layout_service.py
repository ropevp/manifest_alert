"""
Layout Service - Business logic for UI layout calculations.

Handles dynamic layout mode calculations, single alert scaling decisions,
and UI optimization based on current alert states.
"""

from typing import List, Optional, Dict, Tuple
from datetime import datetime
from enum import Enum
import logging

from ...domain.models.manifest import Manifest, ManifestStatus
from ...domain.models.carrier import Carrier
from .alert_service import AlertService, LayoutMode
from .mute_service import MuteService
from ...infrastructure.exceptions import BusinessLogicException


class CardSize(Enum):
    """Enumeration of card size modes."""
    NORMAL = "normal"           # Standard card size
    MAXIMIZED = "maximized"     # Single card expanded mode
    COMPACT = "compact"         # Smaller card for many alerts


class LayoutConfiguration:
    """Configuration for layout calculations."""
    
    def __init__(self):
        # Single card mode thresholds
        self.single_card_enabled = True
        self.max_manifests_for_single_card = 1
        self.max_missed_for_single_card = 0
        
        # Card sizing
        self.normal_card_height = 80
        self.maximized_card_height = 200
        self.compact_card_height = 60
        
        # Grid layout
        self.max_cards_per_column = 10
        self.card_spacing = 5
        self.container_padding = 10


class LayoutService:
    """Service for calculating optimal UI layouts.
    
    This service implements the single alert scaling feature and other
    dynamic layout optimizations based on current system state.
    """
    
    def __init__(self,
                 alert_service: AlertService,
                 mute_service: MuteService,
                 layout_config: Optional[LayoutConfiguration] = None,
                 logger: Optional[logging.Logger] = None):
        """Initialize the layout service.
        
        Args:
            alert_service: Service for alert logic
            mute_service: Service for mute status
            layout_config: Optional layout configuration
            logger: Optional logger instance
        """
        self.alert_service = alert_service
        self.mute_service = mute_service
        self.config = layout_config or LayoutConfiguration()
        self.logger = logger or logging.getLogger(__name__)
        
        self.logger.info("LayoutService initialized")
    
    def calculate_layout(self, manifests: List[Manifest], 
                        current_time: Optional[datetime] = None) -> Dict:
        """Calculate the optimal layout for the given manifests.
        
        Args:
            manifests: List of manifests to layout
            current_time: Current time for calculations (defaults to now)
            
        Returns:
            Dictionary containing layout information
        """
        if current_time is None:
            current_time = datetime.now()
        
        try:
            # Get alert summary
            alert_summary = self.alert_service.get_alert_summary(manifests, current_time)
            
            # Determine layout mode
            layout_mode = self._determine_layout_mode(alert_summary, manifests, current_time)
            
            # Calculate card configurations
            card_configs = self._calculate_card_configurations(manifests, layout_mode, current_time)
            
            # Calculate grid layout
            grid_layout = self._calculate_grid_layout(card_configs)
            
            layout_info = {
                'mode': layout_mode,
                'total_manifests': len(manifests),
                'visible_manifests': len([c for c in card_configs if c['visible']]),
                'card_configurations': card_configs,
                'grid_layout': grid_layout,
                'alert_summary': alert_summary,
                'single_card_active': layout_mode == LayoutMode.SINGLE_CARD,
                'maximized_manifest': self._get_maximized_manifest(card_configs)
            }
            
            self.logger.debug(f"Calculated layout: mode={layout_mode.value}, "
                            f"visible={layout_info['visible_manifests']}/{len(manifests)}")
            
            return layout_info
            
        except Exception as e:
            self.logger.error(f"Error calculating layout: {e}")
            # Return safe default layout
            return self._get_default_layout(manifests)
    
    def should_use_single_card_mode(self, manifests: List[Manifest],
                                  current_time: Optional[datetime] = None) -> bool:
        """Determine if single card mode should be used.
        
        This implements the core single alert scaling logic:
        - Exactly one manifest has active alerts
        - No manifests have missed alerts
        - System is not muted
        
        Args:
            manifests: List of manifests to check
            current_time: Current time for calculations (defaults to now)
            
        Returns:
            True if single card mode should be used
        """
        if not self.config.single_card_enabled:
            return False
        
        if current_time is None:
            current_time = datetime.now()
        
        try:
            # Check if system is muted
            if self.mute_service.is_muted():
                return False
            
            # Get manifests with alerts
            active_manifests = []
            missed_manifests = []
            
            for manifest in manifests:
                status = manifest.get_status(current_time)
                
                if status == ManifestStatus.ACTIVE and not manifest.acknowledged:
                    active_manifests.append(manifest)
                elif status == ManifestStatus.MISSED and not manifest.acknowledged:
                    missed_manifests.append(manifest)
            
            # Single card mode conditions
            active_count = len(active_manifests)
            missed_count = len(missed_manifests)
            
            return (active_count == self.config.max_manifests_for_single_card and
                   missed_count <= self.config.max_missed_for_single_card)
            
        except Exception as e:
            self.logger.error(f"Error checking single card mode: {e}")
            return False
    
    def get_maximized_manifest(self, manifests: List[Manifest],
                             current_time: Optional[datetime] = None) -> Optional[Manifest]:
        """Get the manifest that should be maximized (if any).
        
        Args:
            manifests: List of manifests to check
            current_time: Current time for calculations (defaults to now)
            
        Returns:
            Manifest to maximize, or None if no manifest should be maximized
        """
        if not self.should_use_single_card_mode(manifests, current_time):
            return None
        
        try:
            # Find the single active manifest
            for manifest in manifests:
                status = manifest.get_status(current_time or datetime.now())
                if status == ManifestStatus.ACTIVE and not manifest.acknowledged:
                    return manifest
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting maximized manifest: {e}")
            return None
    
    def calculate_card_size(self, manifest: Manifest, layout_mode: LayoutMode,
                          is_maximized: bool = False) -> CardSize:
        """Calculate the appropriate size for a manifest card.
        
        Args:
            manifest: Manifest to calculate size for
            layout_mode: Current layout mode
            is_maximized: Whether this card is maximized
            
        Returns:
            CardSize enum value
        """
        try:
            if is_maximized and layout_mode == LayoutMode.SINGLE_CARD:
                return CardSize.MAXIMIZED
            
            # Could add logic for compact mode when many cards
            return CardSize.NORMAL
            
        except Exception as e:
            self.logger.error(f"Error calculating card size: {e}")
            return CardSize.NORMAL
    
    def get_card_dimensions(self, card_size: CardSize) -> Tuple[int, int]:
        """Get pixel dimensions for a card size.
        
        Args:
            card_size: Card size to get dimensions for
            
        Returns:
            Tuple of (width, height) in pixels
        """
        heights = {
            CardSize.NORMAL: self.config.normal_card_height,
            CardSize.MAXIMIZED: self.config.maximized_card_height,
            CardSize.COMPACT: self.config.compact_card_height
        }
        
        # Width is typically fixed or calculated based on container
        width = 1200  # Default card width
        height = heights.get(card_size, self.config.normal_card_height)
        
        return width, height
    
    def _determine_layout_mode(self, alert_summary: Dict, manifests: List[Manifest],
                             current_time: datetime) -> LayoutMode:
        """Determine the appropriate layout mode.
        
        Args:
            alert_summary: Alert summary from AlertService
            manifests: List of manifests
            current_time: Current time
            
        Returns:
            LayoutMode enum value
        """
        try:
            # Check if no alerts
            if alert_summary['total_alerts'] == 0:
                return LayoutMode.NO_ALERTS
            
            # Check for single card mode
            if self.should_use_single_card_mode(manifests, current_time):
                return LayoutMode.SINGLE_CARD
            
            # Default to normal mode
            return LayoutMode.NORMAL
            
        except Exception as e:
            self.logger.error(f"Error determining layout mode: {e}")
            return LayoutMode.NORMAL
    
    def _calculate_card_configurations(self, manifests: List[Manifest], 
                                     layout_mode: LayoutMode,
                                     current_time: datetime) -> List[Dict]:
        """Calculate configuration for each manifest card.
        
        Args:
            manifests: List of manifests
            layout_mode: Current layout mode
            current_time: Current time
            
        Returns:
            List of card configuration dictionaries
        """
        card_configs = []
        maximized_manifest = None
        
        if layout_mode == LayoutMode.SINGLE_CARD:
            maximized_manifest = self.get_maximized_manifest(manifests, current_time)
        
        for manifest in manifests:
            status = manifest.get_status(current_time)
            is_maximized = (manifest == maximized_manifest)
            
            # Determine if card should be visible
            visible = True
            if layout_mode == LayoutMode.NO_ALERTS:
                # In no alerts mode, might hide certain cards
                visible = status != ManifestStatus.PENDING
            
            card_size = self.calculate_card_size(manifest, layout_mode, is_maximized)
            width, height = self.get_card_dimensions(card_size)
            
            config = {
                'manifest': manifest,
                'visible': visible,
                'maximized': is_maximized,
                'card_size': card_size,
                'width': width,
                'height': height,
                'status': status,
                'priority': self._calculate_card_priority(manifest, status),
                'alert_count': len(manifest.get_unacknowledged_carriers()),
                'should_flash': self.alert_service.should_trigger_alert(manifest, current_time)
            }
            
            card_configs.append(config)
        
        # Sort by priority (high priority first)
        card_configs.sort(key=lambda c: c['priority'], reverse=True)
        
        return card_configs
    
    def _calculate_grid_layout(self, card_configs: List[Dict]) -> Dict:
        """Calculate grid layout for the cards.
        
        Args:
            card_configs: List of card configurations
            
        Returns:
            Dictionary containing grid layout information
        """
        visible_cards = [c for c in card_configs if c['visible']]
        
        if not visible_cards:
            return {
                'rows': 0,
                'columns': 1,
                'total_height': 0,
                'total_width': 0
            }
        
        # Simple single-column layout for now
        total_height = sum(c['height'] for c in visible_cards)
        total_height += (len(visible_cards) - 1) * self.config.card_spacing
        total_height += 2 * self.config.container_padding
        
        max_width = max(c['width'] for c in visible_cards)
        max_width += 2 * self.config.container_padding
        
        return {
            'rows': len(visible_cards),
            'columns': 1,
            'total_height': total_height,
            'total_width': max_width,
            'card_spacing': self.config.card_spacing,
            'container_padding': self.config.container_padding
        }
    
    def _calculate_card_priority(self, manifest: Manifest, status: ManifestStatus) -> int:
        """Calculate priority for card ordering.
        
        Args:
            manifest: Manifest to calculate priority for
            status: Current manifest status
            
        Returns:
            Priority value (higher = more important)
        """
        # Priority ordering: Missed > Active > Acknowledged > Pending
        if status == ManifestStatus.MISSED:
            return 1000
        elif status == ManifestStatus.ACTIVE:
            return 500
        elif status == ManifestStatus.ACKNOWLEDGED:
            return 100
        else:  # PENDING
            return 50
    
    def _get_maximized_manifest(self, card_configs: List[Dict]) -> Optional[str]:
        """Get the time of the maximized manifest.
        
        Args:
            card_configs: List of card configurations
            
        Returns:
            Manifest time if found, None otherwise
        """
        for config in card_configs:
            if config.get('maximized', False):
                return config['manifest'].time
        return None
    
    def _get_default_layout(self, manifests: List[Manifest]) -> Dict:
        """Get a safe default layout configuration.
        
        Args:
            manifests: List of manifests
            
        Returns:
            Default layout configuration
        """
        return {
            'mode': LayoutMode.NORMAL,
            'total_manifests': len(manifests),
            'visible_manifests': len(manifests),
            'card_configurations': [],
            'grid_layout': {
                'rows': len(manifests),
                'columns': 1,
                'total_height': len(manifests) * self.config.normal_card_height,
                'total_width': 1200
            },
            'alert_summary': {
                'total_alerts': 0,
                'active_alerts': 0,
                'missed_alerts': 0
            },
            'single_card_active': False,
            'maximized_manifest': None
        }
