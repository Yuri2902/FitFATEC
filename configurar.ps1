# Instala dependências e prepara os arquivos locais. Executar NA RAIZ do projeto.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Raiz = $PSScriptRoot
$Backend = Join-Path $Raiz 'ia_academia'
$PythonVenv = Join-Path $Backend '.venv/Scripts/python.exe'
if (-not (Test-Path $PythonVenv)) {
    Write-Host 'Criando ambiente virtual...' -ForegroundColor Cyan
    python -m venv (Join-Path $Backend '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Nao foi possivel criar o venv. Verifique se Python >= 3.10 esta instalado.' }
}
# Kokoro ONNX requer Python >=3.10 e <3.14.
$SaidaVersaoPython = & $PythonVenv -c 'import sys; print(str(sys.version_info.major) + chr(46) + str(sys.version_info.minor))'
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace(($SaidaVersaoPython -join '').Trim())) {
    throw 'Nao foi possivel identificar a versao do Python no ambiente virtual. Verifique a instalacao do Python e execute configurar.ps1 novamente.'
}
$VersaoPython = ($SaidaVersaoPython -join '').Trim()
if ([version]$VersaoPython -lt [version]'3.10' -or [version]$VersaoPython -ge [version]'3.14') {
    throw "A voz neural Kokoro requer Python 3.10 a 3.13. Versao encontrada: $VersaoPython. Instale Python 3.10 a 3.13 e recrie ia_academia/.venv."
}
& $PythonVenv -m pip install -r (Join-Path $Backend 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Falha instalando dependencias. Verifique internet/Python.' }

# Baixa uma vez os pesos da voz. Depois disso, a síntese funciona sem internet.
$PastaVoz = Join-Path $Backend 'modelos/kiara_voz'
New-Item -ItemType Directory -Force -Path $PastaVoz | Out-Null
$ArquivosVoz = @(
    @{
        Nome = 'kokoro-v1.0.int8.onnx'
        Url = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.int8.onnx'
        TamanhoMinimo = 100MB
    },
    @{
        Nome = 'voices-v1.0.bin'
        Url = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin'
        TamanhoMinimo = 20MB
    }
)
foreach ($Arquivo in $ArquivosVoz) {
    $Destino = Join-Path $PastaVoz $Arquivo.Nome
    if ((Test-Path $Destino) -and (Get-Item $Destino).Length -ge $Arquivo.TamanhoMinimo) {
        Write-Host "Modelo de voz ja encontrado: $($Arquivo.Nome)" -ForegroundColor Green
        continue
    }
    $Temporario = "$Destino.download"
    if (Test-Path $Temporario) { Remove-Item $Temporario -Force }
    Write-Host "Baixando $($Arquivo.Nome). Isso pode levar alguns minutos..." -ForegroundColor Cyan
    try {
        Invoke-WebRequest -Uri $Arquivo.Url -OutFile $Temporario -UseBasicParsing
        if (-not (Test-Path $Temporario) -or (Get-Item $Temporario).Length -lt $Arquivo.TamanhoMinimo) {
            throw "Download incompleto de $($Arquivo.Nome)."
        }
        Move-Item -Path $Temporario -Destination $Destino -Force
    } catch {
        if (Test-Path $Temporario) { Remove-Item $Temporario -Force }
        throw "Nao foi possivel baixar $($Arquivo.Nome). Verifique a internet e execute configurar.ps1 novamente. Detalhe: $($_.Exception.Message)"
    }
}

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
Write-Host 'Voz neural local da Kiara pronta (Kokoro / pf_dora). A primeira fala carrega o modelo na memoria.' -ForegroundColor Green
Write-Host 'Dependencias prontas. Confirme banco SQL e .env e execute .\iniciar.ps1' -ForegroundColor Green
