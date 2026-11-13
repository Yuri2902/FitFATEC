# Executar na raiz do projeto. Deixe esta janela aberta enquanto usa o site.
$ErrorActionPreference = 'Stop'
$Backend = Join-Path $PSScriptRoot 'ia_academia'
$PythonVenv = Join-Path $Backend '.venv/Scripts/python.exe'
if (-not (Test-Path $PythonVenv)) {
    Write-Host 'Ambiente virtual nao encontrado. Execute .\configurar.ps1.' -ForegroundColor Red
    return
}
if (-not (Test-Path (Join-Path $PSScriptRoot '.env'))) {
    Write-Host 'Arquivo .env ausente na raiz. Crie-o a partir do .env.example.' -ForegroundColor Red
    return
}
Write-Host 'Iniciando o FitFATEC. Mantenha este terminal aberto.' -ForegroundColor Cyan
Write-Host 'Quando aparecer Running on http://127.0.0.1:5000, abra http://localhost:5000' -ForegroundColor Cyan
Push-Location $Backend
try {
    & $PythonVenv 'servidor.py'
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Falha ao iniciar Flask: copie o erro de cima. Os testes e o servidor sao etapas diferentes.' -ForegroundColor Red
    }
} finally { Pop-Location }
