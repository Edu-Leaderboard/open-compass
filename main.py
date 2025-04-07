import os
import gradio as gr
import pandas as pd
import json

# 数据根目录
DATA_DIR = "data"

with open(DATA_DIR + os.sep + "link.json", "r") as f:
    links = json.load(f)

CUSTOM_FOOTER = '<div id="custom-footer" style="width:100%; padding:10px; text-align:center; position:fixed; bottom:0; left:0; z-index:999;">'

for key, value in links.items():
    CUSTOM_FOOTER += f'<a href="{value}" target="_blank" style="margin:0 15px; text-decoration:none;">{key}</a>|'

CUSTOM_FOOTER += "</div>"


def get_directory_structure(root_dir):
    """
    遍历根目录，返回结构字典：
    {
       "tab1": {
           "subtab1": ["202502.csv", "202504.csv"],
           "subtab2": [ ... ]
       },
       "tab2": { ... }
    }
    """
    structure = {}
    if not os.path.exists(root_dir):
        return structure
    for tab in os.listdir(root_dir):
        tab_path = os.path.join(root_dir, tab)
        if os.path.isdir(tab_path):
            structure[tab] = {}
            for subtab in os.listdir(tab_path):
                subtab_path = os.path.join(tab_path, subtab)
                if os.path.isdir(subtab_path):
                    csv_files = sorted(
                        [f[:-4] for f in os.listdir(subtab_path) if f.endswith(".csv")]
                    )
                    structure[tab][subtab] = csv_files
    return structure


def load_csv_file(tab, subtab, csv_file):
    """
    根据给定的 tab、subtab 和 csv 文件名构建路径并读取 CSV 文件
    """
    file_path = os.path.join(DATA_DIR, tab, subtab, csv_file)
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            df = pd.DataFrame({"错误": [str(e)]})
    else:
        df = pd.DataFrame({"错误": ["文件不存在"]})
    return df


with gr.Blocks(
    css="""
/* 隐藏 Gradio 默认的 footer */
footer { display: none !important; }
"""
) as demo:
    gr.Markdown("# 大模型竞技场")

    # 每次启动时获取目录结构
    structure = get_directory_structure(DATA_DIR)

    # 外层 tab 代表一级目录
    with gr.Tabs():
        for tab_name, subtabs in structure.items():
            with gr.TabItem(tab_name):
                with gr.Tabs():
                    for subtab_name, csv_list in subtabs.items():
                        with gr.TabItem(subtab_name):
                            # 确定默认 CSV：列表第一个（如果存在）
                            default_csv = csv_list[0] if csv_list else None

                            # 下拉框：选项为当前子目录下的 CSV 文件列表，设置默认值
                            csv_dropdown = gr.Dropdown(
                                choices=csv_list,
                                value=default_csv,
                                label="选择时间",
                            )

                            # 输出区域显示 CSV 文件内容，初始时展示 default_csv
                            output_table = gr.Dataframe(
                                value=(
                                    load_csv_file(
                                        tab_name, subtab_name, default_csv + ".csv"
                                    )
                                    if default_csv
                                    else pd.DataFrame()
                                )
                            )

                            # 绑定加载函数
                            def make_loader(tab, subtab):
                                def load_and_display(csv_file):
                                    return load_csv_file(tab, subtab, csv_file + ".csv")

                                return load_and_display

                            loader_fn = make_loader(tab_name, subtab_name)
                            csv_dropdown.change(
                                fn=loader_fn, inputs=csv_dropdown, outputs=output_table
                            )
    gr.HTML(CUSTOM_FOOTER)  # 添加自定义 footer 到页面底部

# 运行 Gradio App
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7788)
