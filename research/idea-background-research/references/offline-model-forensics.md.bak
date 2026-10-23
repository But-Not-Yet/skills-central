# 模型离线取证配方（GGUF 头 / safetensors 嵌入，零推理调用）

用途：词表能力、标记身份、控制 id、嵌入几何这类问题，先在文件层取证（CPU 秒级、零生产调用），再设计行为实验。行为实验的靶点（eos/bos id、标记的 CONTROL 状态、词表可拼性）全部先从 GGUF 头读出，不从文档假设。

## GGUF v3 布局（纯 python 可读）

magic `GGUF`(4B) + version(u32) + tensor_count(u64) + **kv_count(u64)**，然后逐条 KV：

- key：u64 字节数 + UTF-8
- value 类型表：0=u8 1=i8 2=u16 3=i16 4=u32 5=i32 6=f32 7=bool **8=string** **9=array** 10=u64 11=i64
- string = u64 长度 + 内容
- **array = 元素类型(u32) 在前、个数(u64) 在后**——顺序读反直接 MemoryError 或静默错位
- 常用键：general.architecture / general.name / tokenizer.ggml.model / tokenizer.ggml.pre / tokenizer.ggml.tokens（string 数组）/ tokenizer.ggml.token_type（**整数数组，元素类型 5=i32**；1=NORMAL 3=CONTROL）/ tokenizer.ggml.eos_token_id
- 超大数组（亿行级 N-gram 表）别整体 list()——只接需要的 key，其余按元素大小跳过

坑：
- type 8 是 string 不是 bool（bool=7）——类型表写错会静默读到错位数据，症状是后续所有 key 全乱。
- token_type 是整数数组——元素类型 dispatch 不能写死 et==8。
- 整数数组的元素要 unpack 后接住再赋给目标变量；只解包不接住，下游「CONTROL 判定」会全错且难发现（症状：所有标记都显示 NOT-control）。
- 分卷 GGUF（-00001-of-00003）：头与词表完整在首卷；大张量数据跨卷，词表/tokenizer 取证不受影响。

## 字面量可拼性 DP

问「模型有没有能力拼出某字面量」时：以 CONTROL(type=3) 之外的 token 建可拼集合，对目标串做区间 DP（reach[pos] 记起点拼到 pos 的路径），输出路径 id + 多解性。「词表可拼」只证必要条件——BPE 合并优先级、上下文条件仍可能压住路径，不证「想拼就能拼」；对应地，「行为上不走拼写路径」与「词表无手段」是两个命题，报告里不得混用。

## safetensors 嵌入读取（BF16）

布局：u64 header 长度 + json header（每张量 dtype/shape/data_offsets，offset 相对数据段起点）+ 数据段。

- BF16→F32 位级转换：`u16=np.frombuffer(buf,dtype='<u2'); f32=(u16.astype(np.uint32)<<16).view(np.float32)`，reshape 即 [vocab, hidden] 浮点矩阵。
- cosine 近邻一次矩阵乘 `emb @ q / (norms*qnorm)`；排除集（special ids）在结果上置 -inf，不要复制整个矩阵做 mask。
- 环境无 numpy 时：`pip install --user -i https://pypi.tuna.tsinghua.edu.cn/simple numpy`（用户级安装，一次到位）。
- special 口径对齐：tokenizer.json 里 special=True 的条目数可能远少于 GGUF token_type=3 的数量——「排除 special」前先核对两套口径，报告里写明用的是哪套。
