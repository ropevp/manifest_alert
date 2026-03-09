namespace ManifestAlert.Domain.Models;

/// <summary>
/// Represents an acknowledgment record for tracking user actions
/// </summary>
public class Acknowledgment
{
    public string Date { get; set; } = string.Empty;
    public string ManifestTime { get; set; } = string.Empty;
    public string Carrier { get; set; } = string.Empty;
    public string User { get; set; } = string.Empty;
    public string? Reason { get; set; }
    public string? CustomerMessage { get; set; }
    public DateTime Timestamp { get; set; }

    public Acknowledgment()
    {
        Timestamp = DateTime.Now;
    }

    public Acknowledgment(string date, string manifestTime, string carrier, string user, string? reason = null, string? customerMessage = null)
    {
        Date = date ?? throw new ArgumentNullException(nameof(date));
        ManifestTime = manifestTime ?? throw new ArgumentNullException(nameof(manifestTime));
        Carrier = carrier ?? throw new ArgumentNullException(nameof(carrier));
        User = user ?? throw new ArgumentNullException(nameof(user));
        Reason = reason;
        CustomerMessage = customerMessage;
        Timestamp = DateTime.Now;
    }

    /// <summary>
    /// Get unique key for this manifest
    /// </summary>
    public string GetManifestKey() => $"{Date}_{ManifestTime}";

    /// <summary>
    /// Get unique key for this carrier acknowledgment
    /// </summary>
    public string GetCarrierKey() => $"{GetManifestKey()}_{Carrier}";

    /// <summary>
    /// Check if this acknowledgment is for the same manifest
    /// </summary>
    public bool IsSameManifest(string date, string time) =>
        Date == date && ManifestTime == time;

    /// <summary>
    /// Check if this acknowledgment is for the same carrier
    /// </summary>
    public bool IsSameCarrier(string date, string time, string carrier) =>
        IsSameManifest(date, time) && Carrier.Equals(carrier, StringComparison.OrdinalIgnoreCase);

    public override string ToString() =>
        $"{Carrier} acknowledged by {User} at {Timestamp:HH:mm:ss}" +
        (string.IsNullOrEmpty(Reason) ? "" : $" ({Reason})");
}
