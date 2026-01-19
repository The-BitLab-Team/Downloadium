$ErrorActionPreference = 'Stop'

# Run Downloadium (single_file_project) from repo root.
$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$VenvPython = Join-Path $RepoDir '.venv\Scripts\python.exe'
$MainPy = Join-Path $RepoDir 'single_file_project\main.py'

try {
    if (Test-Path $VenvPython) {
        & $VenvPython $MainPy
    } else {
        & python $MainPy
    }
}
catch {
    Write-Host "" 
    Write-Host "Falha ao iniciar o Downloadium." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor DarkGray
    Write-Host "" 
    Write-Host "Dica: instale dependencias com: pip install -r single_file_project\requirements.txt" -ForegroundColor Yellow
    Read-Host "Pressione Enter para sair"
    exit 1
}
