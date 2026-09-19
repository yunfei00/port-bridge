param([ValidateSet("Both","Onedir","Onefile")][string]$Mode="Both",[switch]$SkipInstall)
$ErrorActionPreference="Stop";$Root=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path;Set-Location $Root
$Venv=Join-Path $Root ".venv-port-bridge-fsw-legacy";$Req=Join-Path $Root "packaging\requirements-fsw-legacy.txt"
function Get-Python38 {
 try { & py -3.8 -c "import sys; assert sys.version_info[:2]==(3,8)" *> $null; if($LASTEXITCODE -eq 0){return @("py","-3.8")} } catch {}
 try { $v=& python -c "import sys; print('%d.%d'%sys.version_info[:2])";if($v.Trim() -eq "3.8"){return @("python")} } catch {}
 throw "Python 3.8.x x64 is required for the legacy build."
}
if($SkipInstall){$Python=(Get-Command python).Source}else{
 Remove-Item -Recurse -Force $Venv -ErrorAction SilentlyContinue;$b=Get-Python38
 if($b.Count -eq 2){& $b[0] $b[1] -m venv $Venv}else{& $b[0] -m venv $Venv}
 $Python=Join-Path $Venv "Scripts\python.exe";& $Python -m pip install --upgrade "pip<25";& $Python -m pip install -r $Req
}
$info=& $Python -c "import platform,struct;print(platform.python_version());print(struct.calcsize('P')*8)"
if(-not $info[0].StartsWith("3.8.")){throw "Python 3.8.x required"};if($info[1] -ne "64"){throw "64-bit Python required"}
$diag=Join-Path $Root "build\legacy-source-diagnostics.txt";New-Item -ItemType Directory -Force -Path (Split-Path $diag)|Out-Null
& $Python -m port_bridge.legacy --diagnostics-file $diag
if($LASTEXITCODE -ne 0){throw "Source diagnostics failed"}
function Build([string]$kind,[string]$spec){
 $dist="dist\legacy\$kind";$work="build\legacy\$kind";Remove-Item -Recurse -Force $dist,$work -ErrorAction SilentlyContinue
 & $Python -m PyInstaller --noconfirm --clean --distpath $dist --workpath $work $spec
 if($LASTEXITCODE -ne 0){throw "$kind build failed"}
}
$env:PYTHONPATH=Join-Path $Root "src"
if($Mode -in @("Both","Onedir")){Build "onedir" "packaging\port_bridge_fsw_legacy.spec"}
if($Mode -in @("Both","Onefile")){Build "onefile" "packaging\port_bridge_fsw_legacy_onefile.spec"}
Write-Host "PortBridge Legacy build completed."
