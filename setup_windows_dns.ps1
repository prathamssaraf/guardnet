# GuardNet Windows DNS Setup Script
# Run as Administrator

param(
    [switch]$Enable,
    [switch]$Disable,
    [string]$GuardNetIP = "127.0.0.1"
)

Write-Host "GuardNet DNS Ad Blocker Setup" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

function Get-ActiveNetworkAdapter {
    return Get-NetAdapter | Where-Object { $_.Status -eq "Up" -and $_.MediaType -eq "802.3" -or $_.MediaType -eq "Native 802.11" } | Select-Object -First 1
}

function Enable-GuardNet {
    Write-Host "Setting up GuardNet as your DNS server..." -ForegroundColor Yellow
    
    $adapter = Get-ActiveNetworkAdapter
    if (-not $adapter) {
        Write-Host "ERROR: No active network adapter found!" -ForegroundColor Red
        return
    }
    
    Write-Host "Using network adapter: $($adapter.Name)" -ForegroundColor Cyan
    
    # Set GuardNet as primary DNS, Google as secondary
    try {
        Set-DnsClientServerAddress -InterfaceIndex $adapter.InterfaceIndex -ServerAddresses @($GuardNetIP, "8.8.8.8")
        Write-Host "✓ GuardNet DNS configured successfully!" -ForegroundColor Green
        Write-Host "  Primary DNS: $GuardNetIP (GuardNet)" -ForegroundColor White
        Write-Host "  Secondary DNS: 8.8.8.8 (Google)" -ForegroundColor White
        
        # Test DNS resolution
        Write-Host "`nTesting DNS resolution..." -ForegroundColor Yellow
        $testResult = Test-NetConnection -ComputerName "google.com" -Port 80 -InformationLevel Quiet
        if ($testResult) {
            Write-Host "✓ DNS resolution working!" -ForegroundColor Green
        } else {
            Write-Host "⚠ DNS test failed - please check GuardNet is running" -ForegroundColor Yellow
        }
        
        Write-Host "`nGuardNet is now blocking ads system-wide!" -ForegroundColor Green
        Write-Host "🛡️  All browsers and applications will use ad-free DNS" -ForegroundColor Cyan
        
    } catch {
        Write-Host "ERROR: Failed to set DNS - $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Disable-GuardNet {
    Write-Host "Restoring automatic DNS settings..." -ForegroundColor Yellow
    
    $adapter = Get-ActiveNetworkAdapter
    if (-not $adapter) {
        Write-Host "ERROR: No active network adapter found!" -ForegroundColor Red
        return
    }
    
    try {
        Set-DnsClientServerAddress -InterfaceIndex $adapter.InterfaceIndex -ResetServerAddresses
        Write-Host "✓ DNS settings restored to automatic" -ForegroundColor Green
        Write-Host "GuardNet ad blocking disabled" -ForegroundColor Yellow
        
    } catch {
        Write-Host "ERROR: Failed to reset DNS - $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Show-Status {
    Write-Host "`nCurrent DNS Configuration:" -ForegroundColor Cyan
    Write-Host "=========================" -ForegroundColor Cyan
    
    $adapter = Get-ActiveNetworkAdapter
    if ($adapter) {
        $dnsServers = Get-DnsClientServerAddress -InterfaceIndex $adapter.InterfaceIndex -AddressFamily IPv4
        Write-Host "Network Adapter: $($adapter.Name)" -ForegroundColor White
        Write-Host "DNS Servers:" -ForegroundColor White
        
        foreach ($server in $dnsServers.ServerAddresses) {
            if ($server -eq $GuardNetIP) {
                Write-Host "  🛡️  $server (GuardNet - Ad Blocking Active)" -ForegroundColor Green
            } elseif ($server -eq "8.8.8.8" -or $server -eq "8.8.4.4") {
                Write-Host "  📡 $server (Google DNS)" -ForegroundColor Cyan
            } elseif ($server -eq "1.1.1.1" -or $server -eq "1.0.0.1") {
                Write-Host "  ⚡ $server (Cloudflare DNS)" -ForegroundColor Blue
            } else {
                Write-Host "  📡 $server" -ForegroundColor White
            }
        }
    }
}

# Main execution
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

if ($Enable) {
    Enable-GuardNet
} elseif ($Disable) {
    Disable-GuardNet
} else {
    Write-Host "Usage:" -ForegroundColor White
    Write-Host "  .\setup_windows_dns.ps1 -Enable    # Enable GuardNet ad blocking" -ForegroundColor Cyan
    Write-Host "  .\setup_windows_dns.ps1 -Disable   # Disable GuardNet ad blocking" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Make sure GuardNet is running first:" -ForegroundColor Yellow
    Write-Host "  docker-compose up -d" -ForegroundColor White
}

Show-Status

Write-Host "`nFor more info, see: PERSONAL_SETUP_GUIDE.md" -ForegroundColor Gray