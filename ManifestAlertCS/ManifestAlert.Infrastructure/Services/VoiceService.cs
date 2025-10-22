using Microsoft.Extensions.Logging;
using System.Speech.Synthesis;

namespace ManifestAlert.Infrastructure.Services;

/// <summary>
/// Service for text-to-speech voice announcements
/// </summary>
public class VoiceService : IDisposable
{
    private readonly SpeechSynthesizer _synthesizer;
    private readonly ILogger<VoiceService> _logger;
    private bool _disposed;

    public VoiceService(ILogger<VoiceService> logger)
    {
        _logger = logger;
        _synthesizer = new SpeechSynthesizer();

        // Configure speech synthesizer
        _synthesizer.Volume = 100; // 0-100
        _synthesizer.Rate = 0;     // -10 to 10
    }

    /// <summary>
    /// Announce a message via text-to-speech
    /// </summary>
    public async Task AnnounceAsync(string message)
    {
        try
        {
            if (_disposed)
            {
                _logger.LogWarning("Attempted to use disposed VoiceService");
                return;
            }

            _logger.LogInformation("Announcing: {Message}", message);

            await Task.Run(() =>
            {
                _synthesizer.SpeakAsync(message);
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error announcing message");
        }
    }

    /// <summary>
    /// Announce a message synchronously (blocking)
    /// </summary>
    public void Announce(string message)
    {
        try
        {
            if (_disposed)
            {
                _logger.LogWarning("Attempted to use disposed VoiceService");
                return;
            }

            _logger.LogInformation("Announcing: {Message}", message);
            _synthesizer.Speak(message);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error announcing message");
        }
    }

    /// <summary>
    /// Cancel all current announcements
    /// </summary>
    public void CancelAll()
    {
        try
        {
            _synthesizer.SpeakAsyncCancelAll();
            _logger.LogDebug("All announcements cancelled");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error cancelling announcements");
        }
    }

    /// <summary>
    /// Set voice volume (0-100)
    /// </summary>
    public void SetVolume(int volume)
    {
        if (volume < 0 || volume > 100)
            throw new ArgumentOutOfRangeException(nameof(volume), "Volume must be between 0 and 100");

        _synthesizer.Volume = volume;
        _logger.LogDebug("Voice volume set to {Volume}", volume);
    }

    /// <summary>
    /// Set speech rate (-10 to 10)
    /// </summary>
    public void SetRate(int rate)
    {
        if (rate < -10 || rate > 10)
            throw new ArgumentOutOfRangeException(nameof(rate), "Rate must be between -10 and 10");

        _synthesizer.Rate = rate;
        _logger.LogDebug("Voice rate set to {Rate}", rate);
    }

    public void Dispose()
    {
        if (!_disposed)
        {
            _synthesizer?.Dispose();
            _disposed = true;
        }
    }
}
