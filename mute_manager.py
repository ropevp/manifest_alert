"""
Centralized Mute Status Manager
Handles mute state across multiple PCs via shared network file
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

class MuteManager:
    def __init__(self, settings_manager=None):
        """Initialize mute manager with settings"""
        self.settings_manager = settings_manager
        self._mute_file_path = None
        
    def get_mute_file_path(self) -> str:
        """Get the path to mute_status.json using settings manager"""
        if self._mute_file_path:
            return self._mute_file_path
            
        try:
            if self.settings_manager:
                data_folder = self.settings_manager.get_data_folder()
                if data_folder and os.path.exists(data_folder):
                    self._mute_file_path = os.path.join(data_folder, 'mute_status.json')
                    return self._mute_file_path
        except Exception:
            pass
            
        # Fallback to network location (same as ack.json)
        network_path = r'\\Prddpkmitlgt004\ManifestPC\mute_status.json'
        if os.path.exists(os.path.dirname(network_path)):
            self._mute_file_path = network_path
            return self._mute_file_path
            
        # Local fallback
        self._mute_file_path = os.path.join(os.path.dirname(__file__), 'app_data', 'mute_status.json')
        return self._mute_file_path
    
    def get_mute_status(self) -> Dict:
        """
        Get current mute status from file
        Returns dict with: is_muted, muted_at, muted_by, unmute_at, last_updated
        """
        try:
            mute_file = self.get_mute_file_path()
            
            if not os.path.exists(mute_file):
                return self._create_default_status()
                
            with open(mute_file, 'r', encoding='utf-8') as f:
                status = json.load(f)
                
            # Check if mute period has expired
            if status.get('is_muted') and status.get('unmute_at'):
                unmute_time = datetime.fromisoformat(status['unmute_at'])
                if datetime.now() >= unmute_time:
                    # Auto-unmute
                    status = self._auto_unmute(status)
                    
            return status
            
        except Exception as e:
            print(f"Error reading mute status: {e}")
            return self._create_default_status()
    
    def set_mute_status(self, is_muted: bool, user: str, duration_minutes: Optional[int] = None) -> bool:
        """
        Set mute status in shared file
        Args:
            is_muted: True to mute, False to unmute
            user: Username who is changing the status
            duration_minutes: Optional auto-unmute duration (None for indefinite)
        Returns:
            True if successfully saved, False otherwise
        """
        try:
            current_time = datetime.now()
            
            status = {
                "is_muted": is_muted,
                "muted_at": current_time.isoformat() if is_muted else None,
                "muted_by": user if is_muted else None,
                "unmute_at": None,
                "last_updated": current_time.isoformat()
            }
            
            if is_muted and duration_minutes:
                unmute_time = current_time + timedelta(minutes=duration_minutes)
                status["unmute_at"] = unmute_time.isoformat()
            
            return self._save_status(status)
            
        except Exception as e:
            print(f"Error setting mute status: {e}")
            return False
    
    def is_currently_muted(self) -> Tuple[bool, Optional[str]]:
        """
        Check if system is currently muted
        Returns:
            (is_muted, muted_by_user)
        """
        status = self.get_mute_status()
        return status.get('is_muted', False), status.get('muted_by')
    
    def get_mute_time_remaining(self) -> Optional[int]:
        """
        Get minutes remaining in mute period
        Returns:
            Minutes remaining (int) or None if indefinite/not muted
        """
        status = self.get_mute_status()
        
        if not status.get('is_muted') or not status.get('unmute_at'):
            return None
            
        try:
            unmute_time = datetime.fromisoformat(status['unmute_at'])
            remaining = unmute_time - datetime.now()
            
            if remaining.total_seconds() <= 0:
                return 0
                
            return max(1, int(remaining.total_seconds() / 60))
            
        except Exception:
            return None
    
    def toggle_mute(self, user: str, duration_minutes: Optional[int] = None) -> Tuple[bool, str]:
        """
        Toggle mute status
        Returns:
            (new_mute_state, status_message)
        """
        current_muted, _ = self.is_currently_muted()
        new_state = not current_muted
        
        if self.set_mute_status(new_state, user, duration_minutes):
            if new_state:
                if duration_minutes:
                    message = f"Muted for {duration_minutes} minutes by {user}"
                else:
                    message = f"Muted indefinitely by {user}"
            else:
                message = f"Unmuted by {user}"
            return new_state, message
        else:
            return current_muted, "Error updating mute status"
    
    def _create_default_status(self) -> Dict:
        """Create default unmuted status"""
        return {
            "is_muted": False,
            "muted_at": None,
            "muted_by": None,
            "unmute_at": None,
            "last_updated": datetime.now().isoformat()
        }
    
    def _auto_unmute(self, status: Dict) -> Dict:
        """Auto-unmute when time expires"""
        status["is_muted"] = False
        status["muted_at"] = None
        status["muted_by"] = None
        status["unmute_at"] = None
        status["last_updated"] = datetime.now().isoformat()
        
        # Save the auto-unmute
        self._save_status(status)
        return status
    
    def _save_status(self, status: Dict) -> bool:
        """Save status to file"""
        try:
            mute_file = self.get_mute_file_path()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(mute_file), exist_ok=True)
            
            with open(mute_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2)
                
            return True
            
        except Exception as e:
            print(f"Error saving mute status: {e}")
            return False

# Global instance for easy access
_mute_manager = None

def get_mute_manager(settings_manager=None) -> MuteManager:
    """Get global mute manager instance"""
    global _mute_manager
    if _mute_manager is None:
        _mute_manager = MuteManager(settings_manager)
    return _mute_manager

def is_muted() -> bool:
    """Quick check if system is muted"""
    manager = get_mute_manager()
    muted, _ = manager.is_currently_muted()
    return muted

def toggle_mute(user: str, duration_minutes: Optional[int] = None) -> Tuple[bool, str]:
    """Quick toggle mute function"""
    manager = get_mute_manager()
    return manager.toggle_mute(user, duration_minutes)

if __name__ == "__main__":
    # Test the mute manager
    manager = MuteManager()
    
    print("Testing Mute Manager...")
    
    # Test get status
    status = manager.get_mute_status()
    print(f"Current status: {status}")
    
    # Test mute
    success = manager.set_mute_status(True, "TestUser", 5)
    print(f"Mute test: {success}")
    
    # Test status check
    is_muted, muted_by = manager.is_currently_muted()
    print(f"Is muted: {is_muted} by {muted_by}")
    
    # Test time remaining
    remaining = manager.get_mute_time_remaining()
    print(f"Time remaining: {remaining} minutes")
    
    # Test unmute
    success = manager.set_mute_status(False, "TestUser")
    print(f"Unmute test: {success}")
