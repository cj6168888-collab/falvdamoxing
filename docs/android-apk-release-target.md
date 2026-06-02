# Android APK 发布目标与终止条件

## 目标

移动端公共入口和登录注册页应优先提供 Android APK 下载，而不是 Windows 客户端下载。

目标下载地址：

`/downloads/LegalAI-Android-Client-v2.1.0.apk`

## 当前实现

- 手机宽度下显示“下载 Android APK”。
- 桌面宽度下显示“下载 Windows 客户端”。
- 部署脚本会在前端构建后尝试复制 APK 到 `frontend/dist/downloads/`。
- APK 源文件候选路径：
  - `client/android/dist/LegalAI-Android-Client-v2.1.0.apk`
  - `client/dist-android/LegalAI-Android-Client-v2.1.0.apk`
  - `client/mobile/LegalAI-Android-Client-v2.1.0.apk`

## 终止条件

1. 项目存在真实 APK 构建产物，不使用占位文件伪装 APK。
2. 移动端访问主页、三类入口、登录页、注册页时，客户端下载入口指向 APK。
3. 桌面端仍可下载 Windows zip。
4. 生产环境 `/downloads/LegalAI-Android-Client-v2.1.0.apk` 返回 `200` 且 `Content-Type` 合理。
5. Windows zip 下载仍返回 `200`。

## 当前缺口

本机当前没有 Android SDK、Gradle 或 APK 构建产物，因此本轮只完成入口和部署支持，不伪造 APK。
