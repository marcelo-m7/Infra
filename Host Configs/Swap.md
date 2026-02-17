# SETU — Swap setup and tuning guide

This note documents a safe, repeatable procedure to add and tune a swapfile on an Ubuntu/Debian Linux server. Use this when a machine has low RAM (< 4GB) or when builds/tasks fail due to out-of-memory. It also covers verification, removal, and a few performance considerations.

Audience: sysadmins and devs who can run commands as root or via sudo.

TL;DR (one-liners)

```bash
# create 2GiB swapfile and enable it now + persist in /etc/fstab
sudo fallocate -l 10G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile && echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# tune swappiness (lower = less swapping)
sudo sysctl vm.swappiness=10 && sudo bash -c 'echo "vm.swappiness=10" >> /etc/sysctl.conf'

# verify
sudo swapon --show && free -h
```

## Why add swap?

- Swap provides on-disk backing memory when physical RAM is exhausted. It prevents OOM kills and failed builds, at the cost of higher latency when pages are paged out.

## Recommendations

- For lightweight VMs (1–3 GB RAM): 1–2 GiB swap is commonly sufficient.
- For build servers: match expected peak consumption; consider 2–8 GiB depending on workload.
- Prefer a swapfile (vs partition) for simplicity and safety.
- On NVMe/SSD, swap is efficient for emergency use but may have wear implications if heavily used.


## Create a swapfile (safe steps)

Run these commands as root or with sudo. Adjust size (`2G`) as needed.

```bash
sudo fallocate -l 2G /swapfile                # fast allocation
sudo chmod 600 /swapfile                      # restrict permissions
sudo mkswap /swapfile                         # format swap
sudo swapon /swapfile                         # enable immediately

# Persist: append to /etc/fstab safely (do not type the fstab line as a command)
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

Notes:

- If `fallocate` is unavailable or you want a sparse-proof method, use `dd` instead:

```bash
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048 status=progress
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Tune swappiness and cache pressure

- `vm.swappiness` controls how eagerly the kernel swaps; lower values favor RAM and avoid I/O. Common values: 10 (desktop/build host), 60 (default), 0 (avoid swapping unless strictly necessary).
- `vm.vfs_cache_pressure` controls inode/dentry reclaiming; 50–100 is reasonable.

```bash
sudo sysctl vm.swappiness=10
sudo sysctl vm.vfs_cache_pressure=100
sudo bash -c 'echo "vm.swappiness=10" >> /etc/sysctl.conf'
sudo bash -c 'echo "vm.vfs_cache_pressure=100" >> /etc/sysctl.conf'
```


## Verify swap and health

```bash
sudo swapon --show
free -h
cat /proc/swaps
vmstat 1 5      # watch swapping activity (si/so columns)
```

### Interpreting results

- `swapon --show` lists active swap devices/files and sizes.
- `free -h` shows Swap: used/free — heavy swap usage indicates memory pressure.
- `vmstat` si/so activity > 0 indicates swapping I/O (can slow workloads).


## Removing swap safely

```bash
sudo swapoff /swapfile
sudo rm /swapfile
# remove the line from /etc/fstab (edit or use awk to dedupe)
sudo cp /etc/fstab /etc/fstab.bak.$(date +%s)
sudo awk '!seen[$0]++' /etc/fstab | sudo tee /etc/fstab.tmp && sudo mv /etc/fstab.tmp /etc/fstab
```


## De-duplicate `/etc/fstab` if you accidentally appended the line twice

```bash
sudo cp /etc/fstab /etc/fstab.bak.$(date +%s)
sudo awk '!seen[$0]++' /etc/fstab | sudo tee /etc/fstab.tmp && sudo mv /etc/fstab.tmp /etc/fstab
sudo swapon -a
sudo swapon --show
```

## Alternatives and extras

- zram: compressed in-memory swap (low-latency) good for low-RAM systems. See `zram-tools` / `systemd-zram-setup`.
- swap on encrypted filesystems: place swapfile on the decrypted filesystem or use swap partition with encryption considerations.
- systemd SwapUnits: systemd can manage a swapfile unit — use for advanced setups.

## Performance & SSD wear notes

- Occasional swapping is fine on modern SSDs; heavy swapping causes extra writes and may shorten SSD lifetime.
- If heavy swapping is expected, prefer adding RAM or using zram rather than relying on disk swap long-term.

## Troubleshooting

- If `swapon` fails: check `/var/log/syslog` and `dmesg` for errors (incorrect permissions, filesystem not allowing swapfiles, or ephemeral filesystems).
- If swap doesn't persist on reboot: confirm the exact line exists in `/etc/fstab` and has no stray characters; ensure the file system containing `/swapfile` is mounted early in boot.


## Example complete workflow (Ubuntu/Debian)

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
sudo sysctl vm.swappiness=10
sudo bash -c 'echo "vm.swappiness=10" >> /etc/sysctl.conf'
sudo swapon --show && free -h
```


## Keep it documented

- Add a one-line entry in your infra runbook (this repo) describing why swap was added, size, and date. Example:

```text
2025-11-02: added /swapfile 2G to infra host 88.99.123.102 to avoid build OOMs. vm.swappiness=10
```

If you want, I can create a short checklist file in this repo (e.g., `infra/SWAP-CHECKLIST.md`) and patch `XenInstallation.md` to link to it. Do you want that?
