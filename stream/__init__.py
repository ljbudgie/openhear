"""
stream package – Bluetooth audio output for OpenHear.

Routes processed audio from the DSP pipeline to paired hearing aids via
the system Bluetooth stack.  Phase 1 uses the OS audio device abstraction
(no direct Bluetooth HCI commands) so that the streamer works on Windows 11
without requiring a custom driver.
"""
