// script.js
const API_BASE = '/api';

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
        // 这里会直接弹窗告诉你具体的错误原因
        alert("❌ 打卡流程出错:\n" + e.message);
    }
}

// 增加了详细的错误捕捉 ---

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
