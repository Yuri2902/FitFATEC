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
    Write-Host 'Criado .env — preencha DB_PASSWORD e, para IA online, GEMINI_API_KEY. A SECRET_KEY foi gerada.' -ForegroundColor Yellow
}

# Adiciona novas opcoes apenas se estiverem ausentes. Nao sobrescreve um .env existente.
$ConteudoEnv = [System.IO.File]::ReadAllText($envPath)
$PadroesGemini = [ordered]@{
    GEMINI_MAX_ATTEMPTS = '1'
    GEMINI_TIMEOUT_MS   = '15000'
}
$LinhasNovas = @()
foreach ($Nome in $PadroesGemini.Keys) {
    if ($ConteudoEnv -notmatch "(?m)^\s*$Nome\s*=") {
        $LinhasNovas += "$Nome=$($PadroesGemini[$Nome])"
    }
}
if ($LinhasNovas.Count -gt 0) {
    $QuebraLinha = if ($ConteudoEnv.Contains("`r`n")) { "`r`n" } else { "`n" }
    $Separador = if ($ConteudoEnv.Length -gt 0 -and -not $ConteudoEnv.EndsWith("`n")) { $QuebraLinha } else { '' }
    $Adicao = $Separador + ($LinhasNovas -join $QuebraLinha) + $QuebraLinha
    [System.IO.File]::AppendAllText($envPath, $Adicao, [System.Text.UTF8Encoding]::new($false))
    Write-Host 'Opcoes Gemini ausentes foram adicionadas ao .env (sem sobrescrever as existentes).' -ForegroundColor Cyan
}
Write-Host 'Gemini: padrao de 1 tentativa e limite de 15 segundos. Ajustavel no .env.' -ForegroundColor Cyan
Write-Host 'Dependencias prontas. Confirme banco SQL e .env e execute .\iniciar.ps1' -ForegroundColor Green
