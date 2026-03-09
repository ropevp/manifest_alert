using ManifestAlert.Domain.Models;

namespace ManifestAlert.Application.Interfaces;

/// <summary>
/// Repository interface for manifest data operations
/// </summary>
public interface IManifestRepository
{
    /// <summary>
    /// Get all manifests for a specific date
    /// </summary>
    Task<List<Manifest>> GetManifestsAsync(string date);

    /// <summary>
    /// Get all manifests for today
    /// </summary>
    Task<List<Manifest>> GetTodaysManifestsAsync();

    /// <summary>
    /// Load manifest configuration (times and carriers)
    /// </summary>
    Task<List<Manifest>> LoadManifestConfigAsync();

    /// <summary>
    /// Save acknowledgment
    /// </summary>
    Task SaveAcknowledgmentAsync(Acknowledgment acknowledgment);

    /// <summary>
    /// Get all acknowledgments for a specific date
    /// </summary>
    Task<List<Acknowledgment>> GetAcknowledgmentsAsync(string date);

    /// <summary>
    /// Remove acknowledgment (for undo functionality)
    /// </summary>
    Task RemoveAcknowledgmentAsync(string date, string manifestTime, string carrier);

    /// <summary>
    /// Update customer message for a carrier
    /// </summary>
    Task UpdateCustomerMessageAsync(string date, string manifestTime, string carrier, string? message);
}
