#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zmq
import re
from collections import defaultdict

def host_sort_key(host: str):
    """
    将 host 名拆分为 (字母部分, 数字部分) 便于排序：
    如 "A05" -> ("A", 5)，"Pi10" -> ("Pi", 10)。
    """
    m = re.match(r'([A-Za-z]+)(\d+)', host)
    if m:
        return (m.group(1), int(m.group(2)))
    # 如果不符合，就整体作为字母部分
    return (host, 0)

def write_round_results(filename: str, rnd: int, msgs: dict):
    """
    把同一 round 内按 host 排序后的结果一次性写入文件。
    """
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"=== Round {rnd} ===\n")
        for host in sorted(msgs.keys(), key=host_sort_key):
            m = msgs[host]
            ts        = m["time"]
            Phi_CSI   = m["phi_csi"]
            avg_list  = m["avg_ampl"]
            # 这里只写 avg_list[0]，你也可以按需改写
            f.write(f"{ts} {host}: "
                    f"Phi_CSI={Phi_CSI:.6f}, "
                    f"avg_ampl={avg_list[0]:.6f}\n")
        f.write("\n")

def main():
    # ZeroMQ setup
    context = zmq.Context()
    pull    = context.socket(zmq.PULL)
    pull.bind("tcp://0.0.0.0:60000")

    results_file = "Processed_Result.txt"

    # 用来暂存每个 round 的 msg
    buffer_by_round = defaultdict(dict)
    current_round = None

    print("[PC] Waiting for metrics from Pis…")
    try:
        while True:
            msg = pull.recv_json()
            host      = msg["host"]
            rnd       = msg["round"]
            Phi_CSI   = msg["phi_csi"]
            circ_mean = msg["circ_mean"]
            mean_val  = msg["mean"]
            avg_list  = msg["avg_ampl"]
            ts        = msg["time"]

            # 实时打印
            print(f"[PC] {ts} {host} round {rnd}: "
                  f"Phi_CSI={Phi_CSI:.6f}, "
                  f"circ_mean={circ_mean:.6f}, "
                  f"mean={mean_val:.6f}, "
                  f"avg_ampl=[{avg_list[0]:.6f}, {avg_list[1]:.6f}]")

            # 缓存到当前 round
            buffer_by_round[rnd][host] = msg

            # 如果检测到 new round，先把上一轮写入
            if current_round is None:
                current_round = rnd
            elif rnd != current_round:
                write_round_results(results_file, current_round, buffer_by_round[current_round])
                # 清理上一轮缓存
                del buffer_by_round[current_round]
                current_round = rnd

    except KeyboardInterrupt:
        # 程序终止前，把最后一轮也写入
        if current_round in buffer_by_round:
            write_round_results(results_file, current_round, buffer_by_round[current_round])
        print("\n[PC] Stopped.")

    except Exception as e:
        print(f"[PC] Error: {e}")

if __name__ == "__main__":
    main()
