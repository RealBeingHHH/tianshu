#!/usr/bin/env python3
"""
inline_data.py — 仪表盘自包含构建工具

解决 MEDIA/file:// 模式下 AJAX fetch 被拦截的问题。
扫描 HTML 中的 fetch('xxx.json') 调用，将 JSON 数据直接内嵌入 <script> 标签。

用法:
    python3 inline_data.py                           # 处理 voyager/ 下所有 HTML
    python3 inline_data.py economy_dashboard.html    # 处理单个文件
    python3 inline_data.py --watch                   # 持续监控，文件变化自动重建

内嵌模式:
    原代码:  const r = await fetch('economy_comparison.json');
    替换为:  const r = { ok:true, json:()=>Promise.resolve(INLINE_JSON) };

    INLINE_JSON 在 HTML 顶部 <script> 中定义，值为对应 JSON 文件的内容。
    如果 HTTP fetch 可用（服务器模式），仍走 HTTP；如果失败，自动回退内嵌数据。
"""

import json, os, re, sys, time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / 'voyager'
if not BASE.exists():
    BASE = Path('/mnt/d/hermes-webui/workspace/voyager')

def find_json_fetches(html_content):
    """找到所有 fetch('xxx.json') 调用，返回 {变量名: json文件名}"""
    pattern = r"""fetch\(['\"]([\w_]+\.json)['\"]"""
    return list(set(re.findall(pattern, html_content)))

def load_json_data(json_file):
    """加载 JSON 并压缩轨迹数据"""
    path = BASE / json_file
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    # 压缩：轨迹只保留首尾两点
    for key in list(data.keys()):
        val = data[key]
        if isinstance(val, dict) and 'trajectory' in val:
            t = val['trajectory']
            if len(t) > 2:
                val['trajectory'] = [t[0], t[-1]]
    return data

def inline_html(html_path):
    """处理单个 HTML 文件，将 JSON fetch 内嵌为 INLINE_JSON 数据块"""
    path = Path(html_path)
    if not path.exists():
        print(f"  ❌ 文件不存在: {html_path}")
        return False
    
    content = path.read_text(encoding='utf-8')
    json_files = find_json_fetches(content)
    
    if not json_files:
        print(f"  ⏭ {path.name} — 无需内嵌（没有 JSON fetch）")
        return False
    
    modified = False
    inline_block = '<script>\n/* ═══ 内嵌数据（MEDIA/离线模式自动回退）═══ */\nvar INLINE_DATA = {\n'
    
    for jf in json_files:
        data = load_json_data(jf)
        if data is None:
            print(f"  ⚠ {jf} 数据缺失，跳过")
            continue
        key = jf.replace('.json', '')
        inline_block += f'  "{key}": {json.dumps(data, ensure_ascii=False)},\n'
        modified = True
    
    inline_block += '};\n'
    inline_block += '''
/* 智能 fetch：HTTP 优先，失败回退内嵌数据 */
async function smartFetch(filename) {
  try {
    var r = await fetch(filename, {cache:'no-store'});
    if (r.ok) return r;
  } catch(e) {}
  // 回退内嵌
  var key = filename.replace('.json','');
  if (INLINE_DATA && INLINE_DATA[key]) {
    return { ok:true, json:function(){return Promise.resolve(INLINE_DATA[key]);} };
  }
  return { ok:false, json:function(){return Promise.resolve({});} };
}
</script>
'''
    
    # 在所有 fetch('xxx.json') 的地方替换为 smartFetch
    for jf in json_files:
        content = content.replace(
            f"fetch('{jf}'",
            f"smartFetch('{jf}')"
        )
        content = content.replace(
            f'fetch("{jf}"',
            f'smartFetch("{jf}")'
        )
    
    # 在 </head> 之前插入内嵌数据块
    content = content.replace('</head>', inline_block + '\n</head>')
    
    # 备份原文件
    backup = path.with_suffix('.html.bak')
    if not backup.exists():
        path.rename(backup)
    
    path.write_text(content, encoding='utf-8')
    print(f"  ✅ {path.name} — 内嵌了 {len(json_files)} 个数据源 ({len(content)} bytes)")
    return True

def process_all():
    """处理 voyager/ 下所有 HTML"""
    html_files = sorted(BASE.glob('*.html'))
    count = 0
    for hf in html_files:
        if inline_html(str(hf)):
            count += 1
    return count

def watch_mode(interval=10):
    """持续监控 HTML 和 JSON 文件变化"""
    print(f"  👀 监控中... (每 {interval}s 检查)")
    last_mtimes = {}
    
    # 初始扫描
    for f in list(BASE.glob('*.html')) + list(BASE.glob('*.json')):
        last_mtimes[str(f)] = f.stat().st_mtime
    
    while True:
        time.sleep(interval)
        for f in list(BASE.glob('*.html')) + list(BASE.glob('*.json')):
            key = str(f)
            if not f.exists():
                continue
            mtime = f.stat().st_mtime
            if key not in last_mtimes or mtime > last_mtimes[key]:
                last_mtimes[key] = mtime
                if f.suffix == '.json':
                    # JSON 变了 → 重建所有引用它的 HTML
                    json_name = f.name
                    for hf in BASE.glob('*.html'):
                        content = hf.read_text(encoding='utf-8')
                        if json_name in content:
                            inline_html(str(hf))
                elif f.suffix == '.html':
                    inline_html(str(f))

def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == '--watch':
            watch_mode()
        elif arg == '--restore':
            for bak in BASE.glob('*.html.bak'):
                orig = bak.with_suffix('')
                bak.rename(orig)
                print(f"  ↩ 恢复: {orig.name}")
        else:
            inline_html(arg)
    else:
        n = process_all()
        print(f"\n  🎯 完成: {n} 个面板已自包含化")
        print(f"  📁 原文件备份为 .html.bak")
        print(f"  🌐 HTTP 模式仍走服务端 · MEDIA/离线自动回退内嵌")

if __name__ == '__main__':
    main()
