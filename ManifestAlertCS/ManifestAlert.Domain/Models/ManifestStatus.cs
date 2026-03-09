namespace ManifestAlert.Domain.Models;

/// <summary>
/// Status of a manifest relative to current time
/// </summary>
public enum ManifestStatus
{
    /// <summary>
    /// Manifest time has not yet arrived
    /// </summary>
    Pending,

    /// <summary>
    /// Manifest is currently active and requires attention
    /// </summary>
    Active,

    /// <summary>
    /// Manifest time has passed the alert window
    /// </summary>
    Missed,

    /// <summary>
    /// All carriers in the manifest have been acknowledged
    /// </summary>
    Acknowledged
}
