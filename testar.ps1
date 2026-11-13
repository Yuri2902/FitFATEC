# Testes automatizados do FitFATEC. Os testes nao acessam o banco real.
$ErrorActionPreference = 'Stop'
$Backend = Join-Path $PSScriptRoot 'ia_academia'
$PythonVenv = Join-Path $Backend '.venv/Scripts/python.exe'
if (-not (Test-Path $PythonVenv)) {
    Write-Host 'Python do projeto nao encontrado. Execute .\configurar.ps1 antes dos testes.' -ForegroundColor Red
    return
}
Push-Location $Backend
try {
    Write-Host 'Executando testes do FitFATEC...' -ForegroundColor Cyan
    & $PythonVenv -m unittest discover -s tests -p 'test_*.py' -v
    $Codigo = $LASTEXITCODE
    if ($Codigo -eq 0) {
        Write-Host 'TESTES APROVADOS (OK)' -ForegroundColor Green
    } else {
        Write-Host 'TESTES COM FALHAS: confira o resumo acima. Nao significa necessariamente que o Flask esteja indisponivel.' -ForegroundColor Red
    }
} finally { Pop-Location }
