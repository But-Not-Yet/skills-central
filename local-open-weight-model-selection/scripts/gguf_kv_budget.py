#!/usr/bin/env python3
"""读 GGUF 头部元数据，算 KV 缓存每 token 占用与给定显存预算下的最大上下文。

用法:
  python3 gguf_kv_budget.py model.gguf            # 只报 KV 每 token 成本
  python3 gguf_kv_budget.py model.gguf 12.8       # 另报 12.8 GiB 预算下可容多少上下文

要点 / 陷阱:
- 必须正确跳过字符串数组（tokenizer 词表几万条）。只按固定宽度跳标量、遇数组不消费字节
  → 读取错位，表象是 OverflowError（“字符串长度离谱”）。
- 混合架构（qwen35 等）只有全注意力层有 KV：全注意力层数 = block_count // full_attention_interval。
- MTP 版 GGUF 的 block_count = 基座层数 + 1（草稿层），不影响上面的整除。
- 每元素字节: f16/bf16=2, q8_0=34/32, q4_0=18/32, q5_0=22/32。
- 只读文件头部（顺序 seek），不解权重，可对大文件直接跑。
"""
import struct
import sys

SZ = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 4, 7: 1, 10: 8, 11: 8, 12: 8}
BYTES_PER_ELEM = {'f16': 2.0, 'bf16': 2.0, 'q8_0': 34 / 32, 'q5_0': 22 / 32, 'q4_0': 18 / 32}
GiB = 1024 ** 3


def read_meta(path):
    f = open(path, 'rb')
    if f.read(4) != b'GGUF':
        raise SystemExit('not a GGUF file')
    struct.unpack('<I', f.read(4))[0]  # version
    _n_tensors, n_kv = struct.unpack('<QQ', f.read(16))

    def rstr():
        n = struct.unpack('<Q', f.read(8))[0]
        return f.read(n).decode('utf-8', 'replace')

    def skip_arr(et, n):
        if et == 8:
            for _ in range(n):
                ln = struct.unpack('<Q', f.read(8))[0]
                f.seek(ln, 1)
        elif et == 9:
            for _ in range(n):
                et2 = struct.unpack('<I', f.read(4))[0]
                n2 = struct.unpack('<Q', f.read(8))[0]
                skip_arr(et2, n2)
        else:
            f.seek(SZ[et] * n, 1)

    def rval(t):
        if t == 8:
            return rstr()
        if t == 9:
            et = struct.unpack('<I', f.read(4))[0]
            n = struct.unpack('<Q', f.read(8))[0]
            if n <= 16 and et not in (8, 9):
                return [rval(et) for _ in range(n)]
            skip_arr(et, n)
            return None
        return int.from_bytes(f.read(SZ[t]), 'little', signed=(t in (1, 3, 5, 7)))

    meta = {}
    for _ in range(n_kv):
        k = rstr()
        t = struct.unpack('<I', f.read(4))[0]
        meta[k] = rval(t)
    return meta


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    path = sys.argv[1]
    budget_gib = float(sys.argv[2]) if len(sys.argv) > 2 else None
    m = read_meta(path)
    arch = m.get('general.architecture')
    g = lambda s, d=None: m.get(f'{arch}.{s}', d)
    blocks, kvh = g('block_count'), g('attention.head_count_kv')
    kl, vl = g('attention.key_length'), g('attention.value_length')
    interval = int(g('full_attention_interval', 1) or 1)
    if None in (blocks, kvh, kl, vl):
        raise SystemExit(f'元数据缺字段: arch={arch} blocks={blocks} kvh={kvh} k={kl} v={vl}')
    attn_layers = blocks // interval
    elems = attn_layers * kvh * (kl + vl)
    print(f'arch={arch} block_count={blocks} 全注意力层={attn_layers} (interval={interval}) '
          f'kv_heads={kvh} k/v={kl}/{vl} → {elems} 元素/token')
    ctx_max = g('context_length')
    if ctx_max:
        print(f'架构上下文上限: {ctx_max}')
    for name, bpe in BYTES_PER_ELEM.items():
        b = elems * bpe
        line = (f'  {name:5}: {b:9.0f} B/token ({b / 1024:5.1f} KiB) | '
                f'128K={b * 131072 / GiB:5.2f} GiB | 256K={b * 262144 / GiB:5.2f} GiB')
        if budget_gib:
            line += f' | 预算 {budget_gib:g} GiB 可容 {budget_gib * GiB / b / 1024:.0f}K tok'
        print(line)
    print('提示: 预算 = 总显存 − 权重文件 − 运行时开销(约 1–1.5 GiB)；MTP 草稿头另算少量 KV。')


if __name__ == '__main__':
    main()
