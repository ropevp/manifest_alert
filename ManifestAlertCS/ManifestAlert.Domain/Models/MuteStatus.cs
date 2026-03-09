namespace ManifestAlert.Domain.Models;

/// <summary>
/// Type of mute operation
/// </summary>
public enum MuteType
{
    Disabled,
    Manual,
    Snooze
}

/// <summary>
/// Represents the mute state with enhanced 3-press system
/// 1 press = 5 minutes
/// 2 presses = 10 minutes
/// 3 presses = 15 minutes
/// </summary>
public class MuteStatus
{
    public bool IsMuted { get; set; }
    public MuteType MuteType { get; set; } = MuteType.Disabled;
    public DateTime? MutedAt { get; set; }
    public DateTime? MuteEndTime { get; set; }
    public string? MutedBy { get; set; }
    public string? Reason { get; set; }
    public int PressCount { get; set; } // Tracks number of consecutive presses (1-3)
    public int DurationMinutes { get; set; } // Current mute duration

    // Press configuration
    private const int FirstPressDuration = 5;   // 5 minutes
    private const int SecondPressDuration = 10; // 10 minutes
    private const int ThirdPressDuration = 15;  // 15 minutes
    private static readonly TimeSpan PressResetWindow = TimeSpan.FromSeconds(3); // Window to detect multiple presses

    private DateTime? _lastPressTime;

    /// <summary>
    /// Check if currently muted (and not expired)
    /// </summary>
    public bool IsCurrentlyMuted(DateTime? currentTime = null)
    {
        currentTime ??= DateTime.Now;

        if (!IsMuted)
            return false;

        // Check if snooze has expired
        if (MuteType == MuteType.Snooze && MuteEndTime.HasValue)
        {
            if (currentTime >= MuteEndTime)
            {
                Unmute();
                return false;
            }
        }

        return true;
    }

    /// <summary>
    /// Get remaining time until unmute
    /// </summary>
    public TimeSpan? GetRemainingTime(DateTime? currentTime = null)
    {
        currentTime ??= DateTime.Now;

        if (!IsCurrentlyMuted(currentTime) || !MuteEndTime.HasValue)
            return null;

        var remaining = MuteEndTime.Value - currentTime.Value;
        return remaining.TotalSeconds > 0 ? remaining : TimeSpan.Zero;
    }

    /// <summary>
    /// Get remaining time in minutes (rounded)
    /// </summary>
    public int? GetRemainingMinutes(DateTime? currentTime = null)
    {
        var remaining = GetRemainingTime(currentTime);
        return remaining.HasValue ? Math.Max(0, (int)Math.Ceiling(remaining.Value.TotalMinutes)) : null;
    }

    /// <summary>
    /// Get remaining time formatted as MM:SS
    /// </summary>
    public string GetRemainingTimeFormatted(DateTime? currentTime = null)
    {
        var remaining = GetRemainingTime(currentTime);
        if (!remaining.HasValue)
            return "N/A";

        var minutes = (int)remaining.Value.TotalMinutes;
        var seconds = remaining.Value.Seconds;
        return $"{minutes:D2}:{seconds:D2}";
    }

    /// <summary>
    /// Handle mute button press with 3-press system
    /// 1st press (within 3 seconds) = 5 min
    /// 2nd press (within 3 seconds) = 10 min
    /// 3rd press (within 3 seconds) = 15 min
    /// </summary>
    public void HandleMutePress(string? user = null)
    {
        var now = DateTime.Now;

        // Check if this is part of a multi-press sequence
        if (_lastPressTime.HasValue && (now - _lastPressTime.Value) <= PressResetWindow)
        {
            // Increment press count (max 3)
            PressCount = Math.Min(PressCount + 1, 3);
        }
        else
        {
            // New press sequence
            PressCount = 1;
        }

        _lastPressTime = now;

        // Determine duration based on press count
        int duration = PressCount switch
        {
            1 => FirstPressDuration,
            2 => SecondPressDuration,
            3 => ThirdPressDuration,
            _ => FirstPressDuration
        };

        // Apply the mute
        Mute(duration, user, $"Snooze {duration} min (Press {PressCount})");
    }

    /// <summary>
    /// Mute for a specific duration
    /// </summary>
    public void Mute(int durationMinutes, string? user = null, string? reason = null)
    {
        if (durationMinutes <= 0)
            throw new ArgumentException("Duration must be positive", nameof(durationMinutes));

        var now = DateTime.Now;

        IsMuted = true;
        MutedAt = now;
        MutedBy = user;
        Reason = reason;
        DurationMinutes = durationMinutes;

        if (durationMinutes > 0)
        {
            MuteType = MuteType.Snooze;
            MuteEndTime = now.AddMinutes(durationMinutes);
        }
        else
        {
            MuteType = MuteType.Manual;
            MuteEndTime = null;
        }
    }

    /// <summary>
    /// Mute indefinitely
    /// </summary>
    public void MuteIndefinitely(string? user = null, string? reason = null)
    {
        var now = DateTime.Now;

        IsMuted = true;
        MuteType = MuteType.Manual;
        MutedAt = now;
        MutedBy = user;
        Reason = reason;
        MuteEndTime = null;
        DurationMinutes = 0;
        PressCount = 0;
        _lastPressTime = null;
    }

    /// <summary>
    /// Unmute (resume alerts)
    /// </summary>
    public void Unmute(string? user = null)
    {
        IsMuted = false;
        MuteType = MuteType.Disabled;
        MutedAt = null;
        MuteEndTime = null;
        MutedBy = user;
        Reason = null;
        DurationMinutes = 0;
        PressCount = 0;
        _lastPressTime = null;
    }

    /// <summary>
    /// Extend current mute by additional minutes
    /// </summary>
    public void ExtendMute(int additionalMinutes, string? user = null)
    {
        if (!IsCurrentlyMuted())
            throw new InvalidOperationException("Cannot extend mute when not muted");

        if (additionalMinutes <= 0)
            throw new ArgumentException("Additional minutes must be positive", nameof(additionalMinutes));

        DurationMinutes += additionalMinutes;

        if (MuteEndTime.HasValue)
        {
            MuteEndTime = MuteEndTime.Value.AddMinutes(additionalMinutes);
        }
        else
        {
            // Convert to timed mute if it was indefinite
            MuteEndTime = DateTime.Now.AddMinutes(additionalMinutes);
            MuteType = MuteType.Snooze;
        }

        if (user != null)
            MutedBy = user;
    }

    /// <summary>
    /// Get human-readable summary of mute status
    /// </summary>
    public string GetSummary()
    {
        if (!IsCurrentlyMuted())
            return "Alerts Active";

        if (MuteType == MuteType.Manual)
        {
            var summary = "Muted Indefinitely";
            if (!string.IsNullOrEmpty(MutedBy))
                summary += $" by {MutedBy}";
            return summary;
        }

        if (MuteType == MuteType.Snooze)
        {
            var remaining = GetRemainingMinutes();
            var summary = remaining.HasValue && remaining > 0
                ? $"Snoozed for {remaining} more min"
                : "Snooze Expired";

            if (!string.IsNullOrEmpty(MutedBy))
                summary += $" by {MutedBy}";

            return summary;
        }

        return "Muted";
    }

    /// <summary>
    /// Create an unmuted status
    /// </summary>
    public static MuteStatus CreateUnmuted() => new();

    /// <summary>
    /// Create a muted status with specific duration
    /// </summary>
    public static MuteStatus CreateMuted(int durationMinutes, string? user = null, string? reason = null)
    {
        var status = new MuteStatus();
        status.Mute(durationMinutes, user, reason);
        return status;
    }

    public override string ToString() => GetSummary();
}
