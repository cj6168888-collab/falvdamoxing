# Legal AI Android Client

This is a minimal Android WebView shell for the production Legal AI service.

- App URL: `https://fl.jilinpc.com`
- Package id: `com.legalai.client`
- APK output expected by release scripts: `client/android/dist/LegalAI-Android-Client-v2.1.0.apk`

Build from the repository root:

```powershell
scripts\build-android-client.ps1 -Version 2.1.0
```

The build script downloads Gradle and Android command-line tools into local ignored folders, installs SDK packages, builds a debug APK, and copies it to `client/android/dist/`.

This APK is an installable client shell, not a standalone offline legal system. Server logic and model calls still run on `fl.jilinpc.com`.
