# crypto_watcher 加密监控脚本使用说明

## 安装依赖

```bash
# 安装Python库（推荐使用国内源加速）
pip install playwright -i https://pypi.tuna.tsinghua.edu.cn/simple


# 安装Google Chrome浏览器

```

> **注意**：脚本依赖系统已安装 **Google Chrome 浏览器**（非Edge、Brave等Chromium衍生版）

## 支持的加密类型

本脚本**仅支持标准加密库**，通过Hook全局对象实现监控：

### ✅ 支持的标准加密库
- **CryptoJS 全系列**：AES、DES、3DES、RC4、Rabbit、MD5、SHA1/224/256/384/512、HMAC系列
- **JSEncrypt (RSA)**：公钥加密/解密
- **国密算法**：
  - SM2：`sm2`、`GMSM2`、`window.SM2`
  - SM3：`sm3`、`GMSM3`、`window.SM3`  
  - SM4：`sm4`、`GMSM4`、`window.SM4`
- **Web Crypto API**：`window.crypto.subtle.encrypt/decrypt/digest`

### ❌ 不支持的情况
- **Webpack/模块化封装的加密函数**：加密逻辑被封装在模块内部，未暴露到全局对象
- **代码拷贝内联的加密实现**：将标准库代码复制到局部作用域，无全局引用
- **Web Worker 中的加密**：在独立线程中执行，主页面无法Hook
- **WebAssembly (WASM) 加密**：核心算法编译为二进制模块
- **深度混淆的自研加密算法**：无标准API调用特征

## 使用限制与注意事项

### 新标签页/页面跳转处理
- 脚本会自动对**所有新打开的页面**注入Hook脚本（包括`window.open()`、链接跳转等）
- **但仍需手动刷新新页面**以确保加密库已加载并被Hook捕获
- 原因：Hook脚本在页面加载前注入，但部分网站的加密库在用户交互后才动态加载

### 运行方式
```bash
# 命令行传入目标URL
python crypto_watcher.py https://example.com/login](https://config.net.cn/tools/Md5.html
```

### 输出内容
- **仅显示加解密详情**，不输出网络请求/响应数据包
- 实时监控控制台中的 `🎯 CRYPTO HOOK:` 消息

## 替代方案建议

当遇到以下情况时，建议改用其他方法：
1. **Hook失效** → 使用「明文输入监听 + 网络请求监听」的时序关联法
2. **确认使用标准算法** → 直接在本地环境（Python/Node.js）复现加密逻辑
3. **深度混淆场景** → 下载JS文件进行静态特征扫描分析
