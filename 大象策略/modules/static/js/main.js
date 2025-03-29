// 大象策略 主JavaScript文件
document.addEventListener('DOMContentLoaded', function() {
    console.log('大象策略 Web管理界面已加载');
    
    // 初始化Bootstrap工具提示
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 初始化Bootstrap弹出框
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // 连接WebSocket事件处理
    initializeSocketEvents();
});

// 初始化WebSocket事件处理
function initializeSocketEvents() {
    // 检查SocketIO是否可用
    if (typeof io === 'undefined') {
        console.error('Socket.IO 未加载');
        return;
    }
    
    // 使用socket-config.js中创建的全局socket实例
    var socket = window.socketIO;
    
    if (!socket) {
        console.error('Socket.IO 实例未初始化，请确认socket-config.js已正确加载');
        return;
    }
    
    // 连接事件
    socket.on('connect', function() {
        console.log('已连接到WebSocket服务器');
        showToast('连接成功', '已成功连接到服务器');
    });
    
    // 断开连接事件
    socket.on('disconnect', function() {
        console.log('与WebSocket服务器断开连接');
        showToast('连接断开', '与服务器的连接已断开', 'warning');
    });
    
    // 状态更新事件
    socket.on('status_update', function(data) {
        console.log('收到状态更新:', data);
        updateStatusDisplay(data);
    });
    
    // 日志更新事件
    socket.on('log_update', function(data) {
        console.log('收到日志更新');
        if (data.日志) {
            updateLogsDisplay(data.日志);
        } else if (data.新日志) {
            appendLogEntry(data.新日志);
        }
    });
    
    // 大象数据更新事件
    socket.on('elephants_update', function(data) {
        console.log('收到大象数据更新:', data);
        updateElephantsDisplay(data);
    });
    
    // 交易记录更新事件
    socket.on('trade_update', function(data) {
        console.log('收到交易记录更新');
        if (data.新交易) {
            appendTradeRecord(data.新交易);
        }
    });
    
    socket.on('trades_update', function(data) {
        console.log('收到交易记录批量更新');
        if (data.交易记录) {
            updateTradesDisplay(data.交易记录);
        }
    });
}

// 显示提示消息
function showToast(title, message, type = 'success') {
    // 检查是否有toast容器
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // 创建toast元素
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.className = `toast text-bg-${type}`;
    toast.id = toastId;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">${title}</strong>
            <small>${new Date().toLocaleTimeString()}</small>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // 初始化并显示toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // 显示一段时间后自动删除元素
    setTimeout(() => {
        if (document.getElementById(toastId)) {
            document.getElementById(toastId).remove();
        }
    }, 5000);
}

// 更新状态显示
function updateStatusDisplay(data) {
    // 检查是否在状态页面
    const statusCard = document.getElementById('statusCard');
    if (statusCard) {
        // 更新状态卡片内容
        for (const key in data) {
            const element = document.getElementById(`status-${key}`);
            if (element) {
                if (key.includes('盈亏')) {
                    const value = parseFloat(data[key]);
                    element.textContent = value.toFixed(2);
                    element.className = value >= 0 ? 'text-success' : 'text-danger';
                } else {
                    element.textContent = data[key];
                }
            }
        }
    }
}

// 更新日志显示
function updateLogsDisplay(logs) {
    const logsContainer = document.getElementById('logsContainer');
    if (logsContainer) {
        logsContainer.innerHTML = '';
        logs.forEach(log => {
            appendLogEntry(log, false);
        });
        
        // 滚动到底部
        if (document.getElementById('autoScroll') && document.getElementById('autoScroll').checked) {
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }
    }
}

// 添加单条日志
function appendLogEntry(log, scroll = true) {
    const logsContainer = document.getElementById('logsContainer');
    if (logsContainer) {
        const logElement = document.createElement('div');
        logElement.className = 'log-entry';
        logElement.innerHTML = `<span class="log-time">${log.时间}</span> <span class="log-message">${log.消息}</span>`;
        logsContainer.appendChild(logElement);
        
        // 滚动到底部
        if (scroll && document.getElementById('autoScroll') && document.getElementById('autoScroll').checked) {
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }
    }
}

// 更新大象数据显示
function updateElephantsDisplay(data) {
    // 实现大象数据更新逻辑
}

// 更新交易记录显示
function updateTradesDisplay(trades) {
    const tradesTable = document.getElementById('tradesTable');
    if (tradesTable) {
        const tbody = tradesTable.querySelector('tbody');
        if (tbody) {
            tbody.innerHTML = '';
            trades.forEach(trade => {
                appendTradeRecord(trade, false);
            });
        }
    }
}

// 添加单条交易记录
function appendTradeRecord(trade, prepend = true) {
    const tradesTable = document.getElementById('tradesTable');
    if (tradesTable) {
        const tbody = tradesTable.querySelector('tbody');
        if (tbody) {
            const row = document.createElement('tr');
            
            row.innerHTML = `
                <td>${trade.交易时间}</td>
                <td>${trade.股票代码}</td>
                <td>${trade.股票名称}</td>
                <td>${trade.交易类型}</td>
                <td>${trade.成交价格}</td>
                <td>${trade.成交数量}</td>
                <td class="${parseFloat(trade.盈亏) >= 0 ? 'text-success' : 'text-danger'}">${parseFloat(trade.盈亏).toFixed(2)}</td>
            `;
            
            if (prepend && tbody.firstChild) {
                tbody.insertBefore(row, tbody.firstChild);
            } else {
                tbody.appendChild(row);
            }
        }
    }
} 