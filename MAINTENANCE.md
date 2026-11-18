# Fork maintenance / 个人维护说明

This is **Cooljoes' maintenance fork of OceanBase seekdb**. Fork-specific work
focuses on developer environment diagnostics, reproducible validation, and small,
reviewable improvements. The database engine and inherited changes are credited
to the [upstream project](https://github.com/oceanbase/seekdb) and their original
authors.

本页记录本仓库的维护范围、验证入口和贡献归属。维护状态更新：**2026-11-18**。

## 1. 本仓库新增的维护内容

| 内容 | 入口 | 用途 |
| --- | --- | --- |
| 中英文维护入口 | [English README](README.md) · [中文 README](README_CN.md) | 让访问者先了解个人维护范围，再阅读上游产品介绍 |
| 开发环境报告 | [tools/collect_dev_env.py](tools/collect_dev_env.py) | 汇总本机环境与仓库工具链要求，便于复现和排查构建问题 |
| 验证记录约定 | [下文的验证记录](#4-验证记录) | 将源码检查、实际构建、SQL 回归和性能测试分别记录 |

这一轮以开发辅助工具和文档为范围。数据库运行时修复与性能结论应分别由对应
代码差异和实际运行证据支持。

## 2. 代码来源与贡献归属

本次维护开始时，本仓库 `master` 位于
[`8eee7d408f35`](https://github.com/Cooljoes/seekdb/commit/8eee7d408f35e4b6d985e06a72e8a4cee098fc45)，
该提交添加了参赛团队验证信息；它的父提交是
[`db4bb5dc6f01`](https://github.com/Cooljoes/seekdb/commit/db4bb5dc6f015bc3c54a06aea0c6f74fc50a9801)。

阅读历史或整理项目经历时，请区分以下记录：

| 记录 | 如何核实 |
| --- | --- |
| 本仓库新增的维护工作 | 查看本仓库对应提交的文件差异、作者和验证说明 |
| 继承的上游功能或修复 | 查看原提交作者及上游 PR；出现在 fork 历史中并不等于由 fork 维护者实现 |
| 本机复现结果 | 记录完整 commit、平台、命令和输出；只适用于实际执行的环境 |
| 上游已接受的贡献 | 以 `oceanbase/seekdb` 中对应 PR 的实际状态为依据 |

例如，历史中的 macOS 构建与 jemalloc 启动修复
[`95db14417e53`](https://github.com/Cooljoes/seekdb/commit/95db14417e53af5d64f8e8dde3e90de1f85c333c)
和启动失败/I/O 能力探测修复
[`6ff9b040095e`](https://github.com/Cooljoes/seekdb/commit/6ff9b040095ec810f4b14bf7edc022483d85e39b)
属于继承的上游提交，应保留原作者归属。提交说明中记录的历史验证也应注明来源。

## 3. 开发与复现入口

从本 fork 开始开发：

```bash
git clone https://github.com/Cooljoes/seekdb.git
cd seekdb
git rev-parse HEAD
```

### 先采集环境信息

环境报告工具仅使用 Python 标准库，可输出易读文本或 JSON：

```bash
python3 tools/collect_dev_env.py
python3 tools/collect_dev_env.py --json
python3 tools/collect_dev_env.py --json --build-dir /absolute/path/to/seekdb-build
```

默认读取脚本所在源码目录，构建目录默认为该目录下的 `build`。可通过
`--repo /absolute/path/to/seekdb` 检查另一个 checkout；相对路径按运行命令时的
当前目录解析。

报告包括系统、架构、CPU 数量、Python、仓库固定的工具链版本、PATH 中工具的
位置、磁盘容量和当前 Git commit。它不会运行编译器、Rust 或 Bazel，也不会
下载依赖、创建构建目录或启动数据库。源码导出目录没有 Git 时，commit 显示为
`null`；构建目录不存在时，报告明确标出用于测量容量的最近现有父目录。

工具位置不等于已安装版本符合要求，环境报告也不表示完整构建已通过。报告包含
本地路径，分享前应检查这些路径是否适合公开。

### 构建与运行

先阅读[工具链要求](docs/developer-guide/en/toolchain.md)，再按
[构建与运行指南](docs/developer-guide/en/build-and-run.md)执行：

```bash
./build.py init
./build.py build -j2 seekdb
```

`-j2` 是便于控制本地并发的示例值，可按实际资源调整。`init` 和构建过程可能下载
依赖，完整构建需要较多内存和磁盘空间。工具链版本以本 checkout 的
[.bazelversion](.bazelversion) 和 [rust-toolchain.toml](rust-toolchain.toml) 为准。

如需将构建产物放到外置磁盘，可使用构建器支持的 `-o` 参数，将下方路径替换为
已经挂载、可写且空间充足的目录：

```bash
./build.py build -j2 -o /absolute/path/to/seekdb-build seekdb
```

自定义输出目录只决定构建工作目录和输出链接；共享下载缓存与工具链位置还需按
[构建指南中的缓存说明](docs/developer-guide/en/build-and-run.md#reuse-build-caches)单独配置。

| 要验证的行为 | 已有入口 |
| --- | --- |
| 启动、连接、停止及重启实例 | [Run a local instance](docs/developer-guide/en/build-and-run.md#run-a-local-instance) |
| C++ 单元测试 | [Unit tests](docs/developer-guide/en/unittest.md) |
| SQL 行为回归 | [mysqltest](docs/developer-guide/en/mysqltest.md) |
| 整理可供上游评审的变更 | [Contributing](CONTRIBUTING.md) |

## 4. 验证记录

每次修复或复现请保留以下记录。未执行的项目写明“未执行”，仅有构建成功时应继续
保留运行时验证项，性能变化则需要独立的基线与对照测量。

```text
Date / 日期：
Repository and full commit SHA / 仓库与完整提交：
Changed files / 修改文件：
OS, architecture, CPU and memory / 系统与硬件：
Toolchain versions / 工具链版本：
Build directory and storage / 构建目录及磁盘：
Exact commands / 完整命令：
Observed exit codes and outputs / 实际退出码与输出：
SQL or regression cases / 回归用例：
Skipped checks and reasons / 未执行项及原因：
Performance baseline and candidate / 性能基线与对照（如适用）：
```

本轮在 Linux 开发环境中执行了新增工具的帮助、文本、JSON、无效源码目录和
无 Git 源码目录检查。正常报告退出码为 0；无效源码目录返回退出码 2；无 Git
目录的 commit 为 `null`；检查不存在的构建路径时没有创建该目录。

文档链接与文件差异也已检查。完整数据库编译、macOS 实机运行、SQL 回归和性能
评测需要在对应环境中另行执行。

## 5. 后续维护方向

优先选择能够独立复现、明确说明影响的小问题：环境诊断信息缺失、构建说明与
当前脚本不一致、已有测试中的确定性失败。提交应包含问题、最小变更、实际验证
与适用范围。拟提交上游的代码从对应上游基线单独整理，按
[贡献流程](CONTRIBUTING.md)进行评审。

## 6. 提交身份与 GitHub 记录

Cooljoes 在本仓库已有提交使用了 GitHub 提供的公开 noreply 邮箱。本人在新的
checkout 中维护本仓库时，可配置仓库级身份：

```bash
git config --local user.name "Cooljoes_ZSQD"
git config --local user.email "78728428+Cooljoes@users.noreply.github.com"
git var GIT_AUTHOR_IDENT
```

协作者应使用自己的身份与已关联邮箱。作者姓名、执行 `git push` 的账号和提交
邮箱关联是不同的信息，应以 GitHub 提交页面实际显示的关联为准。

公开 fork 的提交可供查看和评审，但其提交本身不会直接计入个人贡献图；GitHub
对贡献图另有仓库类型、分支及作者邮箱要求。参见
[GitHub contributions reference](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference)。

## License

本仓库继续使用已有 [Apache License 2.0](LICENSE)，并保留上游的
[NOTICE](NOTICE) 与源文件版权声明。
