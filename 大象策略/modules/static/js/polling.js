// 轮询机制实现
// 替代WebSocket的数据更新方式

// 全局变量
let pollingEnabled = true;
let pollingIntervals = {};

// 初始化轮询
function initPolling() {
    console.log('正在初始化轮询机制...');
    
    // 创建轮询状态指示器
    createPollingStatusIndicator();
    
    // 根据当前页面设置不同的轮询
    setupPageSpecificPolling();
    
    // 全局状态轮询（所有页面都需要）
    startPolling('status', '/api/status', updateStatusDisplay, 3000);
}

// 创建轮询状态指示器
function createPollingStatusIndicator() {
    if (!document.getElementById('polling-status')) {
        const navbar = document.querySelector('.navbar-text');
        if (navbar) {
            const statusIndicator = document.createElement('span');
            statusIndicator.id = 'polling-status';
            statusIndicator.className = 'badge bg-success ms-2';
            statusIndicator.textContent = '已连接';
            navbar.appendChild(statusIndicator);
        }
    }
}

// 根据页面设置特定轮询
function setupPageSpecificPolling() {
    // 检查当前页面
    const currentPath = window.location.pathname;
    
    // 主页/控制面板
    if (currentPath === '/' || currentPath === '/index') {
        // 大象数据轮询
        startPolling('elephants', '/api/elephants', updateElephantsDisplay, 5000);
        // 最近交易轮询
        startPolling('recent_trades', '/api/trades?date=today&limit=10', updateRecentTradesDisplay, 5000);
    }
    
    // 日志页面
    else if (currentPath === '/logs') {
        startPolling('logs', '/api/logs', updateLogsDisplay, 3000);
    }
    
    // 交易记录页面
    else if (currentPath === '/trades') {
        // 交易记录在页面上通过筛选按钮手动刷新
        // 但状态数据需要自动更新
    }
    
    // 统计页面
    else if (currentPath === '/stats') {
        startPolling('assets', '/api/assets', updateAssetsDisplay, 10000);
    }
}

// 开始轮询
function startPolling(name, url, callback, interval) {
    if (pollingIntervals[name]) {
        clearInterval(pollingIntervals[name]);
    }
    
    // 立即执行一次
    fetchData(url, callback);
    
    // 设置定时器
    pollingIntervals[name] = setInterval(() => {
        if (pollingEnabled) {
            fetchData(url, callback);
        }
    }, interval);
    
    console.log(`已启动 ${name} 轮询，间隔: ${interval}ms`);
}

// 停止轮询
function stopPolling(name) {
    if (pollingIntervals[name]) {
        clearInterval(pollingIntervals[name]);
        delete pollingIntervals[name];
        console.log(`已停止 ${name} 轮询`);
    }
}

// 停止所有轮询
function stopAllPolling() {
    Object.keys(pollingIntervals).forEach(name => {
        clearInterval(pollingIntervals[name]);
        delete pollingIntervals[name];
    });
    pollingEnabled = false;
    console.log('已停止所有轮询');
    
    // 更新状态指示器
    const statusIndicator = document.getElementById('polling-status');
    if (statusIndicator) {
        statusIndicator.textContent = '已断开';
        statusIndicator.className = 'badge bg-secondary ms-2';
    }
}

// 恢复所有轮询
function resumeAllPolling() {
    pollingEnabled = true;
    setupPageSpecificPolling();
    console.log('已恢复所有轮询');
    
    // 更新状态指示器
    const statusIndicator = document.getElementById('polling-status');
    if (statusIndicator) {
        statusIndicator.textContent = '已连接';
        statusIndicator.className = 'badge bg-success ms-2';
    }
}

// 获取数据
function fetchData(url, callback) {
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            callback(data);
        })
        .catch(error => {
            console.error('获取数据出错:', error);
            // 显示错误提示
            showToast('连接错误', '无法从服务器获取数据', 'danger');
        });
}

// 发送控制命令
function sendControlCommand(action, callback) {
    const formData = new FormData();
    formData.append('action', action);
    
    fetch('/api/control', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (callback) callback(data);
            showToast(data.success ? '操作成功' : '操作失败', data.message);
        })
        .catch(error => {
            console.error('发送控制命令出错:', error);
            showToast('操作失败', '无法发送控制命令', 'danger');
        });
}

// 文档加载后初始化轮询
document.addEventListener('DOMContentLoaded', function() {
    // 初始化轮询
    initPolling();
});