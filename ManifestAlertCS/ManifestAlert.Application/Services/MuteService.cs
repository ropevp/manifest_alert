using ManifestAlert.Application.Interfaces;
using ManifestAlert.Domain.Models;
using Microsoft.Extensions.Logging;

namespace ManifestAlert.Application.Services;

/// <summary>
/// Service for managing mute/snooze operations with enhanced 3-press system
/// </summary>
public class MuteService
{
    private readonly IMuteRepository _repository;
    private readonly ILogger<MuteService> _logger;

    public MuteService(IMuteRepository repository, ILogger<MuteService> logger)
    {
        _repository = repository;
        _logger = logger;
    }

    /// <summary>
    /// Handle mute button press (3-press system: 5/10/15 min)
    /// </summary>
    public async Task HandleMutePressAsync(string? user = null)
    {
        try
        {
            var status = await _repository.GetCurrentStatusAsync();
            status.HandleMutePress(user);
            await _repository.SaveStatusAsync(status);

            _logger.LogInformation(
                "Mute press {PressCount} - Duration: {Duration} min",
                status.PressCount,
                status.DurationMinutes);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error handling mute press");
            throw;
        }
    }

    /// <summary>
    /// Mute for specific duration
    /// </summary>
    public async Task MuteAsync(int durationMinutes, string? user = null, string? reason = null)
    {
        try
        {
            var status = await _repository.GetCurrentStatusAsync();
            status.Mute(durationMinutes, user, reason);
            await _repository.SaveStatusAsync(status);

            _logger.LogInformation("System muted for {Duration} minutes by {User}", durationMinutes, user ?? "Unknown");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error muting system");
            throw;
        }
    }

    /// <summary>
    /// Mute indefinitely
    /// </summary>
    public async Task MuteIndefinitelyAsync(string? user = null, string? reason = null)
    {
        try
        {
            var status = await _repository.GetCurrentStatusAsync();
            status.MuteIndefinitely(user, reason);
            await _repository.SaveStatusAsync(status);

            _logger.LogInformation("System muted indefinitely by {User}", user ?? "Unknown");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error muting system indefinitely");
            throw;
        }
    }

    /// <summary>
    /// Unmute (resume alerts)
    /// </summary>
    public async Task UnmuteAsync(string? user = null)
    {
        try
        {
            var status = await _repository.GetCurrentStatusAsync();
            status.Unmute(user);
            await _repository.SaveStatusAsync(status);

            _logger.LogInformation("System unmuted by {User}", user ?? "Unknown");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error unmuting system");
            throw;
        }
    }

    /// <summary>
    /// Get current mute status
    /// </summary>
    public async Task<MuteStatus> GetCurrentStatusAsync()
    {
        try
        {
            return await _repository.GetCurrentStatusAsync();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting mute status");
            throw;
        }
    }

    /// <summary>
    /// Check if currently muted
    /// </summary>
    public async Task<bool> IsCurrentlyMutedAsync()
    {
        try
        {
            return await _repository.IsCurrentlyMutedAsync();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error checking mute status");
            return false;
        }
    }

    /// <summary>
    /// Extend current mute duration
    /// </summary>
    public async Task ExtendMuteAsync(int additionalMinutes, string? user = null)
    {
        try
        {
            var status = await _repository.GetCurrentStatusAsync();
            status.ExtendMute(additionalMinutes, user);
            await _repository.SaveStatusAsync(status);

            _logger.LogInformation("Mute extended by {Duration} minutes", additionalMinutes);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error extending mute");
            throw;
        }
    }
}
