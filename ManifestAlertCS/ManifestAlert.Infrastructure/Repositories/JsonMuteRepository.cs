using ManifestAlert.Application.Interfaces;
using ManifestAlert.Domain.Models;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;

namespace ManifestAlert.Infrastructure.Repositories;

/// <summary>
/// JSON-based repository for mute status with network folder sync support
/// </summary>
public class JsonMuteRepository : IMuteRepository
{
    private readonly string _mutePath;
    private readonly ILogger<JsonMuteRepository> _logger;
    private MuteStatus? _cachedStatus;
    private DateTime _lastReadTime;
    private static readonly TimeSpan CacheTimeout = TimeSpan.FromMilliseconds(500);

    public JsonMuteRepository(string dataFolder, ILogger<JsonMuteRepository> logger)
    {
        _mutePath = Path.Combine(dataFolder, "mute.json");
        _logger = logger;

        // Ensure data folder exists
        Directory.CreateDirectory(dataFolder);

        // Create default mute status if doesn't exist
        if (!File.Exists(_mutePath))
        {
            var defaultStatus = MuteStatus.CreateUnmuted();
            SaveStatusAsync(defaultStatus).Wait();
        }
    }

    public async Task<MuteStatus> GetCurrentStatusAsync()
    {
        try
        {
            // Check cache (with 500ms TTL for fast refresh)
            if (_cachedStatus != null && (DateTime.Now - _lastReadTime) < CacheTimeout)
            {
                return _cachedStatus;
            }

            // Read from file
            var json = await File.ReadAllTextAsync(_mutePath);
            var status = JsonConvert.DeserializeObject<MuteStatus>(json) ?? MuteStatus.CreateUnmuted();

            // Update cache
            _cachedStatus = status;
            _lastReadTime = DateTime.Now;

            return status;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error loading mute status");
            return MuteStatus.CreateUnmuted();
        }
    }

    public async Task SaveStatusAsync(MuteStatus status)
    {
        try
        {
            var json = JsonConvert.SerializeObject(status, Formatting.Indented);
            await File.WriteAllTextAsync(_mutePath, json);

            // Update cache
            _cachedStatus = status;
            _lastReadTime = DateTime.Now;

            _logger.LogDebug("Mute status saved");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error saving mute status");
            throw;
        }
    }

    public async Task<bool> IsCurrentlyMutedAsync()
    {
        var status = await GetCurrentStatusAsync();
        return status.IsCurrentlyMuted();
    }
}
