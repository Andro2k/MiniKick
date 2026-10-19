[CmdletBinding()]
param(
    [switch]$Silent
)

$ErrorActionPreference = 'Stop'
$repository = 'Andro2k/MiniKick'
$apiUri = "https://api.github.com/repos/$repository/releases/latest"
$headers = @{
    Accept = 'application/vnd.github+json'
    'User-Agent' = 'MiniKick-Installer'
    'X-GitHub-Api-Version' = '2022-11-28'
}
$temporaryDirectory = Join-Path ([System.IO.Path]::GetTempPath()) ("MiniKick-Install-" + [guid]::NewGuid().ToString('N'))

try {
    $release = Invoke-RestMethod -Uri $apiUri -Headers $headers
    $version = ([string]$release.tag_name) -replace '^v', ''
    if ($version -notmatch '^\d+\.\d+\.\d+(?:\.\d+)?$') {
        throw "La release de MiniKick tiene una etiqueta de versión no válida: $($release.tag_name)"
    }

    $expectedAssetName = "MiniKick_Installer_v$version.exe"
    $installerAssets = @($release.assets | Where-Object { $_.name -ceq $expectedAssetName })
    if ($installerAssets.Count -ne 1) {
        throw "La release $($release.tag_name) debe contener exactamente el archivo $expectedAssetName."
    }

    $installerAsset = $installerAssets[0]
    if ($installerAsset.browser_download_url -notmatch '^https://github\.com/Andro2k/MiniKick/releases/download/') {
        throw 'La URL de descarga del instalador no pertenece al repositorio oficial de MiniKick.'
    }
    if ([string]$installerAsset.digest -notmatch '^sha256:([0-9a-fA-F]{64})$') {
        throw "GitHub no proporciona un SHA-256 verificable para $expectedAssetName. No se ejecutó ningún archivo."
    }
    $expectedHash = $Matches[1].ToUpperInvariant()

    New-Item -ItemType Directory -Path $temporaryDirectory | Out-Null
    $installerPath = Join-Path $temporaryDirectory $expectedAssetName
    Invoke-WebRequest -Uri $installerAsset.browser_download_url -OutFile $installerPath -UseBasicParsing

    $actualHash = (Get-FileHash -Path $installerPath -Algorithm SHA256).Hash
    if ($actualHash -ne $expectedHash) {
        throw "La verificación SHA-256 falló para $expectedAssetName. No se ejecutó ningún archivo."
    }

    Write-Host "MiniKick $version descargado y verificado. Iniciando instalador..."
    $installerArguments = @()
    if ($Silent) {
        $installerArguments = @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-')
    }

    $process = Start-Process -FilePath $installerPath -ArgumentList $installerArguments -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        throw "El instalador terminó con el código $($process.ExitCode)."
    }
    Write-Host 'Instalación de MiniKick completada.'
}
catch {
    throw "No se pudo instalar MiniKick: $($_.Exception.Message)"
}
finally {
    if (Test-Path -LiteralPath $temporaryDirectory) {
        Remove-Item -LiteralPath $temporaryDirectory -Recurse -Force
    }
}
