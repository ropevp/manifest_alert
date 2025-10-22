using ManifestAlert.Application.Interfaces;
using ManifestAlert.Application.Services;
using ManifestAlert.Infrastructure.Repositories;
using ManifestAlert.Infrastructure.Services;
using ManifestAlert.WPF.ViewModels;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using System.Windows;

namespace ManifestAlert.WPF;

public partial class App : Application
{
    private IServiceProvider? _serviceProvider;

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        // Setup dependency injection
        var services = new ServiceCollection();
        ConfigureServices(services);
        _serviceProvider = services.BuildServiceProvider();

        // Create and show main window
        var mainWindow = _serviceProvider.GetRequiredService<MainWindow>();
        mainWindow.Show();
    }

    private void ConfigureServices(IServiceCollection services)
    {
        // Get data folder path
        var dataFolder = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "ManifestAlert");

        // Logging
        services.AddLogging(builder =>
        {
            builder.AddDebug();
            builder.AddConsole();
            builder.SetMinimumLevel(LogLevel.Information);
        });

        // Repositories
        services.AddSingleton<IManifestRepository>(sp =>
            new JsonManifestRepository(dataFolder, sp.GetRequiredService<ILogger<JsonManifestRepository>>()));

        services.AddSingleton<IMuteRepository>(sp =>
            new JsonMuteRepository(dataFolder, sp.GetRequiredService<ILogger<JsonMuteRepository>>()));

        // Application Services
        services.AddSingleton<AlertService>();
        services.AddSingleton<ManifestService>();
        services.AddSingleton<MuteService>();
        services.AddSingleton<VoiceService>();

        // ViewModels
        services.AddSingleton<MainViewModel>();

        // Views
        services.AddSingleton<MainWindow>();
    }

    protected override void OnExit(ExitEventArgs e)
    {
        if (_serviceProvider is IDisposable disposable)
        {
            disposable.Dispose();
        }

        base.OnExit(e);
    }
}
