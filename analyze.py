# 将获取到的all_merged_log.txt打印信息统计寻纤成功时间以及时段内平均信噪比

import re
from datetime import datetime

file_path = "all_merged_log.txt"


# =========================
# 普通时间解析 [14:49:06]
# =========================
def parse_time(line, base_date):
    match = re.search(r"\[(\d{2}:\d{2}:\d{2})\]", line)
    if not match:
        return None
    t = datetime.strptime(match.group(1), "%H:%M:%S")
    return t.replace(year=base_date.year, month=base_date.month, day=base_date.day)


# =========================
#  新增：解析开始时间
# =========================
def parse_start_time(line):
    match = re.search(r"新一轮测试开始:\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
    if not match:
        return None
    return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")


# =========================
# 读取文件
# =========================
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

rounds = []
current = None


# =========================
# 解析
# =========================
for line in lines:
    if "新一轮测试开始" in line:
        if current:
            rounds.append(current)

        start_time = parse_start_time(line)

        print(start_time)

        current = {
            "start_time": start_time,
            "snr_logs": [],
            "buzzer_times": []
        }

    elif current:
        t = parse_time(line, current["start_time"])

        # SNR
        m = re.search(r"SNRLOG: bin=\d+ snr=([\d.]+)", line)
        if m and t:
            current["snr_logs"].append((t, float(m.group(1))))

        # 蜂鸣器
        if "蜂鸣器打开" in line and t:
            current["buzzer_times"].append(t)

# 最后一轮
if current:
    rounds.append(current)


# =========================
# 计算
# =========================
def compute(round_data, idx, f):
    start = round_data["start_time"]
    snrs = round_data["snr_logs"]
    buzzers = round_data["buzzer_times"]

    f.write(f"\n================ 第 {idx+1} 轮 ================\n")

    if not start:
        f.write("❌ 起始时间解析失败\n")
        return

    # ① 延迟
    if buzzers:
        print(buzzers[0], start)
        delay = (buzzers[0] - start).total_seconds()
        print(buzzers[0] - start)
        print(delay)
        f.write(f"① 蜂鸣器首次打开延迟: {delay:.2f} 秒\n")
    else:
        f.write("① 未检测到蜂鸣器\n")

    # ② 前2个SNR
    before = []
    if buzzers:
        bt = buzzers[0]
        before = [v for t, v in snrs if t <= bt]

        if len(before) >= 2:
            trigger_snrs = before[-2:]
        elif len(before) == 1:
            trigger_snrs = before
        else:
            trigger_snrs = []

    f.write(f"② 触发阈值SNR（最后两个）：{trigger_snrs}\n")

    # ③ 分段
    segments = {
        "0-7s": [],
        "8-10s": [],
        "11-13s": [],
        "14-20s": []
    }

    for t, v in snrs:
        sec = (t - start).total_seconds()

        if 0 <= sec <= 7:
            segments["0-7s"].append(v)
        elif 8 <= sec <= 10:
            segments["8-10s"].append(v)
        elif 11 <= sec <= 13:
            segments["11-13s"].append(v)
        elif 14 <= sec <= 20:
            segments["14-20s"].append(v)

    f.write("③ 分段平均SNR：\n")

    for k, vals in segments.items():
        if vals:
            avg = sum(vals) / len(vals)
            f.write(f"   {k}: {avg:.2f} (count={len(vals)})\n")
        else:
            f.write(f"   {k}: 无数据\n")



output_file = open("result.txt", "a", encoding="utf-8")
# =========================
# 执行
# =========================
for i, r in enumerate(rounds):
    compute(r, i, output_file)