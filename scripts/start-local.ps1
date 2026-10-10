# Start the already configured local development workspace without opening windows.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Complete docs/DEVELOPMENT.md setup first.' }
if (-not (Test-Path -LiteralPath '.env')) { throw 'Create and configure .env first.' }
New-Item -ItemType Directory -Force -Path '.local' | Out-Null
$pgCtl = Join-Path $projectRoot '.local\pgsql\bin\pg_ctl.exe'
$pgData = Join-Path $projectRoot '.local\pgdata'
if ((Test-Path -LiteralPath $pgCtl) -and (Test-Path -LiteralPath $pgData)) {
    & $pgCtl -D $pgData status *> $null
    if ($LASTEXITCODE -ne 0) {
        Start-Process -FilePath $pgCtl -ArgumentList "-D `"$pgData`" -l `"$projectRoot\.local\postgres.log`" -o `"-p 55432 -h 127.0.0.1`" start" -WindowStyle Hidden
        $ready = $false
        for ($attempt = 0; $attempt -lt 20; $attempt++) {
            Start-Sleep -Milliseconds 500
            & (Join-Path $projectRoot '.local\pgsql\bin\pg_isready.exe') -h 127.0.0.1 -p 55432 *> $null
            if ($LASTEXITCODE -eq 0) { $ready = $true; break }
        }
        if (-not $ready) { throw 'Local PostgreSQL did not become ready; inspect .local/postgres.log.' }
    }
}
& $pythonPath -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw 'Database migration failed.' }
if (-not (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue)) {
    $apiProcess = Start-Process -FilePath $pythonPath -ArgumentList '-m uvicorn profitlens.main:app --host 127.0.0.1 --port 8000' -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput '.local/api.out' -RedirectStandardError '.local/api.err'
    $apiProcess.Id | Set-Content '.local/api.pid'
}
if (-not (Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue)) {
    $nodePath = (Get-Command node.exe).Source
    $webRoot = Join-Path $projectRoot 'apps\web'
    $webProcess = Start-Process -FilePath $nodePath -ArgumentList 'node_modules/next/dist/bin/next start --hostname 127.0.0.1' -WorkingDirectory $webRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput '.local/web.out' -RedirectStandardError '.local/web.err'
    $webProcess.Id | Set-Content '.local/web.pid'
}
Write-Output 'Open http://localhost:3000. Logs are in .local. Run npm run build in apps/web after frontend changes.'
