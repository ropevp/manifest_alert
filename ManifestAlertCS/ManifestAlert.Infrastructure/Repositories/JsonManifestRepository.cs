using ManifestAlert.Application.Interfaces;
using ManifestAlert.Domain.Models;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace ManifestAlert.Infrastructure.Repositories;

/// <summary>
/// JSON-based repository for manifest and acknowledgment data
/// </summary>
public class JsonManifestRepository : IManifestRepository
{
    private readonly string _configPath;
    private readonly string _ackPath;
    private readonly ILogger<JsonManifestRepository> _logger;

    public JsonManifestRepository(string dataFolder, ILogger<JsonManifestRepository> logger)
    {
        _configPath = Path.Combine(dataFolder, "config.json");
        _ackPath = Path.Combine(dataFolder, "ack.json");
        _logger = logger;

        // Ensure data folder exists
        Directory.CreateDirectory(dataFolder);

        // Create default config if doesn't exist
        if (!File.Exists(_configPath))
        {
            CreateDefaultConfig();
        }

        // Create empty ack file if doesn't exist
        if (!File.Exists(_ackPath))
        {
            File.WriteAllText(_ackPath, "[]");
        }
    }

    public async Task<List<Manifest>> GetManifestsAsync(string date)
    {
        var manifests = await LoadManifestConfigAsync();
        var acknowledgments = await GetAcknowledgmentsAsync(date);

        // Apply acknowledgments
        foreach (var manifest in manifests)
        {
            manifest.Date = date;

            foreach (var carrier in manifest.Carriers)
            {
                var ack = acknowledgments.FirstOrDefault(a =>
                    a.IsSameCarrier(date, manifest.Time, carrier.Name));

                if (ack != null)
                {
                    carrier.IsAcknowledged = true;
                    carrier.AcknowledgedBy = ack.User;
                    carrier.AcknowledgedAt = ack.Timestamp;
                    carrier.Reason = ack.Reason;
                    carrier.CustomerMessage = ack.CustomerMessage;
                }
            }
        }

        return manifests;
    }

    public async Task<List<Manifest>> GetTodaysManifestsAsync()
    {
        var today = DateTime.Now.ToString("yyyy-MM-dd");
        return await GetManifestsAsync(today);
    }

    public async Task<List<Manifest>> LoadManifestConfigAsync()
    {
        try
        {
            var json = await File.ReadAllTextAsync(_configPath);
            var config = JObject.Parse(json);
            var manifestsArray = config["manifests"] as JArray;

            var manifests = new List<Manifest>();

            if (manifestsArray != null)
            {
                foreach (var manifestObj in manifestsArray)
                {
                    var time = manifestObj["time"]?.ToString() ?? "";
                    var carriersArray = manifestObj["carriers"] as JArray;

                    var manifest = new Manifest
                    {
                        Time = time,
                        Carriers = new List<Carrier>()
                    };

                    if (carriersArray != null)
                    {
                        foreach (var carrierName in carriersArray)
                        {
                            manifest.Carriers.Add(new Carrier(carrierName.ToString()));
                        }
                    }

                    manifests.Add(manifest);
                }
            }

            _logger.LogInformation("Loaded {Count} manifests from config", manifests.Count);
            return manifests;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error loading manifest config");
            throw;
        }
    }

    public async Task SaveAcknowledgmentAsync(Acknowledgment acknowledgment)
    {
        try
        {
            var acknowledgments = await GetAllAcknowledgmentsAsync();

            // Remove existing acknowledgment for same carrier (if any)
            acknowledgments.RemoveAll(a =>
                a.IsSameCarrier(acknowledgment.Date, acknowledgment.ManifestTime, acknowledgment.Carrier));

            // Add new acknowledgment
            acknowledgments.Add(acknowledgment);

            // Save to file
            var json = JsonConvert.SerializeObject(acknowledgments, Formatting.Indented);
            await File.WriteAllTextAsync(_ackPath, json);

            _logger.LogInformation("Acknowledgment saved for {Carrier}", acknowledgment.Carrier);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error saving acknowledgment");
            throw;
        }
    }

    public async Task<List<Acknowledgment>> GetAcknowledgmentsAsync(string date)
    {
        var allAcks = await GetAllAcknowledgmentsAsync();
        return allAcks.Where(a => a.Date == date).ToList();
    }

    public async Task RemoveAcknowledgmentAsync(string date, string manifestTime, string carrier)
    {
        try
        {
            var acknowledgments = await GetAllAcknowledgmentsAsync();

            // Remove the acknowledgment
            var removed = acknowledgments.RemoveAll(a =>
                a.IsSameCarrier(date, manifestTime, carrier));

            if (removed > 0)
            {
                // Save to file
                var json = JsonConvert.SerializeObject(acknowledgments, Formatting.Indented);
                await File.WriteAllTextAsync(_ackPath, json);

                _logger.LogInformation("Acknowledgment removed for {Carrier}", carrier);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error removing acknowledgment");
            throw;
        }
    }

    public async Task UpdateCustomerMessageAsync(string date, string manifestTime, string carrier, string? message)
    {
        try
        {
            var acknowledgments = await GetAllAcknowledgmentsAsync();

            var ack = acknowledgments.FirstOrDefault(a =>
                a.IsSameCarrier(date, manifestTime, carrier));

            if (ack != null)
            {
                ack.CustomerMessage = message;

                // Save to file
                var json = JsonConvert.SerializeObject(acknowledgments, Formatting.Indented);
                await File.WriteAllTextAsync(_ackPath, json);

                _logger.LogInformation("Customer message updated for {Carrier}", carrier);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating customer message");
            throw;
        }
    }

    private async Task<List<Acknowledgment>> GetAllAcknowledgmentsAsync()
    {
        try
        {
            if (!File.Exists(_ackPath))
            {
                return new List<Acknowledgment>();
            }

            var json = await File.ReadAllTextAsync(_ackPath);
            var acknowledgments = JsonConvert.DeserializeObject<List<Acknowledgment>>(json);
            return acknowledgments ?? new List<Acknowledgment>();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error loading acknowledgments");
            return new List<Acknowledgment>();
        }
    }

    private void CreateDefaultConfig()
    {
        var defaultConfig = new
        {
            manifests = new[]
            {
                new { time = "07:00", carriers = new[] { "Australia Post Metro", "EParcel Express", "EParcel Postplus" } },
                new { time = "11:00", carriers = new[] { "AUP International for NZ", "Australia Post Metro", "EParcel Postplus" } },
                new { time = "12:30", carriers = new[] { "EParcel Express" } },
                new { time = "13:45", carriers = new[] { "NZ Post DPK International", "AUP Oversize Parcel", "DHL Express" } },
                new { time = "14:30", carriers = new[] { "AUP Oversize Parcel", "DHL Express" } },
                new { time = "15:30", carriers = new[] { "Keep at plant", "Toll Api", "Toll Priority" } },
                new { time = "16:00", carriers = new[] { "AUP International Zone 3", "Australia Post Metro", "EParcel Postplus" } }
            }
        };

        var json = JsonConvert.SerializeObject(defaultConfig, Formatting.Indented);
        File.WriteAllText(_configPath, json);

        _logger.LogInformation("Created default config file");
    }
}
