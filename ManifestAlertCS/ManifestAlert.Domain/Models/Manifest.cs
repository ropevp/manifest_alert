namespace ManifestAlert.Domain.Models;

/// <summary>
/// Represents a manifest containing multiple carriers scheduled for a specific time
/// </summary>
public class Manifest
{
    public string Date { get; set; } = string.Empty;
    public string Time { get; set; } = string.Empty;
    public List<Carrier> Carriers { get; set; } = new();

    /// <summary>
    /// Get all carriers that have not been acknowledged
    /// </summary>
    public List<Carrier> GetUnacknowledgedCarriers()
    {
        return Carriers.Where(c => !c.IsAcknowledged).ToList();
    }

    /// <summary>
    /// Get all acknowledged carriers
    /// </summary>
    public List<Carrier> GetAcknowledgedCarriers()
    {
        return Carriers.Where(c => c.IsAcknowledged).ToList();
    }

    /// <summary>
    /// Check if all carriers are acknowledged
    /// </summary>
    public bool IsFullyAcknowledged => Carriers.All(c => c.IsAcknowledged);

    /// <summary>
    /// Check if any carriers are acknowledged
    /// </summary>
    public bool HasAnyAcknowledged => Carriers.Any(c => c.IsAcknowledged);

    /// <summary>
    /// Get the manifest date and time as a DateTime
    /// </summary>
    public DateTime GetManifestDateTime()
    {
        if (DateTime.TryParse($"{Date} {Time}", out var dateTime))
        {
            return dateTime;
        }
        throw new InvalidOperationException($"Invalid date/time format: {Date} {Time}");
    }

    /// <summary>
    /// Check if manifest is currently active (within alert window)
    /// </summary>
    public bool IsActive(DateTime currentTime, int alertWindowMinutes = 30, int preAlertMinutes = 2)
    {
        var manifestTime = GetManifestDateTime();
        var startTime = manifestTime.AddMinutes(-preAlertMinutes);
        var endTime = manifestTime.AddMinutes(alertWindowMinutes);

        return currentTime >= startTime && currentTime <= endTime;
    }

    /// <summary>
    /// Get the current status of this manifest
    /// </summary>
    public ManifestStatus GetStatus(DateTime currentTime, int alertWindowMinutes = 30, int preAlertMinutes = 2)
    {
        if (IsFullyAcknowledged)
            return ManifestStatus.Acknowledged;

        var manifestTime = GetManifestDateTime();
        var startTime = manifestTime.AddMinutes(-preAlertMinutes);
        var endTime = manifestTime.AddMinutes(alertWindowMinutes);

        if (currentTime < startTime)
            return ManifestStatus.Pending;

        if (currentTime >= startTime && currentTime <= endTime)
            return ManifestStatus.Active;

        return ManifestStatus.Missed;
    }

    /// <summary>
    /// Acknowledge a specific carrier in this manifest
    /// </summary>
    public void AcknowledgeCarrier(string carrierName, string user, string? reason = null, string? customerMessage = null)
    {
        var carrier = Carriers.FirstOrDefault(c => c.Name.Equals(carrierName, StringComparison.OrdinalIgnoreCase));
        if (carrier != null)
        {
            carrier.Acknowledge(user, reason, customerMessage);
        }
    }

    /// <summary>
    /// Acknowledge all carriers in this manifest
    /// </summary>
    public void AcknowledgeAll(string user, string? reason = null)
    {
        foreach (var carrier in Carriers)
        {
            carrier.Acknowledge(user, reason);
        }
    }

    public override string ToString() => $"Manifest {Time} ({Carriers.Count} carriers)";
}
