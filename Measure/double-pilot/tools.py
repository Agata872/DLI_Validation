from scipy.signal import butter, sosfilt
from scipy import stats
import numpy as np
import scipy.signal as signal


def circmean(arr, deg=True):

    arr = np.asarray(arr)
    if deg:
        arr = np.deg2rad(arr)

    _circmean = np.angle(np.sum(np.exp(1j * arr)))

    return np.rad2deg(_circmean) if deg else _circmean
def circstd(arr, deg=True):
    arr = np.asarray(arr)
    if deg:
        arr = np.deg2rad(arr)
    R = np.abs(np.sum(np.exp(1j * arr))) / len(arr)
    std = np.sqrt(-2 * np.log(R))
    return np.rad2deg(std) if deg else std


def to_min_pi_plus_pi(angles, deg=True):

    angles = np.asarray(angles)

    thr = 180.0 if deg else np.pi / 2
    rotate = 360.0 if deg else 2 * np.pi

    # ensure positive
    idx = angles < 0.0
    angles[idx] = angles[idx] + rotate

    # ensure betwen -180 and 180 or -pi and pi
    idx = angles > thr
    angles[idx] = angles[idx] - rotate

    return angles

f0 = 1e3
cutoff = 100
lowcut = f0 - cutoff
highcut = f0 + cutoff


# Function to apply a bandpass filter to the IQ data
def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    sos = signal.butter(order, [low, high], btype="band", output="sos")
    return sos


# Function to apply the bandpass filter
def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    sos = butter_bandpass(lowcut, highcut, fs, order)
    return signal.sosfilt(sos, data)


# def butter_bandpass(lowcut, highcut, fs, order=5):
#     nyq = 0.5 * fs
#     low = lowcut / nyq
#     high = highcut / nyq
#     sos = butter(order, [low, high], analog=False, btype="band", output="sos")
#     return sos


# def butter_bandpass_filter(data, lowcut, highcut, fs, order=5, sos=None):
#     if sos is None:
#         sos = butter_bandpass(lowcut, highcut, fs, order=order)
#     y = sosfilt(sos, data)
#     return y


def compute_phase_difference(iq_data, fs):
    # ALERT channel phases are rotated, previously 0-1, now 1-0, according to my paper.

    # Apply bandpass filter to the real and imaginary parts
    iq_filtered = butter_bandpass_filter(iq_data, lowcut, highcut, fs)

    # Calculate the phase of the filtered IQ data
    phase = np.angle(iq_filtered)

    # Calculate the phase difference between channels A and B (CH0 and CH1)
    phase_diff = phase[1, :] - phase[0, :] #TODO removed unwarp

    # phase_diff = np.unwrap(phase[1, :]) - np.unwrap(phase[0, :])

    return phase_diff


# def apply_bandpass(x: np.ndarray, fs=250e3):
#     sos = butter_bandpass(lowcut, highcut, fs, order=9)

#     y_re = butter_bandpass_filter(np.real(x), lowcut, highcut, fs, order=9, sos=sos)
#     y_imag = butter_bandpass_filter(np.imag(x), lowcut, highcut, fs, order=9, sos=sos)

#     return y_re + 1j * y_imag


# def get_phases_and_apply_bandpass(x: np.ndarray, fs=250e3):
#     sos = butter_bandpass(lowcut, highcut, fs, order=9)

#     y_re = butter_bandpass_filter(np.real(x), lowcut, highcut, fs, order=9, sos=sos)
#     y_imag = butter_bandpass_filter(np.imag(x), lowcut, highcut, fs, order=9, sos=sos)

#     return np.angle(y_re + 1j * y_imag), 0  # legacy


# def get_phases_and_remove_CFO(x, fs=250e3, remove_first_samples=True):

#     sos = butter_bandpass(lowcut, highcut, fs, order=9)
#     y_re = butter_bandpass_filter(np.real(x), lowcut, highcut, fs, order=9, sos=sos)
#     y_imag = butter_bandpass_filter(np.imag(x), lowcut, highcut, fs, order=9, sos=sos)

#     # return np.angle(y_re + 1j * y_imag)

#     angle_unwrapped = np.unwrap(np.angle(y_re + 1j * y_imag))
#     t = np.arange(0, len(y_re)) * (1 / fs)

#     lin_regr = stats.linregress(t, angle_unwrapped)
#     angles = angle_unwrapped - lin_regr.slope * t
#     return angles[5000:] if remove_first_samples else angles
