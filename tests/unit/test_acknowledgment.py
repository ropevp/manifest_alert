"""
Unit tests for the Acknowledgment domain model.
"""

import pytest
from datetime import datetime
from src.domain.models.acknowledgment import Acknowledgment
from src.infrastructure.exceptions.custom_exceptions import DataValidationException


class TestAcknowledgment:
    """Test cases for the Acknowledgment model."""
    
    def test_create_acknowledgment_valid(self):
        """Test creating a valid acknowledgment."""
        user = "test_user"
        timestamp = datetime.now()
        reason = "Test reason"
        entity_type = "manifest"
        entity_id = "test_manifest"
        
        ack = Acknowledgment(
            user=user,
            timestamp=timestamp,
            reason=reason,
            entity_type=entity_type,
            entity_id=entity_id
        )
        
        assert ack.user == user
        assert ack.timestamp == timestamp
        assert ack.reason == reason
        assert ack.entity_type == entity_type
        assert ack.entity_id == entity_id
    
    def test_create_acknowledgment_minimal(self):
        """Test creating acknowledgment with minimal required fields."""
        user = "test_user"
        timestamp = datetime.now()
        
        ack = Acknowledgment(user=user, timestamp=timestamp)
        
        assert ack.user == user
        assert ack.timestamp == timestamp
        assert ack.reason == ""
        assert ack.entity_type == ""
        assert ack.entity_id == ""
    
    def test_create_acknowledgment_invalid_user(self):
        """Test creating acknowledgment with invalid user."""
        with pytest.raises(DataValidationException) as exc_info:
            Acknowledgment(user="", timestamp=datetime.now())
        
        assert "User must be a non-empty string" in str(exc_info.value)
        assert exc_info.value.field_name == "user"
    
    def test_create_acknowledgment_invalid_user_type(self):
        """Test creating acknowledgment with invalid user type."""
        with pytest.raises(DataValidationException) as exc_info:
            Acknowledgment(user=123, timestamp=datetime.now())
        
        assert "User must be a non-empty string" in str(exc_info.value)
        assert exc_info.value.field_name == "user"
    
    def test_create_acknowledgment_invalid_timestamp(self):
        """Test creating acknowledgment with invalid timestamp."""
        with pytest.raises(DataValidationException) as exc_info:
            Acknowledgment(user="test_user", timestamp="not_a_datetime")
        
        assert "Timestamp must be a datetime object" in str(exc_info.value)
        assert exc_info.value.field_name == "timestamp"
    
    def test_from_dict_valid(self):
        """Test creating acknowledgment from valid dictionary."""
        data = {
            'user': 'test_user',
            'timestamp': '2024-01-01T10:00:00',
            'reason': 'Test reason',
            'entity_type': 'manifest',
            'entity_id': 'test_manifest'
        }
        
        ack = Acknowledgment.from_dict(data)
        
        assert ack.user == 'test_user'
        assert ack.timestamp.year == 2024
        assert ack.timestamp.month == 1
        assert ack.timestamp.day == 1
        assert ack.timestamp.hour == 10
        assert ack.reason == 'Test reason'
        assert ack.entity_type == 'manifest'
        assert ack.entity_id == 'test_manifest'
    
    def test_from_dict_missing_user(self):
        """Test creating acknowledgment from dict missing required field."""
        data = {
            'timestamp': '2024-01-01T10:00:00'
        }
        
        with pytest.raises(DataValidationException) as exc_info:
            Acknowledgment.from_dict(data)
        
        assert "Missing required field" in str(exc_info.value)
    
    def test_to_dict(self):
        """Test converting acknowledgment to dictionary."""
        timestamp = datetime(2024, 1, 1, 10, 0, 0)
        ack = Acknowledgment(
            user='test_user',
            timestamp=timestamp,
            reason='Test reason',
            entity_type='manifest',
            entity_id='test_manifest'
        )
        
        data = ack.to_dict()
        
        expected = {
            'user': 'test_user',
            'timestamp': '2024-01-01T10:00:00',
            'reason': 'Test reason',
            'entity_type': 'manifest',
            'entity_id': 'test_manifest'
        }
        
        assert data == expected
    
    def test_get_formatted_timestamp(self):
        """Test getting formatted timestamp."""
        timestamp = datetime(2024, 1, 1, 10, 30, 45)
        ack = Acknowledgment(user='test_user', timestamp=timestamp)
        
        formatted = ack.get_formatted_timestamp("%Y-%m-%d %H:%M")
        
        assert formatted == "2024-01-01 10:30"
    
    def test_has_reason(self):
        """Test checking if acknowledgment has reason."""
        ack_with_reason = Acknowledgment(
            user='test_user',
            timestamp=datetime.now(),
            reason='Test reason'
        )
        
        ack_without_reason = Acknowledgment(
            user='test_user',
            timestamp=datetime.now()
        )
        
        ack_empty_reason = Acknowledgment(
            user='test_user',
            timestamp=datetime.now(),
            reason='   '
        )
        
        assert ack_with_reason.has_reason()
        assert not ack_without_reason.has_reason()
        assert not ack_empty_reason.has_reason()
    
    def test_get_display_reason(self):
        """Test getting display-friendly reason."""
        ack_with_reason = Acknowledgment(
            user='test_user',
            timestamp=datetime.now(),
            reason='Test reason'
        )
        
        ack_without_reason = Acknowledgment(
            user='test_user',
            timestamp=datetime.now()
        )
        
        assert ack_with_reason.get_display_reason() == 'Test reason'
        assert ack_without_reason.get_display_reason() == 'No reason provided'
    
    def test_get_summary(self):
        """Test getting acknowledgment summary."""
        timestamp = datetime(2024, 1, 1, 10, 30, 0)
        
        ack_with_reason = Acknowledgment(
            user='test_user',
            timestamp=timestamp,
            reason='Test reason'
        )
        
        ack_without_reason = Acknowledgment(
            user='test_user',
            timestamp=timestamp
        )
        
        summary_with_reason = ack_with_reason.get_summary()
        summary_without_reason = ack_without_reason.get_summary()
        
        assert 'test_user' in summary_with_reason
        assert '01/01 10:30' in summary_with_reason
        assert 'Test reason' in summary_with_reason
        
        assert 'test_user' in summary_without_reason
        assert '01/01 10:30' in summary_without_reason
        assert 'Test reason' not in summary_without_reason
    
    def test_matches_entity(self):
        """Test matching acknowledgment to entity."""
        ack = Acknowledgment(
            user='test_user',
            timestamp=datetime.now(),
            entity_type='manifest',
            entity_id='test_manifest'
        )
        
        assert ack.matches_entity('manifest', 'test_manifest')
        assert not ack.matches_entity('carrier', 'test_manifest')
        assert not ack.matches_entity('manifest', 'other_manifest')
    
    def test_equality(self):
        """Test acknowledgment equality comparison."""
        timestamp = datetime(2024, 1, 1, 10, 0, 0)
        
        ack1 = Acknowledgment(
            user='test_user',
            timestamp=timestamp,
            reason='Test reason',
            entity_type='manifest',
            entity_id='test_manifest'
        )
        
        ack2 = Acknowledgment(
            user='test_user',
            timestamp=timestamp,
            reason='Test reason',
            entity_type='manifest',
            entity_id='test_manifest'
        )
        
        ack3 = Acknowledgment(
            user='different_user',
            timestamp=timestamp,
            reason='Test reason',
            entity_type='manifest',
            entity_id='test_manifest'
        )
        
        assert ack1 == ack2
        assert ack1 != ack3
        assert ack1 != "not_an_acknowledgment"
    
    def test_hash(self):
        """Test acknowledgment hash."""
        timestamp = datetime(2024, 1, 1, 10, 0, 0)
        
        ack1 = Acknowledgment(
            user='test_user',
            timestamp=timestamp,
            entity_type='manifest',
            entity_id='test_manifest'
        )
        
        ack2 = Acknowledgment(
            user='test_user',
            timestamp=timestamp,
            entity_type='manifest',
            entity_id='test_manifest'
        )
        
        # Same acknowledgments should have same hash
        assert hash(ack1) == hash(ack2)
        
        # Should be usable in sets
        ack_set = {ack1, ack2}
        assert len(ack_set) == 1