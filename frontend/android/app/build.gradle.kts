plugins {
    id("com.android.application")
    id("kotlin-android")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "com.example.food_calorie_app"
    compileSdk = flutter.compileSdkVersion
    // Set ndkVersion only when flutter.ndkVersion is present and non-blank.
    // This avoids forcing a specific NDK that may not be installed on the build machine
    // while preserving the original intent when the value is available.
    try {
        val ndkVer: String? = flutter.ndkVersion
        if (ndkVer != null && ndkVer.isNotBlank()) {
            ndkVersion = ndkVer
        }
    } catch (e: Exception) {
        // swallow: if flutter.ndkVersion isn't available at configuration time,
        // don't set ndkVersion and allow the build system to use a system default.
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_11.toString()
    }

    defaultConfig {
        // TODO: Specify your own unique Application ID (https://developer.android.com/studio/build/application-id.html).
        applicationId = "com.example.food_calorie_app"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    buildTypes {
        release {
            // TODO: Add your own signing config for the release build.
            // Signing with the debug keys for now, so `flutter run --release` works.
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}

flutter {
    source = "../.."
}
