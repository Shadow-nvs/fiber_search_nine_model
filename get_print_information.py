# 当识别到KEY5时获取寻纤仪打印信息

import serial
import serial.tools.list_ports
import time
import os
import threading

os.system("chcp 65001")

# =============================
# 全局状态
# =============================
test_active = False
start_time = None

log_file = None
log_lock = threading.Lock()


# =============================
# 解码
# =============================
def decode_serial(data):
    try:
        return data.decode("utf-8")
    except:
        return data.decode("gbk", errors="ignore")


# =============================
# 写日志（线程安全）
# =============================
def write_log(text):
    global log_file
    with log_lock:
        print(text)
        if log_file:
            log_file.write(text + "\n")
            log_file.flush()


# =============================
# 夹纤器串口
# =============================
# def monitor_clamp_port(port):
#     global test_active, start_time, phase = 0

#     ser = serial.Serial(port, 115200, timeout=0)
#     print(f"[夹纤器 {port}] 已启动")

#     buffer = ""

#     while True:
#         try:
#             data = ser.read(ser.in_waiting or 1)
#             if data:
#                 buffer += decode_serial(data)

#                 while "\n" in buffer:
#                     line, buffer = buffer.split("\n", 1)
#                     line = line.strip()

#                     print(f"[夹纤器] {line}")

#                     # ===== 触发测试 =====
#                     if "KEY5" in line and not test_active:
#                         test_active = True
#                         start_time = time.time()

#                         # ===== 每轮分隔 =====
#                         write_log("\n\n=================================")
#                         write_log(f"新一轮测试开始: {time.strftime('%Y-%m-%d %H:%M:%S')}")
#                         write_log("=================================")

#                         ts = time.strftime("%H:%M:%S")
#                         write_log(f"[{ts}] [夹纤器] {line}")

#                         print("\n>>> KEY5 UP 触发，开始记录 <<<\n")

#                         ser.close()
#                         return

#         except Exception as e:
#             print(f"[夹纤器异常] {e}")

#         time.sleep(0.005)
def monitor_clamp_port(port):
    global test_active, start_time, phase

    ser = serial.Serial(port, 115200, timeout=0)
    print(f"[夹纤器 {port}] 已启动")

    buffer = ""

    while True:
        try:
            data = ser.read(ser.in_waiting or 1)
            if data:
                buffer += decode_serial(data)

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()

                    print(f"[夹纤器] {line}")

                    ts = time.strftime("%H:%M:%S")

                    # =============================
                    # 阶段0：等待 KEY5
                    # =============================
                    if phase == 0 and "KEY5" in line:
                        phase = 1
                        test_active = True
                        start_time = time.time()

                        write_log("\n\n=================================")
                        write_log(f"新一轮测试开始: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                        write_log("=================================")

                        write_log(f"[{ts}] [夹纤器] {line}")
                        print("\n>>> KEY5 触发，开始记录夹纤器 <<<\n")

                    # =============================
                    # 阶段1：记录夹纤器
                    # =============================
                    elif phase == 1:
                        write_log(f"[{ts}] [夹纤器] {line}")

                        # 👉 检测 KEY_BASE_START
                        if "KEY_BASE_START" in line:
                            phase = 2
                            # start_time = time.time()

                            write_log(f"[{ts}] [夹纤器] 收到 KEY_BASE_START，切换到寻纤仪记录")
                            print("\n>>> 切换到寻纤仪记录 <<<\n")

        except Exception as e:
            print(f"[夹纤器异常] {e}")

        time.sleep(0.005)


# =============================
# 寻纤仪串口
# =============================
# def monitor_finder_port(port):
#     global test_active, start_time

#     ser = serial.Serial(port, 115200, timeout=0)
#     print(f"[寻纤仪 {port}] 已启动")

#     buffer = ""

#     while True:
#         try:
#             data = ser.read(ser.in_waiting or 1)
#             if data:
#                 buffer += decode_serial(data)

#                 while "\n" in buffer:
#                     line, buffer = buffer.split("\n", 1)
#                     line = line.strip()

#                     now = time.time()

#                     # ===== 只在触发后记录 =====
#                     if test_active and start_time:
#                         elapsed = now - start_time

#                         ts = time.strftime("%H:%M:%S")
#                         write_log(f"[{ts}] [寻纤仪] {line}")

#                         # ===== 20秒结束 =====
#                         if elapsed >= 20:
#                             write_log("\n===== 20秒记录结束 =====\n")

#                             test_active = False
#                             start_time = None

#                             ser.close()
#                             return

#         except Exception as e:
#             print(f"[寻纤仪异常] {e}")

#         time.sleep(0.005)
def monitor_finder_port(port):
    global test_active, start_time, phase

    ser = serial.Serial(port, 115200, timeout=0)
    print(f"[寻纤仪 {port}] 已启动")

    buffer = ""

    while True:
        try:
            data = ser.read(ser.in_waiting or 1)
            if data:
                buffer += decode_serial(data)

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()

                    now = time.time()
                    ts = time.strftime("%H:%M:%S")

                    # =============================
                    # 只有阶段2才记录
                    # =============================
                    if phase == 2 and start_time:
                        write_log(f"[{ts}] [寻纤仪] {line}")

                        if now - start_time >= 20:
                            write_log("\n===== 20秒记录结束 =====\n")

                            # 重置状态
                            test_active = False
                            start_time = None
                            phase = 0

                            print("\n>>> 本轮结束 <<<\n")
                            return

        except Exception as e:
            print(f"[寻纤仪异常] {e}")

        time.sleep(0.005)


# =============================
# 主函数（循环测试核心）
# =============================
def main():
    global log_file, test_active, start_time, phase

    ports = list(serial.tools.list_ports.comports())

    for i, p in enumerate(ports):
        print(f"{i}: {p.device}")

    a = int(input("夹纤器串口: "))
    b = int(input("寻纤仪串口: "))

    clamp_port = ports[a].device
    finder_port = ports[b].device

    # =============================
    # 日志文件（只打开一次）
    # =============================
    log_file = open(f"all_merged_log.txt", "a", encoding="utf-8")
    write_log("\n\n==============================")
    write_log("程序启动")
    write_log("==============================\n")

    print("\n=== 等待 KEY5 UP 触发 ===\n")

    while True:

        # 重置状态
        test_active = False
        start_time = None

        # 启动线程
        t1 = threading.Thread(target=monitor_clamp_port, args=(clamp_port,))
        t2 = threading.Thread(target=monitor_finder_port, args=(finder_port,))

        t1.start()
        t2.start()

        # 等待本轮结束
        while True:
            if not t1.is_alive() and not t2.is_alive():
                break
            time.sleep(0.5)

        print("\n=== 本轮测试结束 ===")
        input(">>> 按 Enter 开始下一轮测试 <<<\n")


# =============================
# 启动
# =============================
if __name__ == "__main__":
    main()