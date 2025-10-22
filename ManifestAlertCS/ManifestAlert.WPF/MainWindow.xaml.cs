using ManifestAlert.WPF.ViewModels;
using System.Windows;

namespace ManifestAlert.WPF;

public partial class MainWindow : Window
{
    public MainWindow(MainViewModel viewModel)
    {
        InitializeComponent();
        DataContext = viewModel;
    }
}
