using ManifestAlert.Application.Interfaces;
using ManifestAlert.Domain.Models;
using Microsoft.Extensions.Logging;

namespace ManifestAlert.Application.Services;

/// <summary>
/// Service for managing manifest operations
/// </summary>
public class ManifestService
{
    private readonly IManifestRepository _repository;
    private readonly ILogger<ManifestService> _logger;

    public ManifestService(IManifestRepository repository, ILogger<ManifestService> logger)
    {
        _repository = repository;
        _logger = logger;
    }

    /// <summary>
    /// Get today's manifests with acknowledgments applied
    /// </summary>
    public async Task<List<Manifest>> GetTodaysManifestsAsync()
    {
        try
        {
            var today = DateTime.Now.ToString("yyyy-MM-dd");
            var manifests = await _repository.LoadManifestConfigAsync();
            var acknowledgments = await _repository.GetAcknowledgmentsAsync(today);

            // Apply acknowledgments to manifests
            foreach (var manifest in manifests)
            {
                manifest.Date = today;

                foreach (var carrier in manifest.Carriers)
                {
                    var ack = acknowledgments.FirstOrDefault(a =>
                        a.IsSameCarrier(today, manifest.Time, carrier.Name));

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
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting today's manifests");
            throw;
        }
    }

    /// <summary>
    /// Acknowledge a carrier
    /// </summary>
    public async Task AcknowledgeCarrierAsync(
        string date,
        string manifestTime,
        string carrierName,
        string user,
        string? reason = null,
        string? customerMessage = null)
    {
        try
        {
            var acknowledgment = new Acknowledgment(date, manifestTime, carrierName, user, reason, customerMessage);
            await _repository.SaveAcknowledgmentAsync(acknowledgment);

            _logger.LogInformation("Carrier {Carrier} acknowledged by {User}", carrierName, user);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error acknowledging carrier {Carrier}", carrierName);
            throw;
        }
    }

    /// <summary>
    /// Undo carrier acknowledgment
    /// </summary>
    public async Task UndoAcknowledgmentAsync(string date, string manifestTime, string carrierName)
    {
        try
        {
            await _repository.RemoveAcknowledgmentAsync(date, manifestTime, carrierName);
            _logger.LogInformation("Acknowledgment undone for carrier {Carrier}", carrierName);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error undoing acknowledgment for {Carrier}", carrierName);
            throw;
        }
    }

    /// <summary>
    /// Update customer message for a carrier
    /// </summary>
    public async Task UpdateCustomerMessageAsync(
        string date,
        string manifestTime,
        string carrierName,
        string? message)
    {
        try
        {
            await _repository.UpdateCustomerMessageAsync(date, manifestTime, carrierName, message);
            _logger.LogInformation("Customer message updated for carrier {Carrier}", carrierName);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating customer message for {Carrier}", carrierName);
            throw;
        }
    }

    /// <summary>
    /// Acknowledge all carriers in a manifest
    /// </summary>
    public async Task AcknowledgeAllCarriersAsync(
        string date,
        string manifestTime,
        List<string> carrierNames,
        string user,
        string? reason = null)
    {
        try
        {
            foreach (var carrierName in carrierNames)
            {
                await AcknowledgeCarrierAsync(date, manifestTime, carrierName, user, reason);
            }

            _logger.LogInformation("All carriers acknowledged for manifest {Time}", manifestTime);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error acknowledging all carriers for manifest {Time}", manifestTime);
            throw;
        }
    }
}
