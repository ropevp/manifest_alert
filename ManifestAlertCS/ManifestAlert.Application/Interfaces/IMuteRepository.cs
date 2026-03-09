using ManifestAlert.Domain.Models;

namespace ManifestAlert.Application.Interfaces;

/// <summary>
/// Repository interface for mute status operations
/// </summary>
public interface IMuteRepository
{
    /// <summary>
    /// Get current mute status
    /// </summary>
    Task<MuteStatus> GetCurrentStatusAsync();

    /// <summary>
    /// Save mute status
    /// </summary>
    Task SaveStatusAsync(MuteStatus status);

    /// <summary>
    /// Check if system is currently muted
    /// </summary>
    Task<bool> IsCurrentlyMutedAsync();
}
