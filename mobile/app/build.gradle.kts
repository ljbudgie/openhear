// ⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE
// Consult an audiologist before using any hearing device.
// Use at your own risk. MIT Licensed.

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "org.openhear.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "org.openhear.app"
        minSdk = 26       // Android 8.0 — required for low-latency audio APIs
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"

        // NDK / CMake configuration for the Oboe-based native DSP library.
        externalNativeBuild {
            cmake {
                cppFlags += "-std=c++17"
                arguments += "-DANDROID_STL=c++_shared"
            }
        }

        ndk {
            // Build for common ABIs; add "x86" / "x86_64" for emulator testing.
            abiFilters += listOf("arm64-v8a", "armeabi-v7a")
        }
    }

    buildFeatures {
        compose = true
    }

    externalNativeBuild {
        cmake {
            path = file("src/main/cpp/CMakeLists.txt")
            version = "3.22.1"
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    // Jetpack Compose (BOM keeps versions aligned)
    val composeBom = platform("androidx.compose:compose-bom:2024.12.01")
    implementation(composeBom)
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    debugImplementation("androidx.compose.ui:ui-tooling")

    // Activity + Compose integration
    implementation("androidx.activity:activity-compose:1.9.3")

    // Core KTX
    implementation("androidx.core:core-ktx:1.15.0")

    // Oboe — low-latency audio (native library pulled via prefab)
    implementation("com.google.oboe:oboe:1.9.0")

    // JSON parsing (android.org.json is built-in; no extra dep needed)

    // Testing
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.6.1")
}
