namespace ManifestAlert.Domain.Models;

/// <summary>
/// Represents a shipping carrier that can be part of a manifest
/// </summary>
public class Carrier
{
    public string Name { get; set; } = string.Empty;
    public bool IsAcknowledged { get; set; }
    public string? AcknowledgedBy { get; set; }
    public DateTime? AcknowledgedAt { get; set; }
    public string? Reason { get; set; }
    public string? CustomerMessage { get; set; }

    public Carrier()
    {
    }

    public Carrier(string name)
    {
        Name = name ?? throw new ArgumentNullException(nameof(name));
    }

    /// <summary>
    /// Acknowledge this carrier
    /// </summary>
    public void Acknowledge(string user, string? reason = null, string? customerMessage = null)
    {
        IsAcknowledged = true;
        AcknowledgedBy = user;
        AcknowledgedAt = DateTime.Now;
        Reason = reason;
        CustomerMessage = customerMessage;
    }

    /// <summary>
    /// Undo acknowledgment (revert to pending)
    /// </summary>
    public void UndoAcknowledgment()
    {
        IsAcknowledged = false;
        AcknowledgedBy = null;
        AcknowledgedAt = null;
        Reason = null;
        // Note: CustomerMessage is preserved
    }

    /// <summary>
    /// Update customer message without changing acknowledgment status
    /// </summary>
    public void UpdateCustomerMessage(string? message)
    {
        CustomerMessage = message;
    }

    public override string ToString() => Name;
}
