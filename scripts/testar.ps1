<#
.SYNOPSIS
    Sobe o CalcSISTEC pronto para testar, com login administrativo já configurado.

.DESCRIPTION
    Um comando só: prepara as credenciais de teste, sobe o app preso a 127.0.0.1
    e abre o navegador na tela de login. Por padrão aponta para o Sistec REAL
    (https://sistec.mec.gov.br); com -Simulado, sobe junto o Sistec de mentira
    (scripts/sistec_simulado.py) e aponta para ele.

    As credenciais ficam em `.env` na raiz do CalcSISTEC, que o .gitignore já
    ignora — nunca são versionadas. Na primeira execução o arquivo é criado com
    uma senha aleatória; depois disso é sempre a mesma, e o script a mostra no
    terminal.

    O app escuta só em 127.0.0.1 (diferente do `run.py`, que usa 0.0.0.0 para
    produção): com senha fixa de teste, ninguém na rede deve alcançar a área
    administrativa.

.PARAMETER Simulado
    Sobe o Sistec simulado na porta 8051 e aponta o CalcSISTEC para ele.
    Use para testar sem tocar no Sistec real.

.PARAMETER Porta
    Porta do CalcSISTEC (padrão 8050).

.PARAMETER SemNavegador
    Não abre o navegador automaticamente.

.PARAMETER Destacado
    Sobe o app em um processo separado, com a saída e os erros em arquivo no
    diretório temporário, e devolve o controle assim que a porta responde —
    é o modo que qualquer agente (ou o comando /testar) usa. Para derrubar
    depois, rode com -Parar.

.PARAMETER Parar
    Encerra quem estiver escutando na porta e sai. Não sobe nada. Com
    -Simulado, encerra também o Sistec simulado da porta 8051.

.EXAMPLE
    .\scripts\testar.ps1
    Testa contra o Sistec real.

.EXAMPLE
    .\scripts\testar.ps1 -Simulado
    Testa contra o Sistec simulado, sem login gov.br.
#>
[CmdletBinding()]
param(
    [switch]$Simulado,
    [int]$Porta = 8050,
    [switch]$SemNavegador,
    [switch]$Destacado,
    [switch]$Parar
)

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

function Escrever-Passo($texto) { Write-Host "  $texto" -ForegroundColor Cyan }
function Escrever-Aviso($texto) { Write-Host "  $texto" -ForegroundColor Yellow }

function Encerrar-Processos($portas) {
    # Mata quem estiver escutando nessas portas. Devolve $true se matou alguém.
    $algum = $false
    foreach ($portaAlvo in $portas) {
        $escuta = Get-NetTCPConnection -LocalPort $portaAlvo -State Listen -ErrorAction SilentlyContinue
        if (-not $escuta) { continue }
        foreach ($processoAlvo in ($escuta.OwningProcess | Sort-Object -Unique)) {
            Stop-Process -Id $processoAlvo -Force -ErrorAction SilentlyContinue
            Escrever-Passo "Encerrado o processo $processoAlvo (porta $portaAlvo)."
            $algum = $true
        }
    }
    return $algum
}

if ($Parar) {
    # 1. Só derrubar: não confere dependências nem sobe nada.
    $portasAlvo = @($Porta)
    if ($Simulado) { $portasAlvo += 8051 }
    Write-Host ""
    if (-not (Encerrar-Processos $portasAlvo)) {
        Escrever-Aviso "Não havia nada no ar nas portas $($portasAlvo -join ', ')."
    }
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "=== CalcSISTEC: ambiente de teste ===" -ForegroundColor Green

# 1. Dependências ------------------------------------------------------------
Escrever-Passo "Conferindo dependências..."
# Duas armadilhas do Windows PowerShell 5.1 aqui:
# 1. here-string passado direto como argumento de comando nativo quebra o
#    parser, por isso ele vai antes para uma variável;
# 2. aspas dentro do trecho são colapsadas ao chegar no python (`print("")`
#    virava `print(")`), por isso o código abaixo não usa aspas nenhuma:
#    sucesso é não imprimir nada.
$codigoDependencias = @'
try:
    import dash, flask, pandas, openpyxl
except ImportError as exc:
    print(exc.name)
'@
$faltando = (python -c $codigoDependencias | Out-String).Trim()
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Não consegui executar o python. Ele está instalado e no PATH?" -ForegroundColor Red
    exit 1
}
if ($faltando) {
    Write-Host ""
    Write-Host "Falta a dependência '$faltando'. Rode uma vez:" -ForegroundColor Red
    Write-Host "    pip install -r requirements.txt"
    exit 1
}

# 2. Credenciais de teste (.env, fora do versionamento) ----------------------
$arquivoEnv = Join-Path $raiz ".env"
if (-not (Test-Path $arquivoEnv)) {
    Escrever-Passo "Primeira execução: criando credenciais de teste em .env"
    $senhaGerada = -join ((1..14) | ForEach-Object { [char[]]'abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789' | Get-Random })
    $segredoGerado = -join ((1..32) | ForEach-Object { [char[]]'abcdef0123456789' | Get-Random })
    @(
        "# Credenciais LOCAIS de teste do CalcSISTEC (nunca versionadas).",
        "# Apague este arquivo para gerar outras.",
        "ADMIN_EMAIL=teste@local.test",
        "ADMIN_SENHA=$senhaGerada",
        "FLASK_SECRET_KEY=$segredoGerado"
    ) | Set-Content -Path $arquivoEnv -Encoding UTF8
}

$config = @{}
Get-Content $arquivoEnv | ForEach-Object {
    if ($_ -match '^\s*([^#=]+?)\s*=\s*(.*)$') { $config[$Matches[1]] = $Matches[2] }
}
if (-not $config.ADMIN_EMAIL -or -not $config.ADMIN_SENHA) {
    Write-Host "O arquivo .env existe mas está sem ADMIN_EMAIL/ADMIN_SENHA. Apague-o e rode de novo." -ForegroundColor Red
    exit 1
}

$env:ADMIN_EMAIL = $config.ADMIN_EMAIL
$env:FLASK_SECRET_KEY = $config.FLASK_SECRET_KEY

# A senha vai ao python por variável de ambiente, nunca na linha de comando
# (linha de comando aparece na lista de processos da máquina).
$env:SENHA_TEMP = $config.ADMIN_SENHA
$env:ADMIN_PASSWORD_HASH = python -c "import os;from werkzeug.security import generate_password_hash as g;print(g(os.environ['SENHA_TEMP']))"
Remove-Item Env:\SENHA_TEMP
if (-not $env:ADMIN_PASSWORD_HASH) {
    Write-Host "Não consegui gerar o hash da senha de teste (werkzeug ausente?)." -ForegroundColor Red
    exit 1
}
$env:PYTHONIOENCODING = "utf-8"

# 3. Sistec: real ou simulado ------------------------------------------------
$trabalhoSimulado = $null
$processoSimulado = $null
if ($Simulado) {
    Remove-Item Env:\CALCSISTEC_SISTEC_BASE_URL -ErrorAction SilentlyContinue
    $env:CALCSISTEC_SISTEC_BASE_URL = "http://127.0.0.1:8051"
    $emUso = Get-NetTCPConnection -LocalPort 8051 -State Listen -ErrorAction SilentlyContinue
    if ($emUso) {
        Escrever-Aviso "Já havia algo escutando na porta 8051 — usando o que está no ar."
    } else {
        Escrever-Passo "Subindo o Sistec simulado na porta 8051..."
        if ($Destacado) {
            # Em -Destacado o simulado também solta o terminal: quem derruba os
            # dois depois é o -Parar, e não o fim deste processo.
            $env:SISTEC_SIM_LOGIN_AUTOMATICO = "1"
            $processoSimulado = Start-Process -FilePath "python" `
                -ArgumentList "scripts/sistec_simulado.py" -WindowStyle Hidden -PassThru `
                -RedirectStandardOutput (Join-Path $env:TEMP "calcsistec-simulado-8051.log") `
                -RedirectStandardError (Join-Path $env:TEMP "calcsistec-simulado-8051.err.log")
        } else {
            $trabalhoSimulado = Start-Job -ScriptBlock {
                param($pasta)
                Set-Location $pasta
                $env:SISTEC_SIM_LOGIN_AUTOMATICO = "1"
                python scripts/sistec_simulado.py
            } -ArgumentList $raiz
        }
        Start-Sleep -Seconds 2
    }
} else {
    Remove-Item Env:\CALCSISTEC_SISTEC_BASE_URL -ErrorAction SilentlyContinue
}

# 4. Porta livre -------------------------------------------------------------
$ocupada = Get-NetTCPConnection -LocalPort $Porta -State Listen -ErrorAction SilentlyContinue
if ($ocupada) {
    $pids = ($ocupada.OwningProcess | Sort-Object -Unique) -join ", "
    Write-Host ""
    Write-Host "A porta $Porta já está em uso (PID $pids) — provavelmente um CalcSISTEC antigo." -ForegroundColor Red
    Write-Host "Feche aquele terminal, ou rode: Stop-Process -Id $pids"
    # O simulado que este processo subiu não pode ficar órfão na 8051.
    if ($trabalhoSimulado) {
        Stop-Job $trabalhoSimulado -ErrorAction SilentlyContinue
        Remove-Job $trabalhoSimulado -ErrorAction SilentlyContinue
    }
    if ($processoSimulado) {
        Stop-Process -Id $processoSimulado.Id -Force -ErrorAction SilentlyContinue
    }
    exit 1
}

# 5. Resumo ------------------------------------------------------------------
$endereco = "http://localhost:$Porta"
Write-Host ""
Write-Host "  Entre em:  $endereco/admin/login" -ForegroundColor Green
Write-Host "  E-mail:    $($config.ADMIN_EMAIL)" -ForegroundColor Green
Write-Host "  Senha:     $($config.ADMIN_SENHA)" -ForegroundColor Green
Write-Host ""
if ($Simulado) {
    Escrever-Passo "Sistec: SIMULADO (http://127.0.0.1:8051) — sem login gov.br, sem dado real."
} else {
    Escrever-Passo "Sistec: REAL (https://sistec.mec.gov.br) — o login gov.br é seu, no seu navegador de sempre."
}
Escrever-Passo "Passo a passo completo: TESTAR.md"
Escrever-Passo "Para parar: Ctrl+C nesta janela."
Write-Host ""

if (-not $SemNavegador) {
    Start-Process "$endereco/admin/login"
}

# 6. App (127.0.0.1: senha de teste não pode ficar exposta na rede) ----------
# Sobe pelo run.py (e não por um app.run avulso) para o watchdog de execuções
# subir junto — uma execução pausada ou travada precisa expirar também aqui.
if ($Destacado) {
    # Modo de quem não pode ficar preso ao servidor (agentes, /testar): sobe
    # destacado, espera a porta responder e devolve o controle.
    $limite = 60
    $limitePedido = 0
    # Escape de teste: encurta a espera sem mudar o padrão de 60 s.
    if ([int]::TryParse($env:CALCSISTEC_TESTAR_TIMEOUT, [ref]$limitePedido) -and $limitePedido -gt 0) {
        $limite = $limitePedido
    }
    $logApp = Join-Path $env:TEMP "calcsistec-$Porta.log"
    $logErro = Join-Path $env:TEMP "calcsistec-$Porta.err.log"
    Escrever-Passo "Subindo o app destacado na porta $Porta (logs em $env:TEMP)..."
    $argumentos = "run.py --host 127.0.0.1 --port $Porta"
    $processo = Start-Process -FilePath "python" -ArgumentList $argumentos `
        -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $logApp -RedirectStandardError $logErro

    $acima = $false
    for ($segundo = 1; $segundo -le $limite; $segundo++) {
        Start-Sleep -Seconds 1
        if (Get-NetTCPConnection -LocalPort $Porta -State Listen -ErrorAction SilentlyContinue) {
            $acima = $true
            break
        }
        if ($processo.HasExited) { break }
    }

    if (-not $acima) {
        Stop-Process -Id $processo.Id -Force -ErrorAction SilentlyContinue
        if ($processoSimulado) { Stop-Process -Id $processoSimulado.Id -Force -ErrorAction SilentlyContinue }
        Write-Host ""
        Write-Host "O app não abriu a porta $Porta em $limite s." -ForegroundColor Red
        Write-Host "  Log:         $logApp"
        Write-Host "  Log de erro: $logErro"
        exit 1
    }

    Write-Host "  PID:         $($processo.Id)"
    Write-Host "  Log:         $logApp"
    Write-Host "  Log de erro: $logErro"
    Escrever-Passo "Para derrubar: .\scripts\testar.ps1 -Parar -Porta $Porta"
    Write-Host ""
    exit 0
}

try {
    python run.py --host 127.0.0.1 --port $Porta
} finally {
    if ($trabalhoSimulado) {
        Stop-Job $trabalhoSimulado -ErrorAction SilentlyContinue
        Remove-Job $trabalhoSimulado -ErrorAction SilentlyContinue
        Write-Host "Sistec simulado encerrado." -ForegroundColor DarkGray
    }
    if ($processoSimulado) {
        Stop-Process -Id $processoSimulado.Id -Force -ErrorAction SilentlyContinue
        Write-Host "Sistec simulado encerrado." -ForegroundColor DarkGray
    }
}
