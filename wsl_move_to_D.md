# Move the laptop's WSL disk from C: to D: (planned, 2026-11-02)

**Why.** Every simulation on the laptop runs inside WSL (Ubuntu). WSL stores its whole Linux disk as one file on C:, `ext4.vhdx`.
- On 2026-11-02 that file was 52 GB, and C: had 39 GB free.
- The rest of the tank batch and the laptop's share of the PCM batch would come close to filling C:.
- D: has about 100 GB free.

**When.** Only when nothing runs in WSL on the laptop. Moving shuts WSL down, which kills every simulation and training job. Planned for after the tank batch finishes (about 4 to 5 Nov), before the PCM batch starts.

**Already done (2026-11-02):** four superseded run folders were slimmed, from 13.2 GB to 4.4 GB.
- The folders: `full_h5mm_n1`, `pilot_h5mm`, `pilot_v2`, `pilot_props`.
- What went: raw OpenFOAM time folders deleted, logs gzipped. Results (`.h5`, `.json`) and case setups were kept.
- WSL usage dropped from 51 to 42 GB. The file on C: keeps its size, but WSL reuses the freed space.
- The PCM runner (`pcm_batch.sh`) now slims each case the same way after it is exported (`PCM_KEEP_RAW=1` keeps everything).

## Steps (Windows PowerShell, run by Saxam)

1. **Check that WSL is idle.** In Ubuntu, `pgrep -c buoyantPimpleFoam` should print 0, and no training should be running.
2. **Stop WSL:** `wsl --shutdown`
3. **Move the disk** (WSL 3.0.3 supports this; it copies the 52 GB file, which takes about 10 to 20 minutes): `wsl --manage Ubuntu --move D:\WSL\Ubuntu`
4. **Start Ubuntu again** and check that `ls ~/of_runs` and `df -h /` look as before.
5. **Optional: shrink the file**, since it does not shrink by itself after deletions. With WSL stopped, run `wsl --manage Ubuntu --set-sparse true`, or compact the file with `Optimize-VHD` (Hyper-V) or diskpart.

Nothing inside Ubuntu changes: paths such as `~/of_runs`, Tailscale, SSH keys and venvs all stay the same.
