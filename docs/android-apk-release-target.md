# Android APK 发布目标与终止条件

## 目标

移动端公共入口和登录注册页应优先提供 Android APK 下载，而不是 Windows 客户端下载。

目标下载地址：

`/downloads/LegalAI-Android-Client-v2.1.0.apk`

## 当前实现

- 手机宽度下显示 Android APK 下载入口。
- 桌面宽度下显示 Windows 客户端下载入口。
- Android 客户端位于 `client/android/`，定位为生产站点 WebView 壳。
- 默认打开 `https://fl.jilinpc.com`，服务器继续承载业务逻辑、模型调用和数据存储。
- 构建脚本：`scripts/build-android-client.ps1 -Version 2.1.0`
- APK 构建产物：`client/android/dist/LegalAI-Android-Client-v2.1.0.apk`
- 部署脚本会复制 APK 到 `frontend/dist/downloads/`，再同步到生产环境。

## 终止条件

1. 项目存在真实 APK 构建产物，不使用占位文件伪装 APK。
2. APK 包名、版本、SDK 范围可验证。
3. APK 签名校验通过，Android 设备可安装。
4. 移动端访问主页、三类入口、登录页、注册页时，客户端下载入口指向 APK。
5. 桌面端仍可下载 Windows zip。
6. 生产环境 `/downloads/LegalAI-Android-Client-v2.1.0.apk` 返回 `200` 且 `Content-Type` 合理。
7. 生产环境 `/downloads/LegalAI-Windows-Client-v2.1.0.zip` 仍返回 `200`。

## 当前 APK 性质

本阶段 APK 是 Android WebView 客户端壳，用于让手机用户安装后进入生产系统。它不是离线版法律大模型，也不在本机保存完整模型能力。

当前构建为 debug 签名 APK，适合内部下载验证和早期交付。若后续进入应用商店、企业分发或正式商业发布，应另起任务增加 release keystore、签名保管、版本升级和安装来源说明。
