from flask import Flask, render_template_string, jsonify, request
import sqlite3
import chromadb
import os
import json
from src.config.settings.settings import settings

app = Flask(__name__)

# --- HTML Template ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XingChen-V Memory Debugger</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f4f4f9; color: #333; }
        header { background-color: #2c3e50; color: #fff; padding: 1rem; text-align: center; }
        .container { display: flex; height: calc(100vh - 60px); }
        .sidebar { width: 250px; background-color: #34495e; color: #ecf0f1; padding: 1rem; overflow-y: auto; }
        .sidebar h3 { border-bottom: 1px solid #7f8c8d; padding-bottom: 0.5rem; }
        .sidebar ul { list-style: none; padding: 0; }
        .sidebar li { margin-bottom: 0.5rem; cursor: pointer; padding: 0.5rem; border-radius: 4px; transition: background 0.3s; }
        .sidebar li:hover { background-color: #2c3e50; }
        .sidebar li.active { background-color: #1abc9c; }
        .main-content { flex: 1; padding: 2rem; overflow-y: auto; }
        .card { background: #fff; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); padding: 1.5rem; margin-bottom: 2rem; }
        table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; color: #2c3e50; }
        tr:hover { background-color: #f1f1f1; }
        pre { background: #f4f4f9; padding: 10px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; }
        .status-badge { display: inline-block; padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; }
        .status-success { background-color: #d4edda; color: #155724; }
        .status-warning { background-color: #fff3cd; color: #856404; }
        .search-box { margin-bottom: 1rem; display: flex; gap: 10px; }
        input[type="text"] { flex: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        button { padding: 8px 16px; background-color: #1abc9c; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #16a085; }
    </style>
</head>
<body>
    <header>
        <h1>🧠 星辰-V 记忆调试器 (Memory Debugger)</h1>
    </header>
    <div class="container">
        <div class="sidebar">
            <h3>KnowledgeDB (SQL)</h3>
            <ul>
                <li onclick="loadView('knowledge')" class="active">📚 知识表 (Knowledge)</li>
                <li onclick="loadView('entities')">👤 实体表 (Entities)</li>
                <li onclick="loadView('edges')">🕸️ 图谱边 (Edges)</li>
                <li onclick="loadView('nodes')">🔵 图谱节点 (Nodes)</li>
            </ul>
            <h3>ChromaDB (Vector)</h3>
            <ul>
                <li onclick="loadView('chroma_memory')">🧠 长期记忆 (Memory)</li>
                <li onclick="loadView('chroma_skills')">🛠️ 技能库 (Skills)</li>
            </ul>
        </div>
        <div class="main-content" id="content-area">
            <!-- Content will be loaded here -->
            <div class="card">
                <h2>欢迎</h2>
                <p>请从左侧菜单选择要查看的数据表。</p>
            </div>
        </div>
    </div>

    <script>
        let currentView = 'knowledge';

        async function loadView(view) {
            currentView = view;
            document.querySelectorAll('.sidebar li').forEach(li => li.classList.remove('active'));
            event.target.classList.add('active');
            
            const contentArea = document.getElementById('content-area');
            contentArea.innerHTML = '<div class="card"><p>Loading...</p></div>';

            try {
                const response = await fetch(`/api/data/${view}`);
                const data = await response.json();
                renderData(view, data);
            } catch (err) {
                contentArea.innerHTML = `<div class="card"><h3>Error</h3><pre>${err.message}</pre></div>`;
            }
        }

        function renderData(view, data) {
            const contentArea = document.getElementById('content-area');
            if (data.error) {
                contentArea.innerHTML = `<div class="card"><h3>Error</h3><pre>${data.error}</pre></div>`;
                return;
            }

            let html = `<div class="card"><h2>${view} (${data.count} items)</h2>`;
            
            // Search Box (Simple client-side filter for now)
            html += `<div class="search-box"><input type="text" id="searchInput" placeholder="Search..." onkeyup="filterTable()"><button>Refresh</button></div>`;

            if (data.items.length === 0) {
                html += '<p>No data found.</p></div>';
                contentArea.innerHTML = html;
                return;
            }

            html += '<table id="dataTable"><thead><tr>';
            const headers = Object.keys(data.items[0]);
            headers.forEach(h => html += `<th>${h}</th>`);
            html += '</tr></thead><tbody>';

            data.items.forEach(item => {
                html += '<tr>';
                headers.forEach(h => {
                    let val = item[h];
                    if (typeof val === 'object') val = JSON.stringify(val);
                    if (typeof val === 'string' && val.length > 100) val = val.substring(0, 100) + '...';
                    html += `<td>${val}</td>`;
                });
                html += '</tr>';
            });

            html += '</tbody></table></div>';
            contentArea.innerHTML = html;
        }

        function filterTable() {
            const input = document.getElementById("searchInput");
            const filter = input.value.toUpperCase();
            const table = document.getElementById("dataTable");
            const tr = table.getElementsByTagName("tr");

            for (let i = 1; i < tr.length; i++) {
                let visible = false;
                const tds = tr[i].getElementsByTagName("td");
                for (let j = 0; j < tds.length; j++) {
                    if (tds[j]) {
                        const txtValue = tds[j].textContent || tds[j].innerText;
                        if (txtValue.toUpperCase().indexOf(filter) > -1) {
                            visible = true;
                            break;
                        }
                    }
                }
                tr[i].style.display = visible ? "" : "none";
            }
        }
        
        // Initial load
        loadView('knowledge');
    </script>
</body>
</html>
"""

# --- API Routes ---

def get_db_connection():
    db_path = os.path.join(settings.MEMORY_DATA_DIR, "knowledge.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/data/<view>')
def get_data(view):
    try:
        if view in ['knowledge', 'entities', 'edges', 'nodes']:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Limit to 100 for performance
            cursor.execute(f"SELECT * FROM {view} ORDER BY created_at DESC LIMIT 100")
            rows = cursor.fetchall()
            items = [dict(row) for row in rows]
            conn.close()
            return jsonify({"count": len(items), "items": items})
            
        elif view.startswith('chroma_'):
            collection_name = "long_term_memory" if view == 'chroma_memory' else "skill_library"
            
            client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
            try:
                collection = client.get_collection(collection_name)
                # Chroma peek
                results = collection.peek(limit=20)
                
                # Format for table
                items = []
                if results['ids']:
                    for i in range(len(results['ids'])):
                        items.append({
                            "id": results['ids'][i],
                            "document": results['documents'][i],
                            "metadata": results['metadatas'][i]
                        })
                return jsonify({"count": collection.count(), "items": items})
            except Exception as e:
                 return jsonify({"count": 0, "items": [], "error": str(e)})

        else:
            return jsonify({"error": "Unknown view"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Web Debugger on http://localhost:5000")
    app.run(debug=True, port=5000)
