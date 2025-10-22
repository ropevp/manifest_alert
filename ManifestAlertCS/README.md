# Manifest Alert System - C# WPF Edition

A professional warehouse manifest alert application with real-time notifications, voice announcements, and beautiful Material Design UI.

## ✨ Features

### Core Functionality
- **Real-time Manifest Tracking**: Monitor scheduled carrier pickups throughout the day
- **Visual & Audio Alerts**: Color-coded status indicators with text-to-speech announcements
- **Multi-PC Synchronization**: Share acknowledgment data across multiple workstations via network folders
- **Smart Status Management**: Automatic status updates (Pending → Active → Missed → Acknowledged)

### Enhanced Mute System (NEW!)
- **3-Press Quick Mute**:
  - 1st press = 5 minutes
  - 2nd press (within 3 seconds) = 10 minutes
  - 3rd press (within 3 seconds) = 15 minutes
- **Live Countdown Timer**: See exactly when alerts will resume
- **Visual Mute Overlay**: Clear indication when system is muted

### Interactive Manifest Management
- **Click-to-Acknowledge**: Toggle carrier acknowledgment status with single click
- **Customer Messages**: Add notes/messages to specific carriers
- **Undo Functionality**: Revert acknowledgments back to pending state
- **Bulk Actions**: Acknowledge all carriers in a manifest at once

### Beautiful UI
- **Material Design**: Modern, professional dark theme optimized for warehouse displays
- **Color-Coded Status**:
  - 🔵 Blue = Pending
  - 🟠 Orange = Active
  - 🔴 Red = Missed
  - 🟢 Green = Acknowledged
- **Responsive Layout**: Automatically adjusts to screen size
- **Large, Clear Fonts**: Optimized for visibility from a distance

## 📋 Requirements

### Development
- .NET 8.0 SDK or later
- Visual Studio 2022 (recommended) or VS Code with C# extension
- Windows 10/11 (for WPF support)

### Runtime
- .NET 8.0 Runtime (Desktop)
- Windows 10 version 1809 or later

## 🚀 Getting Started

### Build from Source

```bash
# Clone or navigate to the directory
cd ManifestAlertCS

# Restore dependencies
dotnet restore

# Build the solution
dotnet build --configuration Release

# Run the application
dotnet run --project ManifestAlert.WPF
```

### Build with Visual Studio
1. Open `ManifestAlert.sln` in Visual Studio 2022
2. Right-click solution → Restore NuGet Packages
3. Build → Build Solution (or press F6)
4. Debug → Start Without Debugging (or press Ctrl+F5)

### Publish for Deployment

```bash
# Create self-contained executable
dotnet publish ManifestAlert.WPF/ManifestAlert.WPF.csproj \
  --configuration Release \
  --runtime win-x64 \
  --self-contained true \
  -p:PublishSingleFile=true \
  --output ./publish

# The executable will be in ./publish/ManifestAlert.WPF.exe
```

## ⚙️ Configuration

### Manifest Configuration
Edit `%APPDATA%\ManifestAlert\config.json` to configure manifest times and carriers:

```json
{
  "manifests": [
    {
      "time": "07:00",
      "carriers": [
        "Australia Post Metro",
        "EParcel Express",
        "EParcel Postplus"
      ]
    },
    {
      "time": "11:00",
      "carriers": [
        "AUP International for NZ",
        "Australia Post Metro"
      ]
    }
  ]
}
```

### Data Files Location
All data is stored in: `%APPDATA%\ManifestAlert\`
- `config.json` - Manifest schedule configuration
- `ack.json` - Acknowledgment history
- `mute.json` - Current mute status

### Network Synchronization
To enable multi-PC sync:
1. Share the data folder on a network drive
2. Point each PC to the shared location (update `App.xaml.cs` dataFolder path)
3. All acknowledgments and mute status will sync automatically

## 🎮 Usage Guide

### Mute System
1. **Quick Mute**: Press MUTE button once for 5 minutes
2. **Extend**: Press again within 3 seconds for 10 minutes
3. **Maximum**: Press a third time for 15 minutes
4. **Unmute**: Click UNMUTE button to resume alerts immediately
5. **Auto-Resume**: System automatically unmutes when countdown reaches zero

### Acknowledge Carriers
1. **Single Carrier**: Click the checkbox next to carrier name
2. **Add Message**: Click the message icon to add customer notes
3. **Undo**: Click checkbox again to revert to pending
4. **Acknowledge All**: Click "ACKNOWLEDGE ALL" button at bottom of card

### Status Indicators
- **Pending** (Blue): Manifest time hasn't arrived yet
- **Active** (Orange): Within alert window (2 min before to 30 min after)
- **Missed** (Red): Past alert window and not acknowledged
- **Acknowledged** (Green): All carriers marked as complete

## 🏗️ Architecture

```
ManifestAlert.Domain/          # Domain models and business entities
├── Models/
│   ├── Manifest.cs           # Manifest with carriers
│   ├── Carrier.cs            # Individual carrier
│   ├── Acknowledgment.cs     # Acknowledgment record
│   └── MuteStatus.cs         # Enhanced mute with 3-press system

ManifestAlert.Application/     # Business logic services
├── Interfaces/
│   ├── IManifestRepository
│   └── IMuteRepository
└── Services/
    ├── AlertService.cs       # Alert triggering logic
    ├── ManifestService.cs    # Manifest operations
    └── MuteService.cs        # Mute/snooze management

ManifestAlert.Infrastructure/  # Data access and external services
├── Repositories/
│   ├── JsonManifestRepository.cs  # JSON-based persistence
│   └── JsonMuteRepository.cs      # Mute status storage
└── Services/
    └── VoiceService.cs            # Text-to-speech

ManifestAlert.WPF/            # User interface
├── ViewModels/
│   ├── MainViewModel.cs         # Main application logic
│   └── ManifestCardViewModel.cs # Manifest card logic
├── MainWindow.xaml              # Beautiful Material Design UI
└── App.xaml                     # DI configuration
```

### Design Patterns Used
- **MVVM (Model-View-ViewModel)**: Clean separation of UI and logic
- **Dependency Injection**: Testable, maintainable code
- **Repository Pattern**: Abstract data access
- **Domain-Driven Design**: Rich domain models with business logic

## 📦 Dependencies

- **MaterialDesignThemes** 5.0.0 - Beautiful Material Design UI components
- **Hardcodet.NotifyIcon.Wpf** 1.1.0 - System tray integration
- **Newtonsoft.Json** 13.0.3 - JSON serialization
- **Microsoft.Extensions.DependencyInjection** 8.0.0 - DI container
- **Microsoft.Extensions.Logging** 8.0.0 - Logging framework

## 🔧 Troubleshooting

### Voice Announcements Not Working
- Ensure Windows Speech Synthesis is enabled
- Check audio output device is working
- Verify volume is not muted in system settings

### Manifests Not Showing
- Check `config.json` exists in `%APPDATA%\ManifestAlert\`
- Verify JSON format is valid
- Check application logs for errors

### Network Sync Issues
- Ensure all PCs have read/write access to shared folder
- Check network connectivity
- Verify folder permissions

## 🤝 Contributing

This is a port of the Python/PyQt6 version with enhanced features. Key improvements:
- **Enhanced Mute System**: 3-press functionality with countdown timer
- **Click-to-Edit**: Interactive manifest editing
- **Material Design UI**: Professional, modern interface
- **Better Architecture**: Clean MVVM with dependency injection

## 📝 License

This project is provided as-is for warehouse management and logistics operations.

## 🙏 Acknowledgments

- Original Python version developed for warehouse operations
- Material Design components by MaterialDesignInXaml
- Windows Speech API for voice announcements

---

**Built with ❤️ for warehouse efficiency**
