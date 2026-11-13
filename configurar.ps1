# Instala dependências e prepara os arquivos locais. Executar NA RAIZ do projeto.
$ErrorActionPreference = 'Stop'
$Raiz = $PSScriptRoot
$Backend = Join-Path $Raiz 'ia_academia'
$PythonVenv = Join-Path $Backend '.venv/Scripts/python.exe'
if (-not (Test-Path $PythonVenv)) {
    Write-Host 'Criando ambiente virtual...' -ForegroundColor Cyan
    python -m venv (Join-Path $Backend '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Nao foi possivel criar o venv. Verifique se Python >= 3.10 esta instalado.' }
}
& $PythonVenv -m pip install -r (Join-Path $Backend 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Falha instalando dependencias. Verifique internet/Python.' }
$envPath = Join-Path $Raiz '.env'
if (-not (Test-Path $envPath)) {
    Copy-Item (Join-Path $Raiz '.env.example') $envPath
    $ChaveNova = (& $PythonVenv -c 'import secrets; print(secrets.token_hex(32))').Trim()
    $Conteudo = Get-Content $envPath -Raw
    $Conteudo = $Conteudo.Replace('SECRET_KEY=COLOQUE_CHAVE_ALEATORIA_AQUI', 'SECRET_KEY=' + $ChaveNova)
    [System.IO.File]::WriteAllText($envPath, $Conteudo, [System.Text.UTF8Encoding]::new($false))
    Write-Host 'Criado .env — abra e defina DB_PASSWORD e SECRET_KEY antes de executar o servidor.' -ForegroundColor Yellow
}
$Modelo = Join-Path $Backend 'modelo_evasao.pkl'
if (-not (Test-Path $Modelo)) {
    Write-Host 'Gerando modelo demonstrativo de risco com dados sinteticos...' -ForegroundColor Cyan
    & $PythonVenv (Join-Path $Backend 'gerar_dados.py')
    if ($LASTEXITCODE -ne 0) { throw 'Falha gerando dados sinteticos.' }
    & $PythonVenv (Join-Path $Backend 'treinar_modelo.py')
    if ($LASTEXITCODE -ne 0) { throw 'Falha treinando modelo.' }
}
Write-Host 'Dependencias prontas. Confirme banco SQL e .env e execute .\iniciar.ps1' -ForegroundColor Green
