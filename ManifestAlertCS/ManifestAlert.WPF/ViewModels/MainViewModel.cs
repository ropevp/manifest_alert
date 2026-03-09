using ManifestAlert.Application.Services;
using ManifestAlert.Domain.Models;
using ManifestAlert.Infrastructure.Services;
using Microsoft.Extensions.Logging;
using System.Collections.ObjectModel;
using System.Windows.Input;
using System.Windows.Threading;

namespace ManifestAlert.WPF.ViewModels;

/// <summary>
/// Main ViewModel for the application
/// </summary>
public class MainViewModel : ViewModelBase, IDisposable
{
    private readonly ManifestService _manifestService;
    private readonly AlertService _alertService;
    private readonly MuteService _muteService;
    private readonly VoiceService _voiceService;
    private readonly ILogger<MainViewModel> _logger;
    private readonly DispatcherTimer _refreshTimer;
    private readonly DispatcherTimer _countdownTimer;

    private bool _isMuted;
    private string _muteButtonText = "MUTE (5 MIN)";
    private string _muteStatusText = "Alerts Active";
    private string _countdownText = "";
    private bool _showCountdown;
    private int _activeAlertCount;
    private int _missedAlertCount;
    private bool _hasActiveAlerts;
    private bool _hasMissedAlerts;
    private bool _isRefreshing;
    private bool _disposed;

    private DateTime _lastAnnouncementTime = DateTime.MinValue;
    private readonly TimeSpan _announcementInterval = TimeSpan.FromMinutes(2);
    private readonly HashSet<string> _announcedAlertKeys = new();

    public MainViewModel(
        ManifestService manifestService,
        AlertService alertService,
        MuteService muteService,
        VoiceService voiceService,
        ILogger<MainViewModel> logger)
    {
        _manifestService = manifestService;
        _alertService = alertService;
        _muteService = muteService;
        _voiceService = voiceService;
        _logger = logger;

        Manifests = new ObservableCollection<ManifestCardViewModel>();

        // Commands
        MuteCommand = new RelayCommand(async () => await HandleMutePressAsync());
        UnmuteCommand = new RelayCommand(async () => await UnmuteAsync());
        RefreshCommand = new RelayCommand(async () => await RefreshAsync());

        // Setup refresh timer (every 1 second)
        _refreshTimer = new DispatcherTimer
        {
            Interval = TimeSpan.FromSeconds(1)
        };
        _refreshTimer.Tick += async (s, e) => await RefreshAsync();
        _refreshTimer.Start();

        // Setup countdown timer (every 500ms for smooth countdown)
        _countdownTimer = new DispatcherTimer
        {
            Interval = TimeSpan.FromMilliseconds(500)
        };
        _countdownTimer.Tick += async (s, e) => await UpdateCountdownAsync();
        _countdownTimer.Start();

        // Initial load
        _ = InitializeAsync();
    }

    public ObservableCollection<ManifestCardViewModel> Manifests { get; }

    public bool IsMuted
    {
        get => _isMuted;
        set => SetProperty(ref _isMuted, value);
    }

    public string MuteButtonText
    {
        get => _muteButtonText;
        set => SetProperty(ref _muteButtonText, value);
    }

    public string MuteStatusText
    {
        get => _muteStatusText;
        set => SetProperty(ref _muteStatusText, value);
    }

    public string CountdownText
    {
        get => _countdownText;
        set => SetProperty(ref _countdownText, value);
    }

    public bool ShowCountdown
    {
        get => _showCountdown;
        set => SetProperty(ref _showCountdown, value);
    }

    public int ActiveAlertCount
    {
        get => _activeAlertCount;
        set
        {
            if (SetProperty(ref _activeAlertCount, value))
                HasActiveAlerts = value > 0;
        }
    }

    public int MissedAlertCount
    {
        get => _missedAlertCount;
        set
        {
            if (SetProperty(ref _missedAlertCount, value))
                HasMissedAlerts = value > 0;
        }
    }

    public bool HasActiveAlerts
    {
        get => _hasActiveAlerts;
        set => SetProperty(ref _hasActiveAlerts, value);
    }

    public bool HasMissedAlerts
    {
        get => _hasMissedAlerts;
        set => SetProperty(ref _hasMissedAlerts, value);
    }

    public ICommand MuteCommand { get; }
    public ICommand UnmuteCommand { get; }
    public ICommand RefreshCommand { get; }

    private async Task InitializeAsync()
    {
        try
        {
            await RefreshAsync();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error initializing MainViewModel");
        }
    }

    private async Task RefreshAsync()
    {
        // Guard against concurrent refreshes
        if (_isRefreshing) return;
        _isRefreshing = true;

        try
        {
            // Get today's manifests
            var manifests = await _manifestService.GetTodaysManifestsAsync();

            // Update manifest view models
            var currentTime = DateTime.Now;

            // Remove manifests that no longer exist
            var toRemove = Manifests
                .Where(vm => !manifests.Any(m => m.Time == vm.Time))
                .ToList();

            foreach (var vm in toRemove)
            {
                Manifests.Remove(vm);
            }

            // Add or update manifests
            foreach (var manifest in manifests)
            {
                var existingVM = Manifests.FirstOrDefault(vm => vm.Time == manifest.Time);

                if (existingVM != null)
                {
                    // Update existing
                    existingVM.UpdateStatus();

                    // Update carriers
                    foreach (var carrierVM in existingVM.Carriers)
                    {
                        carrierVM.RefreshFromModel();
                    }
                }
                else
                {
                    // Add new
                    var newVM = new ManifestCardViewModel(manifest, _manifestService);
                    Manifests.Add(newVM);
                }
            }

            // Sort by time
            var sorted = Manifests.OrderBy(m => m.Time).ToList();
            Manifests.Clear();
            foreach (var item in sorted)
            {
                Manifests.Add(item);
            }

            // Update alert counts
            var summary = await _alertService.GetAlertSummaryAsync(manifests, currentTime);
            ActiveAlertCount = summary.ActiveAlertCount;
            MissedAlertCount = summary.MissedAlertCount;

            // Update mute status
            await UpdateMuteStatusAsync();

            // Check for new alerts to announce
            if (!IsMuted && (summary.ActiveAlertCount > 0 || summary.MissedAlertCount > 0))
            {
                await AnnounceAlertsAsync(summary);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error refreshing manifests");
        }
        finally
        {
            _isRefreshing = false;
        }
    }

    private async Task HandleMutePressAsync()
    {
        try
        {
            await _muteService.HandleMutePressAsync(Environment.UserName);
            await UpdateMuteStatusAsync();

            _logger.LogInformation("Mute button pressed");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error handling mute press");
        }
    }

    private async Task UnmuteAsync()
    {
        try
        {
            await _muteService.UnmuteAsync(Environment.UserName);
            await UpdateMuteStatusAsync();

            _logger.LogInformation("System unmuted");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error unmuting");
        }
    }

    private async Task UpdateMuteStatusAsync()
    {
        try
        {
            var status = await _muteService.GetCurrentStatusAsync();
            if (status == null) return;

            IsMuted = status.IsCurrentlyMuted();
            MuteStatusText = status.GetSummary();

            // Update mute button text based on press count
            if (!IsMuted || status.PressCount == 0)
            {
                MuteButtonText = "MUTE (5 MIN)";
            }
            else
            {
                MuteButtonText = status.PressCount switch
                {
                    1 => "EXTEND (10 MIN)",
                    2 => "EXTEND (15 MIN)",
                    3 => "MAX (15 MIN)",
                    _ => "MUTE (5 MIN)"
                };
            }

            // Update countdown display
            if (IsMuted && status.GetRemainingTime() != null)
            {
                ShowCountdown = true;
                CountdownText = status.GetRemainingTimeFormatted();
            }
            else
            {
                ShowCountdown = false;
                CountdownText = "";
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating mute status");
        }
    }

    private async Task UpdateCountdownAsync()
    {
        if (IsMuted)
        {
            await UpdateMuteStatusAsync();
        }
    }

    private async Task AnnounceAlertsAsync(AlertSummary summary)
    {
        try
        {
            // Build a key representing the current alert state
            var alertKey = $"active:{summary.ActiveAlertCount}|missed:{summary.MissedAlertCount}";

            // Only announce if this is a new alert state or interval has elapsed
            var now = DateTime.Now;
            var intervalElapsed = now - _lastAnnouncementTime >= _announcementInterval;
            var isNewAlert = !_announcedAlertKeys.Contains(alertKey);

            if (!isNewAlert && !intervalElapsed)
                return;

            if (summary.ActiveAlertCount > 0 || summary.MissedAlertCount > 0)
            {
                var message = "Manifest alert. ";

                if (summary.ActiveAlertCount > 0)
                {
                    message += $"{summary.ActiveAlertCount} active alert{(summary.ActiveAlertCount > 1 ? "s" : "")}. ";
                }

                if (summary.MissedAlertCount > 0)
                {
                    message += $"{summary.MissedAlertCount} missed alert{(summary.MissedAlertCount > 1 ? "s" : "")}. ";
                }

                await _voiceService.AnnounceAsync(message);
                _lastAnnouncementTime = now;
                _announcedAlertKeys.Add(alertKey);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error announcing alerts");
        }
    }

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        _refreshTimer.Stop();
        _countdownTimer.Stop();
        _voiceService.Dispose();
    }
}
