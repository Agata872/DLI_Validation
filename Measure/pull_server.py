#!/usr/bin/env python3
import zmq

def main():
    # ZeroMQ setup
    context = zmq.Context()
    pull    = context.socket(zmq.PULL)
    pull.bind("tcp://0.0.0.0:60000")

    # Open (or create) the result file
    results_file = "Processed_Result.txt"
    with open(results_file, "a") as f:
        print("[PC] Waiting for metrics from Pis…")
        try:
            while True:
                msg = pull.recv_json()
                host      = msg["host"]
                rnd       = msg["round"]
                Phi_CSI   = msg["phi_csi"]
                circ_mean = msg["circ_mean"]
                mean_val  = msg["mean"]
                avg_list  = msg["avg_ampl"]      # list of two floats
                ts        = msg["time"]

                # Print to console
                print(f"[PC] {ts} {host} round {rnd}: "
                      f"Phi_CSI={Phi_CSI:.6f}, "
                      f"circ_mean={circ_mean:.6f}, "
                      f"mean={mean_val:.6f}, "
                      f"avg_ampl=[{avg_list[0]:.6f}, {avg_list[1]:.6f}]")

                # Append to file
                f.write(f"{host}: "
                        f"Phi_CSI={Phi_CSI:.6f}, "
                        f"avg_ampl={avg_list[0]:.6f}\n")
                f.flush()
        except KeyboardInterrupt:
            print("\n[PC] Stopped.")
        except Exception as e:
            print(f"[PC] Error: {e}")

if __name__ == "__main__":
    main()