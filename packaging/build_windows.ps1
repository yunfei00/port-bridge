param([ValidateSet("Both","Onedir","Onefile")][string]$Mode="Both",[switch]$SkipInstall)
$ErrorActionPreference="Stop";$Root=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path;Set-Location $Root;$Venv=Join-Path $Root ".venv-port-bridge-build";$Req=Join-Path $Root "packaging\requirements-windows-build.txt"
if($SkipInstall){$Python=(Get-Command python).Source}else{Remove-Item -Recurse -Force $Venv -ErrorAction SilentlyContinue;python -m venv $Venv;$Python=Join-Path $Venv "Scripts\python.exe";& $Python -m pip install --upgrade pip;& $Python -m pip install -r $Req;& $Python -m pip install -e .}
$env:PYTHONPATH=Join-Path $Root "src"
function Build([string]$kind,[string]$spec){$dist="dist\modern\$kind";$work="build\modern\$kind";Remove-Item -Recurse -Force $dist,$work -ErrorAction SilentlyContinue;& $Python -m PyInstaller --noconfirm --clean --distpath $dist --workpath $work $spec;if($LASTEXITCODE -ne 0){throw "$kind build failed"}}
& $Python -m port_bridge.modern_entry --diagnostics
if($Mode -in @("Both","Onedir")){Build "onedir" "packaging\port_bridge.spec"};if($Mode -in @("Both","Onefile")){Build "onefile" "packaging\port_bridge_onefile.spec"}
Write-Host "PortBridge Windows build completed."
