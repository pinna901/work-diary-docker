// script.js

// ========== Theme Toggle Feature ==========

// Check and apply saved theme on page load
function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'night') {
        document.body.classList.add('night-mode');
    }
}

// Toggle theme function
function toggleTheme() {
    const body = document.body;
    body.classList.toggle('night-mode');
    
    // Save theme selection to localStorage
    if (body.classList.contains('night-mode')) {
        localStorage.setItem('theme', 'night');
    } else {
        localStorage.setItem('theme', 'day');
    }
}

// Initialize theme on page load
initTheme();

const API_BASE = '/api';

window.onload = function() { 
    checkStatus(); 
    loadDiaries(); 
};

async function checkStatus() {
    try {
        const res = await fetch(`${API_BASE}/status`);
        const data = await res.json();
        document.getElementById('day-count').innerText = data.count;
        document.getElementById('status-msg').innerText = `数据库模式: ${data.db || '未知'}`;
    } catch (e) {
        document.getElementById('status-msg').innerText = "获取状态失败: " + e.message;
    }
}

async function clockIn() {
    try {
        console.log("开始请求打卡...");
        const res = await fetch(`${API_BASE}/clock-in`, { method: 'POST' });

        console.log("服务器状态码:", res.status);

        // 先以文本形式读取，防止 JSON 解析挂了不知道原因
        const text = await res.text();
        console.log("服务器返回原始内容:", text);

        if (!res.ok) {
            throw new Error(`服务器报错: ${res.status} - ${text}`);
        }

        // 尝试解析 JSON
        let data;
        try {
            data = JSON.parse(text);
        } catch (jsonError) {
            throw new Error("返回的不是有效 JSON！内容是：" + text);
        }

        alert("成功: " + data.message);

        // 成功后刷新数字
        checkStatus();
        
        // 如果打卡历史区域已打开，自动刷新历史记录
        const historySection = document.getElementById('clock-in-history-section');
        if (historySection && historySection.style.display !== 'none') {
            loadClockInHistory();
        }

    } catch (e) {
        console.error("JS 报错:", e);
        alert("❌ 打卡流程出错:\n" + e.message);
    }
}

// 错误捕捉 ---

async function addDiary() {
        const content = document.getElementById('diary-input').value;
        if(!content) return;
        try {
            const res = await fetch(`${API_BASE}/diary`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: content })
            });
            const data = await res.json();
            alert(`保存成功！\n${data.entry.quote}`);
            document.getElementById('diary-input').value = '';
            loadDiaries();
        } catch (e) {
            alert("日记保存失败: " + e.message);
        }
    }

async function loadDiaries() {
        const res = await fetch(`${API_BASE}/diary`);
        const data = await res.json();
        const listDiv = document.getElementById('diary-list');
        listDiv.innerHTML = '';
        data.diaries.forEach(d => {
            const item = document.createElement('div');
            item.className = 'diary-item';
            item.innerHTML = `<div>${d.content}</div><div class="diary-quote">${d.quote || ''}</div>`;
            listDiv.appendChild(item);
        });
    }

// 新增：调用 AI 生成日记内容
async function askAI() {
    const input = document.getElementById('diary-input');
    const content = input.value;
    const btn = document.querySelector('button[onclick="askAI()"]');

    if (!content) {
        alert("请先输入一些关键词，比如：'修复登录bug，很累'");
        return;
    }

    // 按钮变态（防止重复点击）
    const originalText = btn.innerText;
    btn.innerText = "🔮 施法中...";
    btn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/ai-polish`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: content })
        });

        const data = await res.json();

        if (res.ok) {
            // 把 AI 写好的话填回输入框
            input.value = data.result;
        } else {
            alert("AI 罢工了: " + data.error);
        }
    } catch (e) {
        alert("网络请求失败: " + e.message);
    } finally {
        // 恢复按钮
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

// ========== Clock-in History Feature ==========

let currentHistoryPage = 1;

// 切换打卡历史显示/隐藏
function toggleClockInHistory() {
    const historySection = document.getElementById('clock-in-history-section');
    if (historySection.style.display === 'none') {
        historySection.style.display = 'block';
        loadClockInHistory(1);
    } else {
        historySection.style.display = 'none';
    }
}

// 加载打卡历史
async function loadClockInHistory(page = 1) {
    currentHistoryPage = page;
    const perPage = 20;
    
    try {
        const res = await fetch(`${API_BASE}/clock-in/history?page=${page}&per_page=${perPage}`);
        const data = await res.json();
        
        if (!res.ok) {
            throw new Error(data.error || '加载打卡历史失败');
        }
        
        renderClockInHistory(data);
        renderClockInPagination(data);
        
    } catch (e) {
        const listDiv = document.getElementById('clock-in-history-list');
        listDiv.innerHTML = `<p style="color: red;">加载失败: ${e.message}</p>`;
    }
}

// 渲染打卡历史列表
function renderClockInHistory(data) {
    const listDiv = document.getElementById('clock-in-history-list');
    listDiv.innerHTML = '';
    
    if (data.records.length === 0) {
        listDiv.innerHTML = '<p style="color: gray;">暂无打卡记录</p>';
        return;
    }
    
    // 按日期分组
    const groupedByDate = {};
    data.records.forEach(record => {
        const date = record.clock_in_time.split(' ')[0];
        if (!groupedByDate[date]) {
            groupedByDate[date] = [];
        }
        groupedByDate[date].push(record);
    });
    
    // 渲染每个日期组
    Object.keys(groupedByDate).forEach(date => {
        const dateGroup = document.createElement('div');
        dateGroup.className = 'clock-in-date-group';
        
        const dateHeader = document.createElement('div');
        dateHeader.className = 'clock-in-date-header';
        dateHeader.innerHTML = `📅 ${date} (${groupedByDate[date].length} 次)`;
        dateGroup.appendChild(dateHeader);
        
        groupedByDate[date].forEach(record => {
            const item = document.createElement('div');
            item.className = 'clock-in-item';
            const time = record.clock_in_time.split(' ')[1];
            item.innerHTML = `⏰ ${time}`;
            dateGroup.appendChild(item);
        });
        
        listDiv.appendChild(dateGroup);
    });
}

// 渲染分页控件
function renderClockInPagination(data) {
    const paginationDiv = document.getElementById('clock-in-pagination');
    paginationDiv.innerHTML = '';
    
    if (data.total_pages <= 1) {
        return;
    }
    
    const info = document.createElement('div');
    info.style.marginBottom = '10px';
    info.style.fontSize = '14px';
    info.innerHTML = `共 ${data.total} 条记录，第 ${data.page}/${data.total_pages} 页`;
    paginationDiv.appendChild(info);
    
    const btnContainer = document.createElement('div');
    btnContainer.style.display = 'flex';
    btnContainer.style.justifyContent = 'center';
    btnContainer.style.gap = '10px';
    
    // 上一页按钮
    if (data.page > 1) {
        const prevBtn = document.createElement('button');
        prevBtn.innerText = '← 上一页';
        prevBtn.onclick = () => loadClockInHistory(data.page - 1);
        btnContainer.appendChild(prevBtn);
    }
    
    // 下一页按钮
    if (data.page < data.total_pages) {
        const nextBtn = document.createElement('button');
        nextBtn.innerText = '下一页 →';
        nextBtn.onclick = () => loadClockInHistory(data.page + 1);
        btnContainer.appendChild(nextBtn);
    }
    
    paginationDiv.appendChild(btnContainer);
}