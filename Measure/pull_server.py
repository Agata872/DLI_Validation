#!/usr/bin/env python3
import zmq

def main():
    # ZMQ 上下文
    context = zmq.Context()
    # PULL 套接字绑定在 60000 端口，收集所有 Pi 推送的数据
    pull = context.socket(zmq.PULL)
    pull.bind("tcp://0.0.0.0:60000")

    print("[PC] 等待来自 Pi 的数据推送...")
    while True:
        try:
            # 接收 JSON 格式的数据
            msg = pull.recv_json()
            # 打印或进一步处理
            host = msg.get("host")
            rnd  = msg.get("round")
            phi  = msg.get("phi")
            ts   = msg.get("time")
            print(f"[PC] 接收到 \"{host}\" 第{rnd}轮测量: phi={phi:.6f}, time={ts}")
            # TODO: 保存到文件或数据库
        except KeyboardInterrupt:
            print("[PC] 终止接收。")
            break
        except Exception as e:
            print(f"[PC] 处理消息时出错: {e}")

if __name__ == '__main__':
    main()