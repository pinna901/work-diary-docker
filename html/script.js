// script.js
const API_BASE = '/api';

// ========== 主题切换功能 ==========

// 页面加载时检查保存的主题设置
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'cyberpunk') {
        document.body.classList.add('cyberpunk-mode');
    }
});

// 切换主题函数
function toggleTheme() {
    const body = document.body;
    body.classList.toggle('cyberpunk-mode');
    
    // 保存主题设置到 localStorage
    if (body.classList.contains('cyberpunk-mode')) {
        localStorage.setItem('theme', 'cyberpunk');
        console.log('Switched to cyberpunk mode');
    } else {
        localStorage.setItem('theme', 'default');
        console.log('Switched to default mode');
    }
}

window.onload = function() { checkStatus(); loadDiaries(); };

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