using ManifestAlert.Application.Services;
using ManifestAlert.Domain.Models;
using System.Collections.ObjectModel;
using System.Windows;
using System.Windows.Input;

namespace ManifestAlert.WPF.ViewModels;

/// <summary>
/// ViewModel for individual manifest card
/// </summary>
public class ManifestCardViewModel : ViewModelBase
{
    internal readonly ManifestService _manifestService;
    private readonly Manifest _manifest;
    private string _statusText = string.Empty;
    private string _statusColor = "#4CAF50";
    private bool _isActive;
    private bool _isMissed;

    public ManifestCardViewModel(Manifest manifest, ManifestService manifestService)
    {
        _manifest = manifest;
        _manifestService = manifestService;

        Carriers = new ObservableCollection<CarrierViewModel>(
            manifest.Carriers.Select(c => new CarrierViewModel(c, this)));

        UpdateStatus();

        // Commands
        AcknowledgeAllCommand = new RelayCommand(async () => await AcknowledgeAllAsync());
    }

    public string Time => _manifest.Time;
    public string Date => _manifest.Date;

    public ObservableCollection<CarrierViewModel> Carriers { get; }

    public string StatusText
    {
        get => _statusText;
        set => SetProperty(ref _statusText, value);
    }

    public string StatusColor
    {
        get => _statusColor;
        set => SetProperty(ref _statusColor, value);
    }

    public bool IsActive
    {
        get => _isActive;
        set => SetProperty(ref _isActive, value);
    }

    public bool IsMissed
    {
        get => _isMissed;
        set => SetProperty(ref _isMissed, value);
    }

    public ICommand AcknowledgeAllCommand { get; }

    public void UpdateStatus()
    {
        var status = _manifest.GetStatus(DateTime.Now);

        IsActive = status == ManifestStatus.Active;
        IsMissed = status == ManifestStatus.Missed;

        StatusText = status switch
        {
            ManifestStatus.Pending => "PENDING",
            ManifestStatus.Active => "ACTIVE",
            ManifestStatus.Missed => "MISSED",
            ManifestStatus.Acknowledged => "COMPLETE",
            _ => "UNKNOWN"
        };

        StatusColor = status switch
        {
            ManifestStatus.Pending => "#2196F3", // Blue
            ManifestStatus.Active => "#FF9800",  // Orange
            ManifestStatus.Missed => "#F44336",  // Red
            ManifestStatus.Acknowledged => "#4CAF50", // Green
            _ => "#9E9E9E" // Grey
        };

        OnPropertyChanged(nameof(StatusText));
        OnPropertyChanged(nameof(StatusColor));
        OnPropertyChanged(nameof(IsActive));
        OnPropertyChanged(nameof(IsMissed));
    }

    private async Task AcknowledgeAllAsync()
    {
        try
        {
            var carrierNames = _manifest.Carriers.Select(c => c.Name).ToList();
            await _manifestService.AcknowledgeAllCarriersAsync(
                _manifest.Date,
                _manifest.Time,
                carrierNames,
                Environment.UserName);

            // Update all carrier view models
            foreach (var carrierVM in Carriers)
            {
                carrierVM.RefreshFromModel();
            }

            UpdateStatus();
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Error acknowledging all carriers: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }
}

/// <summary>
/// ViewModel for individual carrier within a manifest card
/// </summary>
public class CarrierViewModel : ViewModelBase
{
    private readonly Carrier _carrier;
    private readonly ManifestCardViewModel _parent;
    private bool _isAcknowledged;
    private string? _acknowledgedBy;
    private string? _customerMessage;
    private bool _isEditingMessage;

    public CarrierViewModel(Carrier carrier, ManifestCardViewModel parent)
    {
        _carrier = carrier;
        _parent = parent;

        RefreshFromModel();

        // Commands
        ToggleAcknowledgmentCommand = new RelayCommand(async () => await ToggleAcknowledgmentAsync());
        EditMessageCommand = new RelayCommand(() => IsEditingMessage = true);
        SaveMessageCommand = new RelayCommand(async () => await SaveMessageAsync());
        CancelEditCommand = new RelayCommand(() =>
        {
            IsEditingMessage = false;
            OnPropertyChanged(nameof(CustomerMessage));
        });
    }

    public string Name => _carrier.Name;

    public bool IsAcknowledged
    {
        get => _isAcknowledged;
        set => SetProperty(ref _isAcknowledged, value);
    }

    public string? AcknowledgedBy
    {
        get => _acknowledgedBy;
        set => SetProperty(ref _acknowledgedBy, value);
    }

    public string? CustomerMessage
    {
        get => _customerMessage;
        set => SetProperty(ref _customerMessage, value);
    }

    public bool IsEditingMessage
    {
        get => _isEditingMessage;
        set => SetProperty(ref _isEditingMessage, value);
    }

    public bool HasCustomerMessage => !string.IsNullOrEmpty(_customerMessage);

    public string DisplayText
    {
        get
        {
            var text = Name;
            if (IsAcknowledged && !string.IsNullOrEmpty(AcknowledgedBy))
                text += $" (by {AcknowledgedBy})";
            if (!string.IsNullOrEmpty(CustomerMessage))
                text += $" - {CustomerMessage}";
            return text;
        }
    }

    public ICommand ToggleAcknowledgmentCommand { get; }
    public ICommand EditMessageCommand { get; }
    public ICommand SaveMessageCommand { get; }
    public ICommand CancelEditCommand { get; }

    public void RefreshFromModel()
    {
        IsAcknowledged = _carrier.IsAcknowledged;
        AcknowledgedBy = _carrier.AcknowledgedBy;
        CustomerMessage = _carrier.CustomerMessage;
        OnPropertyChanged(nameof(HasCustomerMessage));
        OnPropertyChanged(nameof(DisplayText));
    }

    private async Task ToggleAcknowledgmentAsync()
    {
        try
        {
            var service = _parent._manifestService;

            if (IsAcknowledged)
            {
                // Undo acknowledgment
                await service.UndoAcknowledgmentAsync(_parent.Date, _parent.Time, Name);
                _carrier.UndoAcknowledgment();
            }
            else
            {
                // Acknowledge
                await service.AcknowledgeCarrierAsync(
                    _parent.Date,
                    _parent.Time,
                    Name,
                    Environment.UserName,
                    customerMessage: CustomerMessage);
                _carrier.Acknowledge(Environment.UserName, customerMessage: CustomerMessage);
            }

            RefreshFromModel();
            _parent.UpdateStatus();
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Error toggling acknowledgment: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    private async Task SaveMessageAsync()
    {
        try
        {
            var service = _parent._manifestService;
            await service.UpdateCustomerMessageAsync(_parent.Date, _parent.Time, Name, CustomerMessage);

            _carrier.UpdateCustomerMessage(CustomerMessage);
            IsEditingMessage = false;
            OnPropertyChanged(nameof(DisplayText));
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Error saving message: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }
}
