# Windows development launcher. Runtime state and logs stay in ignored .local/.
param(
    [ValidateSet('Start', 'Stop')][string]$Action = 'Start',
    [ValidateRange(1, 65535)][int]$WebPort = 3000,
    [ValidateRange(1, 65535)][int]$ApiPort = 8000
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $projectRoot '.local'
$statePath = Join-Path $runtime 'dev-processes.json'
Set-Location -LiteralPath $projectRoot

function Get-OwnedProcess($record) {
    $process = Get-Process -Id $record.id -ErrorAction SilentlyContinue
    # A reused PID must never cause an unrelated process to be stopped.
    if ($process -and $process.StartTime.ToUniversalTime().Ticks.ToString() -eq $record.started) {
        return $process
    }
}

function Stop-Dev {
    if (-not (Test-Path -LiteralPath $statePath)) {
        Write-Host 'No development servers started by this launcher are recorded.'
        return
    }
    $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    if ($state.root -ne $projectRoot) { throw 'The saved launcher state belongs to a different project.' }
    foreach ($record in $state.processes) {
        $process = Get-OwnedProcess $record
        if ($process) {
            # Include Next.js/Uvicorn children, without killing other Node/Python apps.
            & taskkill.exe /PID $process.Id /T /F | Out-Null
            if ($LASTEXITCODE -ne 0 -and (Get-OwnedProcess $record)) {
                throw "Could not stop $($record.name). Choose Stop in dev.cmd again."
            }
        }
    }
    Remove-Item -LiteralPath $statePath
    Write-Host 'ProfitLens development servers stopped. PostgreSQL is left running.'
}

try {
    if ($Action -eq 'Stop') { Stop-Dev; exit 0 }
    if (Test-Path -LiteralPath $statePath) {
        $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
        if ($state.root -ne $projectRoot) { throw 'The saved launcher state belongs to a different project.' }
        if (@($state.processes | Where-Object { Get-OwnedProcess $_ }).Count -gt 0) {
            Write-Host 'Development servers are already started. Choose Stop in dev.cmd before starting again.'
            Write-Host "Website: http://localhost:$($state.webPort)"
            exit 0
        }
        Remove-Item -LiteralPath $statePath
    }
    if ($WebPort -eq $ApiPort) { throw 'Frontend and API ports must differ.' }
    $python = Join-Path $projectRoot '.venv\Scripts\python.exe'
    $webRoot = Join-Path $projectRoot 'apps\web'
    $next = Join-Path $webRoot 'node_modules\next\dist\bin\next'
    foreach ($required in @($python, $next, (Join-Path $projectRoot '.env'))) {
        if (-not (Test-Path -LiteralPath $required)) {
            throw 'Complete the one-time setup in docs/DEVELOPMENT.md first (.venv, .env and npm ci).'
        }
    }
    $node = (Get-Command node.exe -ErrorAction Stop).Source
    foreach ($port in @($WebPort, $ApiPort)) {
        if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
            throw "Port $port is already in use. Stop that existing server first; this launcher will not terminate it."
        }
    }
    New-Item -ItemType Directory -Force -Path $runtime | Out-Null
    # Reuse the prepared machine's private PostgreSQL, if installed.
    # Other machines must start their configured PostgreSQL service or Docker first.
    $pgCtl = Join-Path $runtime 'pgsql\bin\pg_ctl.exe'
    $pgData = Join-Path $runtime 'pgdata'
    if ((Test-Path -LiteralPath $pgCtl) -and (Test-Path -LiteralPath $pgData)) {
        & $pgCtl -D $pgData status *> $null
        if ($LASTEXITCODE -ne 0) {
            $pgLog = Join-Path $runtime 'postgres.log'
            $pgProcess = Start-Process -FilePath $pgCtl -ArgumentList "-D `"$pgData`" -l `"$pgLog`" -o `"-p 55432 -h 127.0.0.1`" -w start" -WindowStyle Hidden -PassThru -Wait
            if ($pgProcess.ExitCode -ne 0) { throw 'PostgreSQL startup failed. Inspect .local/postgres.log.' }
        }
    }
    Write-Host 'Checking database migrations...'
    & $python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw 'Database not ready. Check your PostgreSQL service and .env settings.' }
    $env:WEB_ORIGIN = "http://localhost:$WebPort"
    $env:API_INTERNAL_URL = "http://127.0.0.1:$ApiPort"
    $env:COOKIE_SECURE = 'false'
    $state = @{ root = $projectRoot; webPort = $WebPort; apiPort = $ApiPort; processes = @() }
    $state | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $statePath -Encoding UTF8
    try {
        $apiArgs = "-m uvicorn profitlens.main:app --host 127.0.0.1 --port $ApiPort --reload --reload-dir `"$projectRoot\apps\api`""
        $api = Start-Process -FilePath $python -ArgumentList $apiArgs -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput "$runtime\dev-api.out" -RedirectStandardError "$runtime\dev-api.err"
        $state.processes += @{ name = 'API'; id = $api.Id; started = $api.StartTime.ToUniversalTime().Ticks.ToString() }
        $state | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $statePath -Encoding UTF8
        $web = Start-Process -FilePath $node -ArgumentList "`"$next`" dev --hostname 127.0.0.1 --port $WebPort" -WorkingDirectory $webRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput "$runtime\dev-web.out" -RedirectStandardError "$runtime\dev-web.err"
        $state.processes += @{ name = 'Web'; id = $web.Id; started = $web.StartTime.ToUniversalTime().Ticks.ToString() }
        $state | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $statePath -Encoding UTF8
        Write-Host 'Starting frontend and API with automatic reload...'
        $ready = $false
        for ($attempt = 0; $attempt -lt 45; $attempt++) {
            if (@($state.processes | Where-Object { Get-OwnedProcess $_ }).Count -ne 2) {
                throw 'A server exited. Inspect .local/dev-api.err and .local/dev-web.err.'
            }
            try {
                $health = Invoke-RestMethod -Uri "http://127.0.0.1:$ApiPort/api/health" -TimeoutSec 2
                $response = Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:$WebPort" -TimeoutSec 2
                if ($health.status -eq 'ok' -and $response.StatusCode -eq 200) { $ready = $true; break }
            } catch { Start-Sleep -Milliseconds 500 }
        }
        if (-not $ready) { throw 'Startup timed out. Inspect the .local/dev-*.out and .err logs.' }
        Write-Host "Ready: http://localhost:$WebPort"
        Write-Host "API docs: http://127.0.0.1:$ApiPort/docs"
        Write-Host 'Ready. Choose 2 in dev.cmd to stop both servers; 0 closes only the launcher.'
        Write-Host 'Logs: .local/dev-web.out, dev-web.err, dev-api.out and dev-api.err'
    } catch {
        Stop-Dev
        throw
    }
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
