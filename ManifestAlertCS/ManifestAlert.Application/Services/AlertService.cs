using ManifestAlert.Application.Interfaces;
using ManifestAlert.Domain.Models;
using Microsoft.Extensions.Logging;

namespace ManifestAlert.Application.Services;

/// <summary>
/// Service for managing alert logic and display calculations
/// </summary>
public class AlertService
{
    private readonly IManifestRepository _manifestRepository;
    private readonly IMuteRepository _muteRepository;
    private readonly ILogger<AlertService> _logger;

    // Alert configuration
    public int AlertWindowMinutes { get; set; } = 30;
    public int PreAlertMinutes { get; set; } = 2;

    public AlertService(
        IManifestRepository manifestRepository,
        IMuteRepository muteRepository,
        ILogger<AlertService> logger)
    {
        _manifestRepository = manifestRepository;
        _muteRepository = muteRepository;
        _logger = logger;
    }

    /// <summary>
    /// Determine if a manifest should trigger alerts
    /// </summary>
    public async Task<bool> ShouldTriggerAlertAsync(Manifest manifest, DateTime? currentTime = null)
    {
        currentTime ??= DateTime.Now;

        try
        {
            // Check if all carriers are acknowledged
            if (manifest.IsFullyAcknowledged)
                return false;

            // Check if manifest is in alertable state
            if (!manifest.IsActive(currentTime.Value, AlertWindowMinutes, PreAlertMinutes))
                return false;

            // Check if system is muted
            if (await _muteRepository.IsCurrentlyMutedAsync())
                return false;

            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error checking alert trigger for manifest {Time}", manifest.Time);
            return false;
        }
    }

    /// <summary>
    /// Calculate optimal layout mode based on current alerts
    /// Single card mode: exactly one manifest active, no missed manifests
    /// </summary>
    public async Task<(bool SingleCardMode, int ActiveCount, int MissedCount)> CalculateLayoutModeAsync(
        List<Manifest> manifests,
        DateTime? currentTime = null)
    {
        currentTime ??= DateTime.Now;

        try
        {
            if (await _muteRepository.IsCurrentlyMutedAsync())
                return (false, 0, 0);

            var activeCount = 0;
            var missedCount = 0;

            foreach (var manifest in manifests)
            {
                if (await ShouldTriggerAlertAsync(manifest, currentTime))
                {
                    var status = manifest.GetStatus(currentTime.Value, AlertWindowMinutes, PreAlertMinutes);
                    if (status == ManifestStatus.Active)
                        activeCount++;
                    else if (status == ManifestStatus.Missed)
                        missedCount++;
                }
            }

            // Single card mode: exactly 1 active, 0 missed
            var singleCardMode = activeCount == 1 && missedCount == 0;

            return (singleCardMode, activeCount, missedCount);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error calculating layout mode");
            return (false, 0, 0);
        }
    }

    /// <summary>
    /// Get comprehensive alert summary
    /// </summary>
    public async Task<AlertSummary> GetAlertSummaryAsync(List<Manifest> manifests, DateTime? currentTime = null)
    {
        currentTime ??= DateTime.Now;

        var summary = new AlertSummary
        {
            TotalManifests = manifests.Count,
            IsMuted = await _muteRepository.IsCurrentlyMutedAsync()
        };

        foreach (var manifest in manifests)
        {
            var status = manifest.GetStatus(currentTime.Value, AlertWindowMinutes, PreAlertMinutes);

            switch (status)
            {
                case ManifestStatus.Active when !manifest.IsFullyAcknowledged:
                    summary.ActiveManifests.Add(manifest);
                    summary.ActiveAlertCount += manifest.GetUnacknowledgedCarriers().Count;
                    break;

                case ManifestStatus.Missed when !manifest.IsFullyAcknowledged:
                    summary.MissedManifests.Add(manifest);
                    summary.MissedAlertCount += manifest.GetUnacknowledgedCarriers().Count;
                    break;

                case ManifestStatus.Pending:
                    summary.PendingManifests.Add(manifest);
                    break;

                case ManifestStatus.Acknowledged:
                    summary.AcknowledgedManifests.Add(manifest);
                    break;
            }
        }

        summary.TotalAlertCount = summary.ActiveAlertCount + summary.MissedAlertCount;

        return summary;
    }
}

/// <summary>
/// Summary of current alert state
/// </summary>
public class AlertSummary
{
    public int TotalManifests { get; set; }
    public List<Manifest> ActiveManifests { get; set; } = new();
    public List<Manifest> MissedManifests { get; set; } = new();
    public List<Manifest> PendingManifests { get; set; } = new();
    public List<Manifest> AcknowledgedManifests { get; set; } = new();
    public int TotalAlertCount { get; set; }
    public int ActiveAlertCount { get; set; }
    public int MissedAlertCount { get; set; }
    public bool IsMuted { get; set; }
}
