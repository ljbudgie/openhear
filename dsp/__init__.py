"""
dsp package – digital signal processing pipeline for OpenHear.

Provides the real-time audio processing loop together with individual
DSP stages: Wide Dynamic Range Compression, spectral-subtraction noise
reduction, and speech frequency emphasis.

All user-tunable parameters live in dsp/config.py as plain Python
constants so they can be edited without touching algorithm code.
"""
