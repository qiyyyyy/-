// Socket.IO连接配置
// 提高Socket.IO连接稳定性的配置文件

// 全局Socket.IO实例
let socket;

// 初始化Socket.IO连接
function initSocketIO() {
    console.log('正在初始化Socket.IO连接...');
    
    // 连接选项
    const options = {
        reconnection: true,           // 启用重连
        reconnectionAttempts: 10,     // 最大重连尝试次数
        reconnectionDelay: 1000,      // 初始重连延迟（毫秒）
        reconnectionDelayMax: 5000,   // 最大重连延迟（毫秒）
        timeout: 20000,               // 连接超时时间
        autoConnect: true,            // 自动连接
        transports: ['websocket', 'polling'], // 首选WebSocket，回退到polling
        upgrade: true,                // 允许从polling升级到websocket
        forceNew: false,              // 不强制使用新连接
        path: '/socket.io/'           // Socket.IO路径
    };
    
    try {
        // 创建Socket.IO连接
        socket = io(options);
        
        // 连接事件处理
        socket.on('connect', function() {
            console.log('已连接到WebSocket服务器');
            showConnectionStatus('已连接', 'bg-success');
        });
        
        socket.on('connect_error', function(error) {
            console.error('连接错误:', error);
            showConnectionStatus('连接错误', 'bg-danger');
        });
        
        socket.on('reconnect_attempt', function(attemptNumber) {
            console.log(`尝试重连 (${attemptNumber})`);
            showConnectionStatus('正在重连...', 'bg-warning');
        });
        
        socket.on('reconnect', function(attemptNumber) {
            console.log(`已重连 (${attemptNumber})`);
            showConnectionStatus('已重连', 'bg-success');
        });
        
        socket.on('disconnect', function(reason) {
            console.log('连接断开:', reason);
            showConnectionStatus('已断开', 'bg-secondary');
        });
        
        // 返回创建的socket实例
        return socket;
    } catch (error) {
        console.error('初始化Socket.IO时出错:', error);
        showConnectionStatus('连接失败', 'bg-danger');
        return null;
    }
}

// 显示连接状态
function showConnectionStatus(status, className) {
    const statusIndicator = document.getElementById('socket-status');
    if (statusIndicator) {
        statusIndicator.textContent = status;
        statusIndicator.className = `badge ${className}`;
    }
}

// 文档加载后初始化Socket.IO
document.addEventListener('DOMContentLoaded', function() {
    // 初始化Socket.IO
    socket = initSocketIO();
    
    // 将socket实例添加到全局window对象，供其他脚本使用
    window.socketIO = socket;
    
    // 如果页面上有连接状态指示器，则添加连接状态表示
    if (!document.getElementById('socket-status')) {
        const navbar = document.querySelector('.navbar-text');
        if (navbar) {
            const statusIndicator = document.createElement('span');
            statusIndicator.id = 'socket-status';
            statusIndicator.className = 'badge bg-secondary ms-2';
            statusIndicator.textContent = '未连接';
            navbar.appendChild(statusIndicator);
        }
    }
}); 