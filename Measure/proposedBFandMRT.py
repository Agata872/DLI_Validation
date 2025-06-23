import numpy as np
import cvxpy as cp
import re

# %%
def CSIgenerator2(filename):
    """
    Reads CSI data from a text file and returns:
    - CSI_matrix: NumPy array of complex CSI values (1 per unique AP)
    - unique_APs: List of unique AP names (sorted by first appearance)

    Expected line format:
    "AP1: Phi_CSI=1.57, avg_ampl=0.93"
    """

    with open(filename, 'r') as file:
        lines = file.readlines()

    APs = []
    CSI = []

    pattern = re.compile(r'(\w+):\s*Phi_CSI=([-\d\.]+),\s*avg_ampl=([\d\.]+)')

    for line in lines:
        match = pattern.search(line)
        if match:
            ap_name = match.group(1)
            phi = float(match.group(2))
            ampl = float(match.group(3))

            APs.append(ap_name)
            CSI.append(ampl * np.exp(1j * phi))

    # Map unique APs to row indices
    unique_APs, idx_map = np.unique(APs, return_inverse=True)

    # Initialize CSI matrix
    CSI_matrix = np.zeros(len(unique_APs), dtype=complex)
    for i, val in enumerate(CSI):
        CSI_matrix[idx_map[i]] = val

    return CSI_matrix.reshape(-1, 1), list(unique_APs)

# %%
def dominant_eigenvector(X):
    # Compute the dominant eigenvector (eigenvector of the largest eigenvalue)
    eigvals, eigvecs = np.linalg.eigh(X)
    idx = np.argmax(eigvals)
    return eigvecs[:, idx]

# %%
def sdr_solver(H_DL, H_BD, M, scale, alpha, P_max):
    # Compute M_BD and M_DL
    M_BD = H_BD.conj().T @ H_BD
    M_DL = H_DL.conj().T @ H_DL
    
    # Define the semidefinite variable (Hermitian)
    X_new = cp.Variable((M, M), hermitian=True)
    
    # Objective: maximize scale * trace(M_BD * X_new)
    objective = cp.Maximize(scale * cp.real(cp.trace(M_BD @ X_new)))
    
    # Constraints
    constraints = [
        cp.real(cp.trace(scale * (M_DL - alpha * M_BD) @ X_new)) <= 0,
        X_new >> 0  # Hermitian positive semidefinite constraint
    ]

    # Add per-antenna power constraints
    for i in range(M):
        constraints.append(cp.real(X_new[i, i]) <= P_max)
    
    # Problem definition and solve
    prob = cp.Problem(objective, constraints)
    prob.solve(solver=cp.SCS, verbose=False)  # You can try other solvers, e.g., 'CVXOPT' or 'MOSEK'
    
    if X_new.value is None:
        raise ValueError("Optimization did not converge.")
    
    # Extract dominant eigenvector
    w_optimum = dominant_eigenvector(X_new.value)
    
    # Normalize the beamforming vector
    w = w_optimum / np.linalg.norm(w_optimum)
    
    # print(f"\nCVX Solution for alpha = {alpha}")
    
    # # Compute constraint and objective values
    # const = (np.linalg.norm(H_DL @ w) / np.linalg.norm(H_BD @ w))**2
    # obj = (np.linalg.norm(H_BD @ w))**2
    
    # print(f"Prop.: Constraint is {const:.9f}")
    # print(f"Prop.: Objective is {obj:.9f}\n")
    
    return w


def compute_bf_phases(
    bf_type: str,
    alpha: float,
    scale: float,
    f_c: float,
    file_bd: str,
    file_reader: str,
    write_output: bool = False
):
    # Read the channel data
   h_C, unique_APs = CSIgenerator2(file_bd)
   H_DL, _ = CSIgenerator2(file_reader)

   # Ensure H_DL is a row vector
   if H_DL.shape[0] != 1:
       H_DL = H_DL.T

   # Constants
   c = 3e8  # Speed of light in m/s
   _lambda = c / f_c  # Wavelength

   # Distance and channel
   distance = 1
   h_R = _lambda / (4 * np.pi * distance)
   h_R = np.array([h_R])[:, np.newaxis]

   # Channels
   H_BD = h_R * h_C.T

   # Dimensions
   M = len(h_C)
   N = len(h_R) 
   P_max = 1

   # Beamforming
   if bf_type.lower() == "cvx":
       w = sdr_solver(H_DL, H_BD, M, scale, alpha, P_max)
   elif bf_type.lower() == "mrt":
       w = np.conj(h_C) / np.abs(h_C)
       w = w / np.linalg.norm(w)
   else:
       raise ValueError("Unsupported BF type. Use 'cvx' or 'mrt'.")

   # Extract phase
   w_angle = np.angle(w)
   
   # Compute constraint and objective values
   const = (np.linalg.norm(H_DL @ w) / np.linalg.norm(H_BD @ w))**2
   obj = (np.linalg.norm(H_BD @ w))**2
      
   print(f"Constraint is {const:.9f}")
   print(f"Objective is {obj:.9f}\n")

   # Write to file if requested
   if write_output:
       filename = 'Proposed_BF.txt' if bf_type.lower() == 'cvx' else 'MRT_BF.txt'
       with open(filename, 'w') as f:
           for name, angle in zip(unique_APs, w_angle):
               f.write(f'{name}: {angle.item():.8f}\n')

   return w_angle, unique_APs


phases, AP_list = compute_bf_phases(
    bf_type='cvx',
    alpha=0,
    scale=1e1,
    f_c=0.92e9,
    file_bd='Processed_Result_BD.txt',
    file_reader='Processed_Result_Reader.txt',
    write_output=True
)



# # %% Read the channel data

# h_C, unique_APs = CSIgenerator2('Processed_Result_BD.txt')
# H_DL, unique_APs = CSIgenerator2('Processed_Result_Reader.txt')

# # If H_DL is not a row vector, transpose it
# if H_DL.shape[0] != 1:
#     H_DL = H_DL.T
    
# # Constants
# f_c = 0.92e9       # Hz
# c = 3e8            # Speed of light in m/s
# _lambda = c / f_c  # Wavelength

# # Distance and channel
# distance = 1
# h_R = _lambda / (4 * np.pi * distance)
# h_R = np.array([h_R])[:, np.newaxis]

# # Channels
# H_BD = h_R * h_C.T

# # Dimensions
# M = len(h_C)  # or h_C.shape[0]
# N = len(h_R)         # h_R is scalar


# # %% Parameters
# P_max = 1
# scale = 1e2
# alpha = 0

# # %% Proposed Method - CVX (MOSEK)
# w_cvx = sdr_solver(H_DL, H_BD, M, scale, alpha, P_max)

# # %% Benchmark - MRT

# w_mrt = np.conj(h_C) / np.abs(h_C)
# w_mrt = w_mrt / np.linalg.norm(w_mrt)

# # Compute constraint and objective values
# const_mrt = (np.linalg.norm(H_DL @ w_mrt) / np.linalg.norm(H_BD @ w_mrt))**2
# obj_mrt = (np.linalg.norm(H_BD @ w_mrt))**2
   
# print(f"MRT: Constraint is {const_mrt:.9f}")
# print(f"MRT: Objective is {obj_mrt:.9f}\n")

# # %%

# w_cvx_angle = np.angle(w_cvx);
# w_mrt_angle = np.angle(w_mrt);


# # Write Proposed_BF.txt
# with open('Proposed_BF.txt', 'w') as f:
#     for name, angle in zip(unique_APs, w_cvx_angle):
#         f.write(f'{name}: {angle.item():.8f}\n')

# # Write MRT_BF.txt
# with open('MRT_BF.txt', 'w') as f:
#     for name, angle in zip(unique_APs, w_mrt_angle):
#         f.write(f'{name}: {angle.item():.8f}\n')

