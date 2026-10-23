# amdgpu 功耗上限的源码链（Linux master 分支实读）

用途：需要向主人（或检察官）证明「XW 这类上限是谁定的」时，按这条链取证，别背结论。文件路径以 torvalds/linux master 为准，raw 地址可直接 web_extract。

## 写入与拒收链
1. `drivers/gpu/drm/amd/pm/amdgpu_pm.c` — `amdgpu_hwmon_set_power_cap`：微瓦÷1e6 转瓦后直接下发，**本层不做范围检查**。
2. `drivers/gpu/drm/amd/pm/amdgpu_dpm.c` — `amdgpu_dpm_set_power_limit`：纯转发（加锁）。
3. `drivers/gpu/drm/amd/pm/swsmu/amdgpu_smu.c` — `smu_set_ppt_limit`：**真正的拒收点**。按 `smu->ppt_limits.range` 比较，超限 `dev_err("New PPT limit (%d) is out of range [%d,%d]")` + `-EINVAL`。od_enabled 时区间用 `od_min/od_max`，否则 `min/max`。
4. `drivers/gpu/drm/amd/pm/swsmu/smu13/smu_v13_0_0_ppt.c` — `smu_v13_0_0_init_ppt_limits`：区间全部来自固件表——
   - default = `SkuTable.SocketPowerLimitAc[PPT0]`
   - max = max(`SocketPowerLimitAc`, `MsgLimits.Power[PPT0][AC]`)
   - min = min_limit × (100 − od_percent_lower)/100
   - od_max = max_limit × (100 + od_percent_upper)/100
   - 百分比取自 powerplay 表 `overdrive_table.min/max[SMU_13_0_0_ODSETTING_POWERPERCENTAGE]`
   → 结论：**sysfs 的 cap_max 是固件申报值的放缩结果，换发行版/换内核不挪它**。
5. 超限值的绕行（同文件 `smu_v13_0_0_set_ppt_limit`）：limit > msg_limit 且 `smu->od_enabled` 时，驱动本可设 base=msg_limit 并用 OD 表 `Ppt` 百分比抬升。od_enabled 由 `smu_v13_0_0_check_powerplay_table` 里 overdrive lower/upper FeatureCtrlMask 是否非零决定。实测 od_max 未超过 max 时，说明内核从 combo 表读到的增项为 0——TechPowerUp 对 ATOM 段解析出的百分比与内核读到的可以不一致（PMFW combo 表 vs ATOM 段），以 dmesg 实测区间为准。
6. 读取链：`amdgpu_hwmon_show_power_cap_generic` → `amdgpu_dpm_get_power_limit`，PP_PWR_LIMIT_MAX 档回显固件区间。

## 判读口径
- dmesg `out of range [a,b]` 里的 b 就是 od 放缩后的最终值，可直接引用为「内核认可的天花板」。
- `power1_cap_default` = SocketPowerLimitAc（瓦），可与固件档案的 PPT 值互相印证，用来确认卡上实际跑的 ROM。
- 想提上限的可行路径只剩：刷更高 PPT/增项非零的 VBIOS（amdvbflash，有风险），或等上游/厂商放表。ppfeaturemask 不解功耗锁。
