import json
import time
from urllib.parse import unquote, parse_qs
from playwright.sync_api import sync_playwright
import os
import sys

class RequestInterceptor:
    def __init__(self):
        self.packet_count = 0
        self.crypto_hook_count = 0
        # 静态资源文件扩展名列表
        self.static_extensions = {
            '.js', '.css', '.html', '.htm', '.png', '.jpg', '.jpeg', '.gif', '.ico', 
            '.svg', '.woff', '.woff2', '.ttf', '.eot', '.mp4', '.mp3', '.pdf', '.txt',
            '.map', '.json', '.xml', '.webp', '.avif'
        }
        
    def is_static_resource(self, url):
        """判断URL是否为静态资源文件 - 仅基于文件扩展名"""
        url_lower = url.lower()
        # 只检查文件扩展名，不检查目录路径（避免误过滤）
        for ext in self.static_extensions:
            if url_lower.endswith(ext):
                return True
        return False
    
    def print_complete_packet(self, request, response):
        """打印完整的请求-响应数据包 - 已禁用"""
        # 此功能已按需求禁用，不再输出任何请求响应数据包
        pass
        
    def handle_crypto_console_message(self, msg_text):
        """处理加密相关的控制台消息"""
        try:
            if '🎯 CRYPTO HOOK:' in msg_text:
                self.crypto_hook_count += 1
                # 解析加密信息并格式化输出
                crypto_info = msg_text.replace('🎯 CRYPTO HOOK: ', '')
                print(f"\n加解密详情 #{self.crypto_hook_count}", flush=True)
                print(f"{crypto_info}", flush=True)
                print("-" * 50, flush=True)
        except Exception as e:
            print(f"❌ Error handling crypto message: {str(e)}", flush=True)
    
    def save_traffic(self, filename="captured_traffic.json"):
        """保存捕获的数据到文件（简化版）"""
        print(f"\n💾 加解密监控完成。共捕获 {self.crypto_hook_count} 条加解密操作", flush=True)

def main(target_url):
    interceptor = RequestInterceptor()
    
    with sync_playwright() as p:
        # 启动浏览器，忽略 HTTPS 错误
        browser = p.chromium.launch(
            channel="chrome", 
            headless=False,
            args=[
                "--ignore-certificate-errors",
                "--disable-web-security",
                "--allow-running-insecure-content",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=WebRTC",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        
        try:
            # 创建上下文 - 使用更真实的浏览器指纹
            context_options = {
                "viewport": {"width": 1280, "height": 800},
                "ignore_https_errors": True,
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                "bypass_csp": True,
                "java_script_enabled": True,
                "accept_downloads": False,
                "locale": "zh-CN",
                "timezone_id": "Asia/Shanghai",
                "permissions": [],
                "extra_http_headers": {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1"
                }
            }
            
            context = browser.new_context(**context_options)
            
            # 创建新页面
            page = context.new_page()
            
            # 访问目标网站（从命令行参数传入）
            print(f"打开目标网址: {target_url}", flush=True)
            print("开始监控加解密操作...", flush=True)
            print("仅显示加解密详情，不显示网络数据包", flush=True)
            
            # 注入改进的加密Hook脚本 - 合并完整输出
            crypto_hook_script = """
            // 改进的Hook策略 - 合并完整加密信息
            setTimeout(function() {
                // Hook CryptoJS 全系列
                if (typeof CryptoJS !== 'undefined') {
                    console.log('🎯 CRYPTO HOOK: Full CryptoJS hook active');
                    
                    // AES - 加密和解密
                    if (CryptoJS.AES && CryptoJS.AES.encrypt) {
                        const originalAESEncrypt = CryptoJS.AES.encrypt;
                        CryptoJS.AES.encrypt = function(message, key, cfg) {
                            let mode = 'CBC';
                            let ivInfo = 'None';
                            let keyInfo = typeof key === 'string' ? 'String: ' + key : 'WordArray: ' + (key?.toString() || 'Unknown');
                            
                            if (cfg) {
                                if (cfg.mode) {
                                    mode = cfg.mode.toString().toUpperCase();
                                    if (mode === '[OBJECT OBJECT]') {
                                        if (cfg.mode === CryptoJS.mode.CBC) mode = 'CBC';
                                        else if (cfg.mode === CryptoJS.mode.ECB) mode = 'ECB';
                                        else mode = 'UNKNOWN';
                                    }
                                }
                                if (cfg.iv) {
                                    ivInfo = typeof cfg.iv === 'string' ? 'String: ' + cfg.iv : 'WordArray: ' + cfg.iv.toString();
                                }
                            }
                            
                            let messageInfo = typeof message === 'string' ? message : message?.toString() || 'Object';
                            const result = originalAESEncrypt.apply(this, arguments);
                            
                            console.log('🎯 CRYPTO HOOK: Algorithm: AES-Encrypt | Mode: ' + mode + ' | Key: ' + keyInfo + ' | IV: ' + ivInfo + ' | Plaintext: ' + messageInfo + ' | Result: ' + result.toString());
                            return result;
                        };
                    }
                    
                    if (CryptoJS.AES && CryptoJS.AES.decrypt) {
                        const originalAESDecrypt = CryptoJS.AES.decrypt;
                        CryptoJS.AES.decrypt = function(ciphertext, key, cfg) {
                            let mode = 'CBC';
                            let ivInfo = 'None';
                            let keyInfo = typeof key === 'string' ? 'String: ' + key : 'WordArray: ' + (key?.toString() || 'Unknown');
                            
                            if (cfg) {
                                if (cfg.mode) {
                                    mode = cfg.mode.toString().toUpperCase();
                                    if (mode === '[OBJECT OBJECT]') {
                                        if (cfg.mode === CryptoJS.mode.CBC) mode = 'CBC';
                                        else if (cfg.mode === CryptoJS.mode.ECB) mode = 'ECB';
                                        else mode = 'UNKNOWN';
                                    }
                                }
                                if (cfg.iv) {
                                    ivInfo = typeof cfg.iv === 'string' ? 'String: ' + cfg.iv : 'WordArray: ' + cfg.iv.toString();
                                }
                            }
                            
                            let ciphertextInfo = typeof ciphertext === 'string' ? ciphertext : ciphertext?.toString() || 'Object';
                            const result = originalAESDecrypt.apply(this, arguments);
                            
                            console.log('🎯 CRYPTO HOOK: Algorithm: AES-Decrypt | Mode: ' + mode + ' | Key: ' + keyInfo + ' | IV: ' + ivInfo + ' | Ciphertext: ' + ciphertextInfo + ' | Result: ' + result.toString());
                            return result;
                        };
                    }
                    
                    // DES - 加密和解密
                    if (CryptoJS.DES && CryptoJS.DES.encrypt) {
                        const originalDESEncrypt = CryptoJS.DES.encrypt;
                        CryptoJS.DES.encrypt = function(message, key, cfg) {
                            let mode = 'ECB';
                            let ivInfo = 'None';
                            let keyInfo = typeof key === 'string' ? 'String: ' + key : 'WordArray: ' + (key?.toString() || 'Unknown');
                            
                            if (cfg) {
                                if (cfg.mode) {
                                    mode = cfg.mode.toString().toUpperCase();
                                    if (mode === '[OBJECT OBJECT]') {
                                        if (cfg.mode === CryptoJS.mode.CBC) mode = 'CBC';
                                        else if (cfg.mode === CryptoJS.mode.ECB) mode = 'ECB';
                                        else mode = 'UNKNOWN';
                                    }
                                }
                                if (cfg.iv) {
                                    ivInfo = typeof cfg.iv === 'string' ? 'String: ' + cfg.iv : 'WordArray: ' + cfg.iv.toString();
                                }
                            }
                            
                            let messageInfo = typeof message === 'string' ? message : message?.toString() || 'Object';
                            const result = originalDESEncrypt.apply(this, arguments);
                            
                            console.log('🎯 CRYPTO HOOK: Algorithm: DES-Encrypt | Mode: ' + mode + ' | Key: ' + keyInfo + ' | IV: ' + ivInfo + ' | Plaintext: ' + messageInfo + ' | Result: ' + result.toString());
                            return result;
                        };
                    }
                    
                    if (CryptoJS.DES && CryptoJS.DES.decrypt) {
                        const originalDESDecrypt = CryptoJS.DES.decrypt;
                        CryptoJS.DES.decrypt = function(ciphertext, key, cfg) {
                            let mode = 'ECB';
                            let ivInfo = 'None';
                            let keyInfo = typeof key === 'string' ? 'String: ' + key : 'WordArray: ' + (key?.toString() || 'Unknown');
                            
                            if (cfg) {
                                if (cfg.mode) {
                                    mode = cfg.mode.toString().toUpperCase();
                                    if (mode === '[OBJECT OBJECT]') {
                                        if (cfg.mode === CryptoJS.mode.CBC) mode = 'CBC';
                                        else if (cfg.mode === CryptoJS.mode.ECB) mode = 'ECB';
                                        else mode = 'UNKNOWN';
                                    }
                                }
                                if (cfg.iv) {
                                    ivInfo = typeof cfg.iv === 'string' ? 'String: ' + cfg.iv : 'WordArray: ' + cfg.iv.toString();
                                }
                            }
                            
                            let ciphertextInfo = typeof ciphertext === 'string' ? ciphertext : ciphertext?.toString() || 'Object';
                            const result = originalDESDecrypt.apply(this, arguments);
                            
                            console.log('🎯 CRYPTO HOOK: Algorithm: DES-Decrypt | Mode: ' + mode + ' | Key: ' + keyInfo + ' | IV: ' + ivInfo + ' | Ciphertext: ' + ciphertextInfo + ' | Result: ' + result.toString());
                            return result;
                        };
                    }
                    
                    // TripleDES - 加密和解密
                    if (CryptoJS.TripleDES && CryptoJS.TripleDES.encrypt) {
                        const originalTripleDESEncrypt = CryptoJS.TripleDES.encrypt;
                        CryptoJS.TripleDES.encrypt = function(message, key, cfg) {
                            let mode = 'ECB';
                            let ivInfo = 'None';
                            let keyInfo = typeof key === 'string' ? 'String: ' + key : 'WordArray: ' + (key?.toString() || 'Unknown');
                            
                            if (cfg) {
                                if (cfg.mode) {
                                    mode = cfg.mode.toString().toUpperCase();
                                    if (mode === '[OBJECT OBJECT]') {
                                        if (cfg.mode === CryptoJS.mode.CBC) mode = 'CBC';
                                        else if (cfg.mode === CryptoJS.mode.ECB) mode = 'ECB';
                                        else mode = 'UNKNOWN';
                                    }
                                }
                                if (cfg.iv) {
                                    ivInfo = typeof cfg.iv === 'string' ? 'String: ' + cfg.iv : 'WordArray: ' + cfg.iv.toString();
                                }
                            }
                            
                            let messageInfo = typeof message === 'string' ? message : message?.toString() || 'Object';
                            const result = originalTripleDESEncrypt.apply(this, arguments);
                            
                            console.log('🎯 CRYPTO HOOK: Algorithm: 3DES-Encrypt | Mode: ' + mode + ' | Key: ' + keyInfo + ' | IV: ' + ivInfo + ' | Plaintext: ' + messageInfo + ' | Result: ' + result.toString());
                            return result;
                        };
                    }
                    
                    if (CryptoJS.TripleDES && CryptoJS.TripleDES.decrypt) {
                        const originalTripleDESDecrypt = CryptoJS.TripleDES.decrypt;
                        CryptoJS.TripleDES.decrypt = function(ciphertext, key, cfg) {
                            let mode = 'ECB';
                            let ivInfo = 'None';
                            let keyInfo = typeof key === 'string' ? 'String: ' + key : 'WordArray: ' + (key?.toString() || 'Unknown');
                            
                            if (cfg) {
                                if (cfg.mode) {
                                    mode = cfg.mode.toString().toUpperCase();
                                    if (mode === '[OBJECT OBJECT]') {
                                        if (cfg.mode === CryptoJS.mode.CBC) mode = 'CBC';
                                        else if (cfg.mode === CryptoJS.mode.ECB) mode = 'ECB';
                                        else mode = 'UNKNOWN';
                                    }
                                }
                                if (cfg.iv) {
                                    ivInfo = typeof cfg.iv === 'string' ? 'String: ' + cfg.iv : 'WordArray: ' + cfg.iv.toString();
                                }
                            }
                            
                            let ciphertextInfo = typeof ciphertext === 'string' ? ciphertext : ciphertext?.toString() || 'Object';
                            const result = originalTripleDESDecrypt.apply(this, arguments);
                            
                            console.log('🎯 CRYPTO HOOK: Algorithm: 3DES-Decrypt | Mode: ' + mode + ' | Key: ' + keyInfo + ' | IV: ' + ivInfo + ' | Ciphertext: ' + ciphertextInfo + ' | Result: ' + result.toString());
                            return result;
                        };
                    }
                    
                    // RC4 - 加密和解密（RC4通常使用相同方法）
                    if (CryptoJS.RC4) {
                        const originalRC4 = CryptoJS.RC4.encrypt || CryptoJS.RC4;
                        CryptoJS.RC4.encrypt = function(message, key) {
                            const result = originalRC4.apply(this, arguments);
                            console.log('🎯 CRYPTO HOOK: Algorithm: RC4-Encrypt | Message: ' + (typeof message === 'string' ? message : message?.toString() || 'Object') + ' | Key: ' + (typeof key === 'string' ? key : key?.toString() || 'Object') + ' | Result: ' + result.toString());
                            return result;
                        };
                        if (typeof CryptoJS.RC4 === 'function') {
                            CryptoJS.RC4 = function(message, key) {
                                const result = originalRC4.apply(this, arguments);
                                console.log('🎯 CRYPTO HOOK: Algorithm: RC4-Encrypt | Message: ' + (typeof message === 'string' ? message : message?.toString() || 'Object') + ' | Key: ' + (typeof key === 'string' ? key : key?.toString() || 'Object') + ' | Result: ' + result.toString());
                                return result;
                            };
                        }
                    }
                    
                    // Rabbit - 加密和解密
                    if (CryptoJS.Rabbit && CryptoJS.Rabbit.encrypt) {
                        const originalRabbitEncrypt = CryptoJS.Rabbit.encrypt;
                        CryptoJS.Rabbit.encrypt = function(message, key, cfg) {
                            let ivInfo = 'None';
                            let keyInfo = typeof key === 'string' ? 'String: ' + key : 'WordArray: ' + (key?.toString() || 'Unknown');
                            
                            if (cfg && cfg.iv) {
                                ivInfo = typeof cfg.iv === 'string' ? 'String: ' + cfg.iv : 'WordArray: ' + cfg.iv.toString();
                            }
                            
                            let messageInfo = typeof message === 'string' ? message : message?.toString() || 'Object';
                            const result = originalRabbitEncrypt.apply(this, arguments);
                            
                            console.log('🎯 CRYPTO HOOK: Algorithm: Rabbit-Encrypt | Key: ' + keyInfo + ' | IV: ' + ivInfo + ' | Plaintext: ' + messageInfo + ' | Result: ' + result.toString());
                            return result;
                        };
                    }
                    
                    if (CryptoJS.Rabbit && CryptoJS.Rabbit.decrypt) {
                        const originalRabbitDecrypt = CryptoJS.Rabbit.decrypt;
                        CryptoJS.Rabbit.decrypt = function(ciphertext, key, cfg) {
                            let ivInfo = 'None';
                            let keyInfo = typeof key === 'string' ? 'String: ' + key : 'WordArray: ' + (key?.toString() || 'Unknown');
                            
                            if (cfg && cfg.iv) {
                                ivInfo = typeof cfg.iv === 'string' ? 'String: ' + cfg.iv : 'WordArray: ' + cfg.iv.toString();
                            }
                            
                            let ciphertextInfo = typeof ciphertext === 'string' ? ciphertext : ciphertext?.toString() || 'Object';
                            const result = originalRabbitDecrypt.apply(this, arguments);
                            
                            console.log('🎯 CRYPTO HOOK: Algorithm: Rabbit-Decrypt | Key: ' + keyInfo + ' | IV: ' + ivInfo + ' | Ciphertext: ' + ciphertextInfo + ' | Result: ' + result.toString());
                            return result;
                        };
                    }
                    
                    // Hash functions - 完整SHA系列支持
                    if (CryptoJS.MD5) {
                        const originalMD5 = CryptoJS.MD5;
                        CryptoJS.MD5 = function(message) {
                            const result = originalMD5.apply(this, arguments);
                            console.log('🎯 CRYPTO HOOK: Algorithm: MD5 | Input: ' + (typeof message === 'string' ? message : message?.toString() || 'Object') + ' | Result: ' + result.toString());
                            return result;
                        };
                    }
                    
                    if (CryptoJS.SHA1) {
                        const originalSHA1 = CryptoJS.SHA1;
                        CryptoJS.SHA1 = function(message) {
                            const result = originalSHA1.apply(this, arguments);
                            console.log('🎯 CRYPTO HOOK: Algorithm: SHA1 | Input: ' + (typeof message === 'string' ? message : message?.toString() || 'Object') + ' | Result: ' + result.toString());
                            return result;
                        };
                    }
                    
                    if (CryptoJS.SHA224) {
                        const originalSHA224 = CryptoJS.SHA224;
                        CryptoJS.SHA224 = function(message) {
                            const result = originalSHA224.apply(this, arguments);
                            console.log('🎯 CRYPTO HOOK: Algorithm: SHA224 | Input: ' + (typeof message === 'string' ? message : message?.toString() || 'Object') + ' | Result: ' + result.toString());
                            return result;
                        };
                    }
                    
                    if (CryptoJS.SHA256) {
                        const originalSHA256 = CryptoJS.SHA256;
                        CryptoJS.SHA256 = function(message) {
                            const result = originalSHA256.apply(this, arguments);
                            console.log('🎯 CRYPTO HOOK: Algorithm: SHA256 | Input: ' + (typeof message === 'string' ? message : message?.toString() || 'Object') + ' | Result: ' + result.toString());
                            return result;
                        };
                    }
                    
                    if (CryptoJS.SHA384) {
                        const originalSHA384 = CryptoJS.SHA384;
                        CryptoJS.SHA384 = function(message) {
                            const result = originalSHA384.apply(this, arguments);
                            console.log('🎯 CRYPTO HOOK: Algorithm: SHA384 | Input: ' + (typeof message === 'string' ? message : message?.toString() || 'Object') + ' | Result: ' + result.toString());
                            return result;
                        };
                    }
                    
                    if (CryptoJS.SHA512) {
                        const originalSHA512 = CryptoJS.SHA512;
                        CryptoJS.SHA512 = function(message) {
                            const result = originalSHA512.apply(this, arguments);
                            console.log('🎯 CRYPTO HOOK: Algorithm: SHA512 | Input: ' + (typeof message === 'string' ? message : message?.toString() || 'Object') + ' | Result: ' + result.toString());
                            return result;
                        };
                    }
                    
                    // HMAC - 完整支持所有算法变体
                    if (CryptoJS.HmacMD5) {
                        const originalHmacMD5 = CryptoJS.HmacMD5;
                        CryptoJS.HmacMD5 = function(message, key) {
                            const result = originalHmacMD5.apply(this, arguments);
                            console.log('🎯 CRYPTO HOOK: Algorithm: HMAC-MD5 | Message: ' + (typeof message === 'string' ? message : message?.toString() || 'Object') + ' | Key: ' + (typeof key === 'string' ? key : key?.toString() || 'Object') + ' | Result: ' + result.toString());
                            return result;
                        };
                    }
                    
                    if (CryptoJS.HmacSHA1) {
                        const originalHmacSHA1 = CryptoJS.HmacSHA1;
                        CryptoJS.HmacSHA1 = function(message, key) {
                            const result = originalHmacSHA1.apply(this, arguments);
                            console.log('🎯 CRYPTO HOOK: Algorithm: HMAC-SHA1 | Message: ' + (typeof message === 'string' ? message : message?.toString() || 'Object') + ' | Key: ' + (typeof key === 'string' ? key : key?.toString() || 'Object') + ' | Result: ' + result.toString());
                            return result;
                        };
                    }
                    
                    if (CryptoJS.HmacSHA224) {
                        const originalHmacSHA224 = CryptoJS.HmacSHA224;
                        CryptoJS.HmacSHA224 = function(message, key) {
                            const result = originalHmacSHA224.apply(this, arguments);
                            console.log('🎯 CRYPTO HOOK: Algorithm: HMAC-SHA224 | Message: ' + (typeof message === 'string' ? message : message?.toString() || 'Object') + ' | Key: ' + (typeof key === 'string' ? key : key?.toString() || 'Object') + ' | Result: ' + result.toString());
                            return result;
                        };
                    }
                    
                    if (CryptoJS.HmacSHA256) {
                        const originalHmacSHA256 = CryptoJS.HmacSHA256;
                        CryptoJS.HmacSHA256 = function(message, key) {
                            const result = originalHmacSHA256.apply(this, arguments);
                            console.log('🎯 CRYPTO HOOK: Algorithm: HMAC-SHA256 | Message: ' + (typeof message === 'string' ? message : message?.toString() || 'Object') + ' | Key: ' + (typeof key === 'string' ? key : key?.toString() || 'Object') + ' | Result: ' + result.toString());
                            return result;
                        };
                    }
                    
                    if (CryptoJS.HmacSHA384) {
                        const originalHmacSHA384 = CryptoJS.HmacSHA384;
                        CryptoJS.HmacSHA384 = function(message, key) {
                            const result = originalHmacSHA384.apply(this, arguments);
                            console.log('🎯 CRYPTO HOOK: Algorithm: HMAC-SHA384 | Message: ' + (typeof message === 'string' ? message : message?.toString() || 'Object') + ' | Key: ' + (typeof key === 'string' ? key : key?.toString() || 'Object') + ' | Result: ' + result.toString());
                            return result;
                        };
                    }
                    
                    if (CryptoJS.HmacSHA512) {
                        const originalHmacSHA512 = CryptoJS.HmacSHA512;
                        CryptoJS.HmacSHA512 = function(message, key) {
                            const result = originalHmacSHA512.apply(this, arguments);
                            console.log('🎯 CRYPTO HOOK: Algorithm: HMAC-SHA512 | Message: ' + (typeof message === 'string' ? message : message?.toString() || 'Object') + ' | Key: ' + (typeof key === 'string' ? key : key?.toString() || 'Object') + ' | Result: ' + result.toString());
                            return result;
                        };
                    }
                }
                
                // Hook JSEncrypt (RSA)
                if (typeof JSEncrypt !== 'undefined') {
                    console.log('🎯 CRYPTO HOOK: JSEncrypt (RSA) hook active');
                    
                    // Hook setPublicKey 方法
                    if (JSEncrypt.prototype.setPublicKey) {
                        const originalSetPublicKey = JSEncrypt.prototype.setPublicKey;
                        JSEncrypt.prototype.setPublicKey = function(publicKey) {
                            console.log('🎯 CRYPTO HOOK: RSA PublicKey set: ' + publicKey);
                            return originalSetPublicKey.apply(this, arguments);
                        };
                    }
                    
                    // Hook encrypt 方法
                    if (JSEncrypt.prototype.encrypt) {
                        const originalEncrypt = JSEncrypt.prototype.encrypt;
                        JSEncrypt.prototype.encrypt = function(message) {
                            const result = originalEncrypt.apply(this, arguments);
                            console.log('🎯 CRYPTO HOOK: Algorithm: RSA (JSEncrypt) | Plaintext: ' + message + ' | Result: ' + result);
                            return result;
                        };
                    }
                }
                
                // Hook Forge (RSA and others)
                if (typeof forge !== 'undefined') {
                    console.log('🎯 CRYPTO HOOK: Forge library hook active');
                }
                
                // Hook 国密 SM4 库 - 多种常见实现
                // sm-crypto 库
                if (typeof sm4 !== 'undefined' && typeof sm4.encrypt === 'function') {
                    console.log('🎯 CRYPTO HOOK: SM4 (sm-crypto) hook active');
                    const originalSM4Encrypt = sm4.encrypt;
                    sm4.encrypt = function(plaintext, key, cfg) {
                        let mode = 'ECB';
                        let ivInfo = 'None';
                        let keyInfo = typeof key === 'string' ? 'String: ' + key : String(key);
                        
                        if (cfg) {
                            if (cfg.mode) {
                                mode = cfg.mode.toString().toUpperCase();
                            }
                            if (cfg.iv) {
                                ivInfo = typeof cfg.iv === 'string' ? 'String: ' + cfg.iv : String(cfg.iv);
                            }
                        }
                        
                        const result = originalSM4Encrypt.apply(this, arguments);
                        console.log('🎯 CRYPTO HOOK: Algorithm: SM4 | Mode: ' + mode + ' | Key: ' + keyInfo + ' | IV: ' + ivInfo + ' | Plaintext: ' + plaintext + ' | Result: ' + result);
                        return result;
                    };
                }
                
                // GMSM4 库
                if (typeof GMSM4 !== 'undefined' && typeof GMSM4.encrypt === 'function') {
                    console.log('🎯 CRYPTO HOOK: SM4 (GMSM4) hook active');
                    const originalGMSM4Encrypt = GMSM4.encrypt;
                    GMSM4.encrypt = function(plaintext, key, mode, iv) {
                        let modeInfo = mode || 'ECB';
                        let ivInfo = iv || 'None';
                        let keyInfo = typeof key === 'string' ? 'String: ' + key : String(key);
                        
                        const result = originalGMSM4Encrypt.apply(this, arguments);
                        console.log('🎯 CRYPTO HOOK: Algorithm: SM4 | Mode: ' + modeInfo + ' | Key: ' + keyInfo + ' | IV: ' + ivInfo + ' | Plaintext: ' + plaintext + ' | Result: ' + result);
                        return result;
                    };
                }
                
                // 其他可能的 SM4 实现
                if (typeof window.SM4 !== 'undefined' && typeof window.SM4.encrypt === 'function') {
                    console.log('🎯 CRYPTO HOOK: SM4 (window.SM4) hook active');
                    const originalWindowSM4Encrypt = window.SM4.encrypt;
                    window.SM4.encrypt = function(key, plaintext, mode, iv) {
                        let modeInfo = mode || 'ECB';
                        let ivInfo = iv || 'None';
                        let keyInfo = typeof key === 'string' ? 'String: ' + key : String(key);
                        
                        const result = originalWindowSM4Encrypt.apply(this, arguments);
                        console.log('🎯 CRYPTO HOOK: Algorithm: SM4 | Mode: ' + modeInfo + ' | Key: ' + keyInfo + ' | IV: ' + ivInfo + ' | Plaintext: ' + plaintext + ' | Result: ' + result);
                        return result;
                    };
                }
                
                // SM4 解密支持
                if (typeof sm4 !== 'undefined' && typeof sm4.decrypt === 'function') {
                    console.log('🎯 CRYPTO HOOK: SM4-Decrypt (sm-crypto) hook active');
                    const originalSM4Decrypt = sm4.decrypt;
                    sm4.decrypt = function(ciphertext, key, cfg) {
                        let mode = 'ECB';
                        let ivInfo = 'None';
                        let keyInfo = typeof key === 'string' ? 'String: ' + key : String(key);
                        
                        if (cfg) {
                            if (cfg.mode) {
                                mode = cfg.mode.toString().toUpperCase();
                            }
                            if (cfg.iv) {
                                ivInfo = typeof cfg.iv === 'string' ? 'String: ' + cfg.iv : String(cfg.iv);
                            }
                        }
                        
                        const result = originalSM4Decrypt.apply(this, arguments);
                        console.log('🎯 CRYPTO HOOK: Algorithm: SM4-Decrypt | Mode: ' + mode + ' | Key: ' + keyInfo + ' | IV: ' + ivInfo + ' | Ciphertext: ' + ciphertext + ' | Result: ' + result);
                        return result;
                    };
                }
                
                // GMSM4 解密支持
                if (typeof GMSM4 !== 'undefined' && typeof GMSM4.decrypt === 'function') {
                    console.log('🎯 CRYPTO HOOK: SM4-Decrypt (GMSM4) hook active');
                    const originalGMSM4Decrypt = GMSM4.decrypt;
                    GMSM4.decrypt = function(ciphertext, key, mode, iv) {
                        let modeInfo = mode || 'ECB';
                        let ivInfo = iv || 'None';
                        let keyInfo = typeof key === 'string' ? 'String: ' + key : String(key);
                        
                        const result = originalGMSM4Decrypt.apply(this, arguments);
                        console.log('🎯 CRYPTO HOOK: Algorithm: SM4-Decrypt | Mode: ' + modeInfo + ' | Key: ' + keyInfo + ' | IV: ' + ivInfo + ' | Ciphertext: ' + ciphertext + ' | Result: ' + result);
                        return result;
                    };
                }
                
                // window.SM4 解密支持
                if (typeof window.SM4 !== 'undefined' && typeof window.SM4.decrypt === 'function') {
                    console.log('🎯 CRYPTO HOOK: SM4-Decrypt (window.SM4) hook active');
                    const originalWindowSM4Decrypt = window.SM4.decrypt;
                    window.SM4.decrypt = function(key, ciphertext, mode, iv) {
                        let modeInfo = mode || 'ECB';
                        let ivInfo = iv || 'None';
                        let keyInfo = typeof key === 'string' ? 'String: ' + key : String(key);
                        
                        const result = originalWindowSM4Decrypt.apply(this, arguments);
                        console.log('🎯 CRYPTO HOOK: Algorithm: SM4-Decrypt | Mode: ' + modeInfo + ' | Key: ' + keyInfo + ' | IV: ' + ivInfo + ' | Ciphertext: ' + ciphertext + ' | Result: ' + result);
                        return result;
                    };
                }
                
                // SM2 非对称加密/签名支持
                if (typeof sm2 !== 'undefined') {
                    console.log('🎯 CRYPTO HOOK: SM2 (sm-crypto) hook active');
                    
                    // SM2 加密
                    if (typeof sm2.doEncrypt === 'function') {
                        const originalSM2Encrypt = sm2.doEncrypt;
                        sm2.doEncrypt = function(plaintext, publicKey, cipherMode) {
                            const result = originalSM2Encrypt.apply(this, arguments);
                            console.log('🎯 CRYPTO HOOK: Algorithm: SM2-Encrypt | Plaintext: ' + plaintext + ' | PublicKey: ' + publicKey + ' | CipherMode: ' + cipherMode + ' | Result: ' + result);
                            return result;
                        };
                    }
                    
                    // SM2 解密
                    if (typeof sm2.doDecrypt === 'function') {
                        const originalSM2Decrypt = sm2.doDecrypt;
                        sm2.doDecrypt = function(ciphertext, privateKey, cipherMode) {
                            const result = originalSM2Decrypt.apply(this, arguments);
                            console.log('🎯 CRYPTO HOOK: Algorithm: SM2-Decrypt | Ciphertext: ' + ciphertext + ' | PrivateKey: ' + privateKey + ' | CipherMode: ' + cipherMode + ' | Result: ' + result);
                            return result;
                        };
                    }
                    
                    // SM2 签名
                    if (typeof sm2.doSignature === 'function') {
                        const originalSM2Sign = sm2.doSignature;
                        sm2.doSignature = function(msgHash, privateKey, options) {
                            const result = originalSM2Sign.apply(this, arguments);
                            console.log('🎯 CRYPTO HOOK: Algorithm: SM2-Signature | MsgHash: ' + msgHash + ' | PrivateKey: ' + privateKey + ' | Options: ' + JSON.stringify(options) + ' | Result: ' + result);
                            return result;
                        };
                    }
                    
                    // SM2 验签
                    if (typeof sm2.doVerifySignature === 'function') {
                        const originalSM2Verify = sm2.doVerifySignature;
                        sm2.doVerifySignature = function(msgHash, signValue, publicKey) {
                            const result = originalSM2Verify.apply(this, arguments);
                            console.log('🎯 CRYPTO HOOK: Algorithm: SM2-Verify | MsgHash: ' + msgHash + ' | SignValue: ' + signValue + ' | PublicKey: ' + publicKey + ' | Result: ' + result);
                            return result;
                        };
                    }
                }
                
                // GMSM2 支持
                if (typeof GMSM2 !== 'undefined') {
                    console.log('🎯 CRYPTO HOOK: SM2 (GMSM2) hook active');
                    
                    if (typeof GMSM2.encrypt === 'function') {
                        const originalGMSM2Encrypt = GMSM2.encrypt;
                        GMSM2.encrypt = function(publicKey, plaintext) {
                            const result = originalGMSM2Encrypt.apply(this, arguments);
                            console.log('🎯 CRYPTO HOOK: Algorithm: SM2-Encrypt (GMSM2) | PublicKey: ' + publicKey + ' | Plaintext: ' + plaintext + ' | Result: ' + result);
                            return result;
                        };
                    }
                    
                    if (typeof GMSM2.sign === 'function') {
                        const originalGMSM2Sign = GMSM2.sign;
                        GMSM2.sign = function(privateKey, msg) {
                            const result = originalGMSM2Sign.apply(this, arguments);
                            console.log('🎯 CRYPTO HOOK: Algorithm: SM2-Signature (GMSM2) | PrivateKey: ' + privateKey + ' | Message: ' + msg + ' | Result: ' + result);
                            return result;
                        };
                    }
                }
                
                // SM3 哈希支持
                if (typeof sm3 !== 'undefined' && typeof sm3 === 'function') {
                    console.log('🎯 CRYPTO HOOK: SM3 (sm-crypto) hook active');
                    const originalSM3 = sm3;
                    sm3 = function(message) {
                        const result = originalSM3.apply(this, arguments);
                        console.log('🎯 CRYPTO HOOK: Algorithm: SM3 | Input: ' + message + ' | Result: ' + result);
                        return result;
                    };
                }
                
                // GMSM3 支持
                if (typeof GMSM3 !== 'undefined' && typeof GMSM3.hash === 'function') {
                    console.log('🎯 CRYPTO HOOK: SM3 (GMSM3) hook active');
                    const originalGMSM3Hash = GMSM3.hash;
                    GMSM3.hash = function(message) {
                        const result = originalGMSM3Hash.apply(this, arguments);
                        console.log('🎯 CRYPTO HOOK: Algorithm: SM3 (GMSM3) | Input: ' + message + ' | Result: ' + result);
                        return result;
                    };
                }
                
                // 其他 SM3 实现
                if (typeof window.SM3 !== 'undefined' && typeof window.SM3 === 'function') {
                    console.log('🎯 CRYPTO HOOK: SM3 (window.SM3) hook active');
                    const originalWindowSM3 = window.SM3;
                    window.SM3 = function(message) {
                        const result = originalWindowSM3.apply(this, arguments);
                        console.log('🎯 CRYPTO HOOK: Algorithm: SM3 | Input: ' + message + ' | Result: ' + result);
                        return result;
                    };
                }
                
                // Hook Web Crypto API (fallback)
                if (window.crypto && window.crypto.subtle) {
                    const originalEncrypt = window.crypto.subtle.encrypt;
                    window.crypto.subtle.encrypt = async function(algorithm, key, data) {
                        const result = await originalEncrypt.apply(this, arguments);
                        console.log('🎯 CRYPTO HOOK: Web Crypto Algorithm: ' + algorithm.name + ' | Result length: ' + result.byteLength + ' bytes');
                        return result;
                    };
                    
                    const originalDigest = window.crypto.subtle.digest;
                    window.crypto.subtle.digest = async function(algorithm, data) {
                        const result = await originalDigest.apply(this, arguments);
                        console.log('🎯 CRYPTO HOOK: Web Crypto Hash: ' + algorithm + ' | Result length: ' + result.byteLength + ' bytes');
                        return result;
                    };
                }
            }, 2000);
            """
            
            # 注入Hook脚本到初始页面
            page.add_init_script(crypto_hook_script)
            
            # 监听控制台消息处理加密信息
            def handle_console(msg):
                if '🎯 CRYPTO HOOK:' in msg.text:
                    interceptor.handle_crypto_console_message(msg.text)
            
            # 关键新增：监听所有新页面并注入Hook
            def inject_hook_to_all_pages():
                # 对当前已存在的页面注入
                for p in context.pages:
                    p.add_init_script(crypto_hook_script)
                    p.on("console", handle_console)
                
                # 监听未来新创建的页面
                context.on("page", lambda new_page: (
                    new_page.add_init_script(crypto_hook_script),
                    new_page.on("console", handle_console)
                ))
            
            inject_hook_to_all_pages()

            # 使用 route 来同时捕获请求和响应
            def handle_route(route):
                request = route.request
                # 继续请求
                route.continue_()
                # 等待响应
                try:
                    response = request.response()
                    if response:
                        # 等待响应完成
                        response.finished()
                        # 打印完整数据包（会自动过滤静态资源）
                        interceptor.print_complete_packet(request, response)
                except Exception as e:
                    # 如果无法获取响应，至少打印请求（会自动过滤静态资源）
                    interceptor.print_complete_packet(request, None)
            
            # 拦截所有请求
            context.route("**/*", handle_route)
            
            page.goto(target_url)
            page.wait_for_load_state("networkidle")
            print("页面加载完成！", flush=True)
            
            print("\n浏览器已准备就绪，请在浏览器中进行加密操作...", flush=True)
            print("加解密详情将实时显示...", flush=True)
            print("按 Ctrl+C 停止", flush=True)
            
            # 关键修复：保持脚本运行，等待用户交互
            try:
                while True:
                    # 使用 page.wait_for_timeout 驱动事件循环
                    page.wait_for_timeout(100)
            except KeyboardInterrupt:
                print("\n👋 Stopping packet interception...", flush=True)
                interceptor.save_traffic()
            
        except Exception as e:
            print(f"⚠️  Error during execution: {str(e)}", flush=True)
            import traceback
            traceback.print_exc()
        
        finally:
            browser.close()

if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    
    if len(sys.argv) != 2:
        print("使用方法: python request_interceptor\\ copy.py <目标URL>", flush=True)
        print("示例: python request_interceptor\\ copy.py https://user.elecredit.com/user/login", flush=True)
        sys.exit(1)
    
    target_url = sys.argv[1]
    main(target_url)
