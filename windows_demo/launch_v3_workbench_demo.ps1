param(
    [string]$BaseUrl = "http://127.0.0.1:18080",
    [ValidateSet("msedge", "chrome", "default")]
    [string]$Browser = "msedge",
    [switch]$NoAppMode,
    [switch]$SkipServiceStartup,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-NormalizedBaseUrl {
    param([string]$RawBaseUrl)

    $resolved = ""
    if ($null -ne $RawBaseUrl) {
        $resolved = $RawBaseUrl.Trim()
    }
    if ([string]::IsNullOrWhiteSpace($resolved)) {
        $resolved = "http://127.0.0.1:18080"
    }
    return $resolved.TrimEnd('/')
}

function Test-TargetPortListening {
    param(
        [string]$HostName,
        [int]$Port
    )

    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $asyncResult = $client.BeginConnect($HostName, $Port, $null, $null)
        $connected = $asyncResult.AsyncWaitHandle.WaitOne(800)
        if (-not $connected) {
            return $false
        }
        $client.EndConnect($asyncResult)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Dispose()
    }
}

function Wait-WorkbenchReady {
    param([string]$EntryUrl)

    $index = 0
    while ($index -lt 20) {
        try {
            Invoke-WebRequest -Uri $EntryUrl -UseBasicParsing -TimeoutSec 2 | Out-Null
            return $true
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
        $index += 1
    }
    return $false
}

function Get-BrowserLaunchInfo {
    param(
        [string]$TargetBrowser,
        [string]$EntryUrl,
        [bool]$UseAppMode,
        [bool]$ResolveExecutable
    )

    if ($TargetBrowser -eq "default") {
        return @{
            file_path = $EntryUrl
            argument_list = @()
            command_text = $EntryUrl
            browser_mode = "browser"
        }
    }

    $resolvedFilePath = $TargetBrowser
    $resolvedCommandName = $TargetBrowser
    if ($ResolveExecutable) {
        $browserCommand = Get-Command $TargetBrowser -ErrorAction SilentlyContinue
        if ($null -eq $browserCommand) {
            throw "Browser command not found: $TargetBrowser"
        }
        $resolvedFilePath = $browserCommand.Source
        $resolvedCommandName = $browserCommand.Name
    }

    $argumentList = @()
    if ($UseAppMode) {
        $argumentList += "--app=$EntryUrl"
        $browserMode = "app"
    }
    else {
        $argumentList += $EntryUrl
        $browserMode = "browser"
    }

    return @{
        file_path = $resolvedFilePath
        argument_list = $argumentList
        command_text = "$resolvedCommandName $($argumentList -join ' ')"
        browser_mode = $browserMode
    }
}

$normalizedBaseUrl = Get-NormalizedBaseUrl -RawBaseUrl $BaseUrl
$baseUri = [System.Uri]$normalizedBaseUrl
$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $repoRoot ".venv_service\Scripts\python.exe"
$managePath = Join-Path $repoRoot "manage.py"
$entryUrl = "$normalizedBaseUrl/ui/v3/workbench/"
$useAppMode = -not $NoAppMode.IsPresent
$serverHostPort = if ($baseUri.IsDefaultPort) { $baseUri.Host } else { "$($baseUri.Host):$($baseUri.Port)" }
$serviceCommand = "& `"$pythonPath`" `"$managePath`" runserver $serverHostPort"
$launchInfo = Get-BrowserLaunchInfo -TargetBrowser $Browser -EntryUrl $entryUrl -UseAppMode:$useAppMode -ResolveExecutable:$false
$serviceStartupMode = if ($SkipServiceStartup.IsPresent) { "skipped" } else { "auto_if_needed" }

if ($DryRun.IsPresent) {
    [ordered]@{
        launch_mode = "browser_first"
        tauri_priority = $true
        browser = $Browser
        browser_mode = $launchInfo.browser_mode
        base_url = $normalizedBaseUrl
        entry_url = $entryUrl
        launcher_script = $PSCommandPath
        service_command = $serviceCommand
        service_startup_mode = $serviceStartupMode
        browser_command = $launchInfo.command_text
    } | ConvertTo-Json -Compress
    return
}

if (-not (Test-Path $pythonPath)) {
    throw "Python runtime not found: $pythonPath"
}

if (-not (Test-Path $managePath)) {
    throw "manage.py not found: $managePath"
}

if (-not $SkipServiceStartup.IsPresent) {
    $isListening = Test-TargetPortListening -HostName $baseUri.Host -Port $baseUri.Port
    if (-not $isListening) {
        Start-Process -FilePath $pythonPath -ArgumentList @($managePath, "runserver", $serverHostPort) -WorkingDirectory $repoRoot -WindowStyle Minimized | Out-Null
        $ready = Wait-WorkbenchReady -EntryUrl $entryUrl
        if (-not $ready) {
            throw "Workbench entry was not ready before timeout: $entryUrl"
        }
    }
}

if ($Browser -ne "default") {
    $launchInfo = Get-BrowserLaunchInfo -TargetBrowser $Browser -EntryUrl $entryUrl -UseAppMode:$useAppMode -ResolveExecutable:$true
}

if ($Browser -eq "default") {
    Start-Process -FilePath $entryUrl | Out-Null
}
else {
    Start-Process -FilePath $launchInfo.file_path -ArgumentList $launchInfo.argument_list | Out-Null
}
