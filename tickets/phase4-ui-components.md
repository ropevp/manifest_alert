# Phase 4: UI Components & Presentation Layer

## Priority: HIGH
## Estimated Time: 4-5 hours
## Dependencies: Phase 1-3 (Domain Models, Repositories, Business Logic)

## Objective
Create the PyQt6 UI components that provide the visual interface for the manifest alert system. This phase implements the dynamic layout switching for single alert scaling and modernizes the UI architecture.

## Background
The current system has UI code mixed with business logic in a single monolithic class. We need to extract this into separate, testable UI components while preserving the exact look, feel, and behavior that users expect.

## Acceptance Criteria

### ✅ Core UI Components
- [ ] `StatusCard` component for individual manifest displays
- [ ] `ControlPanel` for mute button and system controls
- [ ] `CountdownDisplay` for mute countdown timers
- [ ] `LayoutManager` for dynamic layout switching
- [ ] `ConfigDialog` for settings and preferences

### ✅ Single Alert Scaling UI
- [ ] Dynamic scaling between grid and single alert modes
- [ ] Smooth transitions without UI flicker
- [ ] Maximized single alert with larger fonts and spacing
- [ ] Automatic layout detection and switching
- [ ] Preserve all styling and visual elements

### ✅ Layout Management
- [ ] Grid layout for multiple alerts
- [ ] Single maximized layout for single alert scaling
- [ ] Responsive layout switching based on business logic
- [ ] Multi-monitor support preservation
- [ ] Fullscreen mode compatibility

### ✅ Visual Design Standards
- [ ] Match current system's exact appearance
- [ ] Consistent color scheme and typography
- [ ] Proper spacing and alignment
- [ ] Visual feedback for user interactions
- [ ] Audio/visual alert synchronization

## Implementation Details

### File Structure to Create
```
src/
├── presentation/
│   ├── __init__.py
│   ├── components/
│   │   ├── __init__.py
│   │   ├── status_card.py
│   │   ├── control_panel.py
│   │   ├── countdown_display.py
│   │   ├── layout_manager.py
│   │   └── audio_visual_manager.py
│   ├── windows/
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   └── config_dialog.py
│   └── styles/
│       ├── __init__.py
│       ├── theme_manager.py
│       └── style_constants.py
└── tests/
    └── unit/
        ├── test_status_card.py
        ├── test_layout_manager.py
        └── test_ui_components.py
```

### Key Implementation Requirements

#### 1. StatusCard with Dynamic Scaling
```python
class StatusCard(QWidget):
    def __init__(self, manifest: Manifest, alert_service: AlertService):
        super().__init__()
        self.manifest = manifest
        self.alert_service = alert_service
        self.is_maximized = False
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Initialize UI components"""
        self.layout = QVBoxLayout()
        
        # Title (manifest name)
        self.title_label = QLabel(self.manifest.name)
        
        # Time display
        self.time_label = QLabel(self.manifest.time.strftime("%H:%M"))
        
        # Carriers list
        self.carriers_layout = QVBoxLayout()
        self.update_carriers_display()
        
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.time_label)
        self.layout.addLayout(self.carriers_layout)
        self.setLayout(self.layout)
    
    def set_maximized_mode(self, maximized: bool) -> None:
        """CRITICAL: Dynamic layout switching for single alert scaling"""
        if self.is_maximized == maximized:
            return
            
        self.is_maximized = maximized
        
        if maximized:
            self.apply_maximized_styling()
        else:
            self.apply_normal_styling()
    
    def apply_maximized_styling(self) -> None:
        """Apply styling for single alert maximized mode"""
        # Larger fonts for maximized mode
        self.title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: white;")
        self.time_label.setStyleSheet("font-size: 24px; color: #cccccc;")
        
        # Update carrier display for maximized mode
        for i in range(self.carriers_layout.count()):
            carrier_label = self.carriers_layout.itemAt(i).widget()
            if carrier_label:
                carrier_label.setStyleSheet("font-size: 22px; color: white; margin: 5px;")
    
    def apply_normal_styling(self) -> None:
        """Apply styling for normal grid mode"""
        # Normal fonts for grid mode
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        self.time_label.setStyleSheet("font-size: 14px; color: #cccccc;")
        
        # Update carrier display for normal mode
        for i in range(self.carriers_layout.count()):
            carrier_label = self.carriers_layout.itemAt(i).widget()
            if carrier_label:
                carrier_label.setStyleSheet("font-size: 14px; color: white; margin: 2px;")
```

#### 2. LayoutManager for Dynamic Switching
```python
class LayoutManager(QWidget):
    def __init__(self, layout_service: LayoutService):
        super().__init__()
        self.layout_service = layout_service
        self.status_cards = []
        self.current_mode = LayoutMode.GRID
        self.setup_layouts()
    
    def setup_layouts(self) -> None:
        """Initialize both grid and single layouts"""
        # Main container
        self.main_layout = QStackedLayout()
        
        # Grid layout for multiple alerts
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        
        # Single layout for maximized single alert
        self.single_widget = QWidget()
        self.single_layout = QVBoxLayout(self.single_widget)
        
        self.main_layout.addWidget(self.grid_widget)
        self.main_layout.addWidget(self.single_widget)
        self.setLayout(self.main_layout)
    
    def update_layout(self, alerts: List[Alert], layout_mode: LayoutMode) -> None:
        """Update layout based on current alerts and mode"""
        if layout_mode == self.current_mode and len(alerts) == len(self.status_cards):
            return  # No change needed
        
        self.clear_current_layout()
        self.create_status_cards(alerts)
        
        if layout_mode == LayoutMode.SINGLE_MAXIMIZED:
            self.apply_single_layout()
        else:
            self.apply_grid_layout()
        
        self.current_mode = layout_mode
    
    def apply_single_layout(self) -> None:
        """Apply single maximized layout"""
        if len(self.status_cards) == 1:
            card = self.status_cards[0]
            card.set_maximized_mode(True)
            self.single_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
            self.main_layout.setCurrentWidget(self.single_widget)
    
    def apply_grid_layout(self) -> None:
        """Apply grid layout for multiple alerts"""
        cols = 2  # 2 columns for grid
        for i, card in enumerate(self.status_cards):
            card.set_maximized_mode(False)
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(card, row, col)
        
        self.main_layout.setCurrentWidget(self.grid_widget)
```

#### 3. Control Panel with Mute Button
```python
class ControlPanel(QWidget):
    def __init__(self, mute_service: MuteService):
        super().__init__()
        self.mute_service = mute_service
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Initialize control panel UI"""
        layout = QHBoxLayout()
        
        # Mute button with instant feedback
        self.mute_button = QPushButton()
        self.mute_button.setFixedSize(80, 40)
        self.mute_button.clicked.connect(self.toggle_mute)
        
        # Countdown display
        self.countdown_display = CountdownDisplay()
        
        layout.addWidget(self.mute_button)
        layout.addWidget(self.countdown_display)
        self.setLayout(layout)
        
        # Update initial state
        self.update_mute_state()
    
    def toggle_mute(self) -> None:
        """Toggle mute with instant UI feedback"""
        # Provide immediate visual feedback
        self.mute_button.setEnabled(False)
        
        # Perform mute toggle in background thread
        def toggle_operation():
            success = self.mute_service.toggle_mute()
            QTimer.singleShot(0, lambda: self.on_mute_toggle_complete(success))
        
        threading.Thread(target=toggle_operation, daemon=True).start()
    
    def on_mute_toggle_complete(self, success: bool) -> None:
        """Handle mute toggle completion"""
        self.mute_button.setEnabled(True)
        if success:
            self.update_mute_state()
        else:
            # Show error feedback
            self.show_error_feedback()
```

## Visual Design Specifications

### Typography Scale
- **Single Alert Title**: 28px, Bold, White
- **Single Alert Time**: 24px, Regular, #cccccc
- **Single Alert Carriers**: 22px, Regular, White
- **Grid Alert Title**: 16px, Bold, White
- **Grid Alert Time**: 14px, Regular, #cccccc
- **Grid Alert Carriers**: 14px, Regular, White

### Color Scheme (Preserve Current)
- **Background**: Dark theme as per current system
- **Alert Cards**: Current card background colors
- **Text**: White primary, #cccccc secondary
- **Buttons**: Current button styling
- **Borders**: Current border colors and styles

### Layout Specifications
- **Grid Mode**: 2-column layout, cards evenly spaced
- **Single Mode**: Centered, maximum 80% of screen width
- **Spacing**: 10px margins in grid, 20px in single mode
- **Transitions**: 200ms fade animation between modes

## Testing Requirements

### UI Component Tests
- [ ] StatusCard rendering in both normal and maximized modes
- [ ] Layout switching between grid and single modes
- [ ] Control panel button responsiveness
- [ ] Visual styling matches current system exactly
- [ ] Multi-monitor behavior preservation

### Integration Tests
- [ ] End-to-end layout switching triggered by business logic
- [ ] UI updates in response to service layer events
- [ ] Performance under rapid layout switching
- [ ] Memory usage during extended operation

### Visual Regression Tests
- [ ] Screenshot comparison with current system
- [ ] Font sizes and colors match exactly
- [ ] Layout proportions preserved
- [ ] Button states and feedback correct

## Performance Requirements
- **Layout switching**: <100ms for transition completion
- **Button response**: <50ms for visual feedback
- **Memory usage**: <50MB for all UI components
- **CPU usage**: <5% during normal operation

## Success Criteria
- [ ] All UI components implemented and tested
- [ ] Single alert scaling visual behavior matches requirements
- [ ] Dynamic layout switching working smoothly
- [ ] Exact visual match with current system
- [ ] Performance requirements met
- [ ] UI tests pass with >85% coverage

## Risk Mitigation
- **Visual Risk**: Continuous comparison with current system
- **Performance Risk**: Profile layout switching performance
- **Usability Risk**: Test with actual users for feedback
- **Compatibility Risk**: Test on multiple screen resolutions

## Reference Files
- Current UI implementation: `alert_display.py` (UI-related methods)
- Visual styling: Current system for exact color/font matching
- Architecture spec: `OOP_REWRITE_SPECIFICATION.md` (Presentation Layer)

## Definition of Done
- All UI components implemented and styled correctly
- Single alert scaling visual behavior working
- Layout switching smooth and responsive
- Visual match with current system confirmed
- Performance benchmarks met
- Ready for Phase 5 integration
