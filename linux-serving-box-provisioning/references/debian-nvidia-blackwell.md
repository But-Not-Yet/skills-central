# Debian 上喂饱 Blackwell（RTX 50 系）的 NVIDIA 驱动

## 判据

**Blackwell（RTX 50xx）只支持 570+ 的开源（open）内核模块。**
闭源（proprietary）内核模块不论版本都不支持该架构。

## Debian 各源的陷阱

| 源 | 包 | 结论 |
|---|---|---|
| trixie 正源 | `nvidia-driver` / `nvidia-kernel-dkms` 550.x | 闭源流派，**带不动** |
| trixie-backports | 同上，`~bpo13+1` 550.x | **同样闭源**，升级版本无用 |
| sid | 仍 550 系闭源 | **同样死路** |
| **NVIDIA CUDA 仓库** | `nvidia-driver-cuda` + `nvidia-kernel-open-dkms` 590–615 | **正路** |

教训：症状是「换了三个源都是 550」时，**不是版本问题，是流派（open vs closed）问题**——
先查架构对内核模块流派的要求，再挑版本。

## 安装步骤（Debian 13）

```bash
# 0. 先清干净闭源残留（否则文件冲突）
sudo apt-get purge -y '^nvidia-.*' '^libnvidia-.*' xserver-xorg-video-nvidia

# 1. 配 NVIDIA 官方仓库（debian13 分仓，确认存在后再给用户命令）
wget https://developer.download.nvidia.com/compute/cuda/repos/debian13/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb

# 2. 关键前置：https 源需要 CA——chroot/最小系统里常缺
sudo apt-get install -y ca-certificates

# 3. 装（DKMS 针对 6.12 内核编译，几分钟）
sudo apt-get install -y nvidia-driver-cuda nvidia-kernel-open-dkms
# 验收：dpkg -l | grep nvidia-driver-cuda → 615.x 之类；nvidia-smi 出卡名
```

**排查形状**：`Unable to locate package` 时先查仓库索引本身
（`curl <repo>/Packages.gz | zgrep -A1 '^Package: <名>'`）确认包在索引里，
再怀疑本地 apt——大概率是 https CA 缺失导致该源静默失败，
`apt-get update` 的输出里 `Err:` 行即证据。

## headless 注意

- `nvidia-driver-cuda` 是纯计算档（带 CUDA 运行库、无 GL/X 桌面件），正合 headless。
- chroot/最小系统里 DKMS 编译若报 openssl 缺失（MOK 自签），先 `apt-get install openssl`。
- Secure Boot 开着会拒载自签模块——干活机在 BIOS 直接关掉最省事。
