# ⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE
# Consult an audiologist before using any hearing device.
# Use at your own risk. MIT Licensed.
#
# CMakeLists.txt — builds libopenhear_dsp.so for the OpenHear Android app.

cmake_minimum_required(VERSION 3.22)
project(openhear_dsp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# --------------------------------------------------------------------------
# Oboe — Google's low-latency audio library for Android.
# Fetched automatically via Gradle / prefab; fall back to FetchContent
# if building outside the Gradle wrapper.
# --------------------------------------------------------------------------
find_package(oboe REQUIRED CONFIG)

# --------------------------------------------------------------------------
# Shared library consumed by the Kotlin layer via System.loadLibrary().
# --------------------------------------------------------------------------
add_library(openhear_dsp SHARED
    openhear_dsp.cpp
)

target_link_libraries(openhear_dsp
    PRIVATE
        oboe::oboe
        android
        log
)

# Strip debug symbols in release for smaller APK.
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    set_target_properties(openhear_dsp PROPERTIES
        LINK_FLAGS "-s"
    )
endif()
