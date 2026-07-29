# Launcher catalog daily-care runtime

This document defines the code-side contract for migrating
`softwarecenter.launchboards.daily-care` away from executable code stored in
OneDrive. It does not authorize or perform a scheduler, Windows Task, profile,
or registry mutation.

## Boundary

- Runtime code: a reviewed SoftwareCenter commit materialized below
  `C:\_Local_DEV\runtime\SoftwareCenter\<commit>`.
- Synchronized inputs: `software_apps.json` and `DESKTOP-REGISTRY.txt`, passed
  as exact command-line arguments.
- Local profile state: the two QSettings namespaces `SoftwareCenter` and
  `LaunchBoards`.
- Backups: local Plan-D storage only, never the synchronized software root.
- Default: dry-run. The scheduler payload below intentionally omits `--apply`.

The runtime never derives synchronized data paths from `__file__`, never
invokes a shell, and never copies catalog or registry data into the repository.

## CLI contract

```powershell
$python = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
$oneDrive = Join-Path $env:USERPROFILE 'OneDrive'
$runtimeRoot = 'C:\_Local_DEV\runtime\SoftwareCenter\<approved-commit>'
$script = Join-Path $runtimeRoot 'scripts\softwarecenter_sync.py'

& $python $script `
  --catalog (Join-Path $oneDrive '.TOPICS\.SOFTWARE\_tools\software_apps.json') `
  --registry (Join-Path $oneDrive 'Desktop\DESKTOP-REGISTRY.txt') `
  --software-root (Join-Path $oneDrive '.TOPICS\.SOFTWARE') `
  --local-dev-root 'C:\_Local_DEV'
```

Exit codes:

- `0`: valid dry-run or completed apply.
- `2`: missing/invalid input or a failed apply gate.
- `3`: write operation failed after a backup was created.

An apply run additionally requires `--apply`. It aborts while either managed
GUI is running and creates a local `launcher-catalog-profile-backup-v2` before
the first profile or registry write. The backup contains both original
QSettings projections and the exact original registry text plus SHA-256. If a
write fails after the backup, the runtime prints its exact path and immediately
attempts to restore both profiles and the registry. An incomplete rollback is
reported explicitly and still exits `3`. The registry bytes are captured once
immediately before the write phase and reused unchanged for both backup and
rollback; if that final read is unavailable, the apply exits before any write.

## Pinned runtime materialization

Only use a reviewed commit that is reachable from the intended release branch.
The target directory must not already contain unrelated files.

```powershell
$repo = 'C:\_Local_DEV\repos\SoftwareCenter'
$approvedCommit = '<approved-commit>'
$releaseRef = 'origin/master'
$runtimeRoot = "C:\_Local_DEV\runtime\SoftwareCenter\$approvedCommit"
$archive = Join-Path $env:TEMP "softwarecenter-$approvedCommit.tar"

git -C $repo cat-file -e "$approvedCommit^{commit}"
git -C $repo merge-base --is-ancestor $approvedCommit $releaseRef
if ($LASTEXITCODE -ne 0) {
  throw "$approvedCommit is not reachable from $releaseRef"
}
if (Test-Path -LiteralPath $runtimeRoot) {
  throw "Runtime target already exists: $runtimeRoot"
}
if (Test-Path -LiteralPath $archive) {
  throw "Temporary archive already exists: $archive"
}
New-Item -ItemType Directory -Path $runtimeRoot
git -C $repo archive --format=tar --output=$archive $approvedCommit
tar -xf $archive -C $runtimeRoot
Remove-Item -LiteralPath $archive
git -C $repo show -s --format='%H' $approvedCommit
```

Record the commit, runtime path, interpreter path, input hashes, and dry-run
output in the native migration receipt. Do not use a mutable OneDrive worktree
or an unpinned conflict copy.

## Proposed native scheduler migration

`ellmos-scheduler` 0.1.0 has no in-place payload-update command. Preserve the
old job as a disabled rollback target and introduce a separately identifiable
candidate. Run these commands only after:

1. the pinned runtime dry-run exits `0`;
2. current `jobs --json`, `status --json`, and recent runs are captured;
3. the existing job has a recent native success receipt or its degraded
   baseline is explicitly recorded;
4. the SoftwareCenter and LaunchBoards processes are absent;
5. a byte-for-byte scheduler database backup exists outside OneDrive.

```powershell
$db = Join-Path $env:LOCALAPPDATA 'ellmos\scheduler.db'
$python = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
$oneDrive = Join-Path $env:USERPROFILE 'OneDrive'
$approvedCommit = '<approved-commit>'
$runtimeRoot = "C:\_Local_DEV\runtime\SoftwareCenter\$approvedCommit"
$script = Join-Path $runtimeRoot 'scripts\softwarecenter_sync.py'

$argv = @(
  $python,
  $script,
  '--catalog',
  (Join-Path $oneDrive '.TOPICS\.SOFTWARE\_tools\software_apps.json'),
  '--registry',
  (Join-Path $oneDrive 'Desktop\DESKTOP-REGISTRY.txt'),
  '--software-root',
  (Join-Path $oneDrive '.TOPICS\.SOFTWARE'),
  '--local-dev-root',
  'C:\_Local_DEV'
)
$payload = @{
  argv = $argv
  cwd = $runtimeRoot
} | ConvertTo-Json -Compress
$schedule = @{
  kind = 'daily'
  time = '06:20'
  timezone = 'Europe/Berlin'
} | ConvertTo-Json -Compress

ellmos-scheduler --db $db jobs --json
ellmos-scheduler --db $db status --json
ellmos-scheduler --db $db add `
  --id softwarecenter.launchboards.daily-care.v4 `
  --schedule $schedule `
  --executor command `
  --payload $payload `
  --lease-seconds 300 `
  --timeout-seconds 120
ellmos-scheduler --db $db jobs --json
ellmos-scheduler --db $db disable softwarecenter.launchboards.daily-care
ellmos-scheduler --db $db jobs --json
```

Adding the candidate before disabling the old job keeps the rollback target
available if candidate creation fails. If the final disable or its readback
fails, immediately disable the `.v4` candidate before leaving the system.

The existing Windows Task continues to run one native scheduler tick; its
action does not need to point at this script. Do not alter that task unless its
own native readback proves a separate defect.

The first candidate execution must be observed through native scheduler run
history. The receipt must prove:

- `executor=command`;
- argv contains the pinned runtime and all four explicit paths;
- `cwd` is the pinned runtime, not OneDrive;
- exit code `0`;
- output says `DRY-RUN`;
- input files, QSettings profiles, and registry remain unchanged.

## Rollback

If the candidate must be rolled back before its first run:

```powershell
$db = Join-Path $env:LOCALAPPDATA 'ellmos\scheduler.db'
ellmos-scheduler --db $db disable softwarecenter.launchboards.daily-care.v4
ellmos-scheduler --db $db enable softwarecenter.launchboards.daily-care
ellmos-scheduler --db $db jobs --json
```

After any apply run, also restore the registry text and both profile snapshots
from the reported `launcher-catalog-profile-backup-v2` file. The explicit
restore gate uses the same exact runtime/input bindings:

```powershell
$python = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
$oneDrive = Join-Path $env:USERPROFILE 'OneDrive'
$runtimeRoot = 'C:\_Local_DEV\runtime\SoftwareCenter\<approved-commit>'
$script = Join-Path $runtimeRoot 'scripts\softwarecenter_sync.py'
$backup = 'C:\_Local_DEV\launcher_catalog_backups\<backup-file>.json'

& $python $script `
  --catalog (Join-Path $oneDrive '.TOPICS\.SOFTWARE\_tools\software_apps.json') `
  --registry (Join-Path $oneDrive 'Desktop\DESKTOP-REGISTRY.txt') `
  --software-root (Join-Path $oneDrive '.TOPICS\.SOFTWARE') `
  --local-dev-root 'C:\_Local_DEV' `
  --apply `
  --restore-backup $backup
```

The restore command validates the backup format, registry binding and SHA-256,
then snapshots the current state before restoring both QSettings profiles and
the registry. If the restore itself fails after its first write, it compensates
back to that pre-restore snapshot and reports whether the compensation was
complete. Verify the registry hash and QSettings readback afterwards. Never
overwrite a newer user edit without first comparing it to the backup and
obtaining the applicable decision.

The candidate job, pinned runtime, and database backup remain in place until a
successful run and rollback rehearsal have both been recorded. Cleanup is a
separate, explicit operation.
