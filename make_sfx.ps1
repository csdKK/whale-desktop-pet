$ErrorActionPreference = "Stop"

$workDir = $PSScriptRoot
$bundleDir = Join-Path $workDir "installer_bundle"
$stubCs = Join-Path $workDir "_sfx_stub.cs"
$outExe = Join-Path $workDir "WhalePetInstaller.exe"
$zipPath = Join-Path $workDir "_bundle.zip"

Write-Host "Step 1/3: Creating ZIP archive..."
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($bundleDir, $zipPath, [System.IO.Compression.CompressionLevel]::Optimal, $false)
$zipSize = (Get-Item $zipPath).Length / 1MB
Write-Host ("ZIP size: {0:N1} MB" -f $zipSize)

Write-Host "Step 2/3: Compiling SFX stub..."
$stubExe = Join-Path $workDir "_sfx_stub.exe"
if (Test-Path $stubExe) { Remove-Item $stubExe -Force }

$code = Get-Content $stubCs -Raw
$refs = @("System.dll", "System.IO.Compression.FileSystem.dll", "System.Windows.Forms.dll")
Add-Type -TypeDefinition $code -OutputAssembly $stubExe -ReferencedAssemblies $refs -OutputType WindowsApplication
Write-Host "Stub compiled"

Write-Host "Step 3/3: Embedding ZIP into EXE..."
$marker = [System.Text.Encoding]::ASCII.GetBytes("WHALEPET_ZIP_DATA_START")
$stubBytes = [System.IO.File]::ReadAllBytes($stubExe)
$zipBytes = [System.IO.File]::ReadAllBytes($zipPath)

$fs = [System.IO.File]::Open($outExe, [System.IO.FileMode]::Create)
$fs.Write($stubBytes, 0, $stubBytes.Length)
$fs.Write($marker, 0, $marker.Length)
$fs.Write($zipBytes, 0, $zipBytes.Length)
$fs.Close()

$exeSize = (Get-Item $outExe).Length / 1MB
Write-Host ""
Write-Host "========================================"
Write-Host "SUCCESS: WhalePetInstaller.exe"
Write-Host ("Size: {0:N1} MB ({1:N2} GB)" -f $exeSize, ($exeSize / 1024))
Write-Host "========================================"

Remove-Item $zipPath -Force
Remove-Item $stubExe -Force
Write-Host "Temp files cleaned"