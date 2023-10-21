import json
import tkinter as tk
from tkinter import ttk
from tkinter import Button
from ttkbootstrap import Style
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import datetime 
import webbrowser
from pylab import mpl

# 设置显示中文字体
mpl.rcParams["font.sans-serif"] = ["SimHei"]

# 创建一个函数，用于从爱词霸查询单词的意思
def search_word_online(word):
    search_url = f"https://www.iciba.com/word?w={word}"
    webbrowser.open(search_url)

# 定义单词条目的结构体
class WordEntry:
    def __init__(self, word, meanings, proficiency):
        self.word = word
        self.meanings = meanings
        self.proficiency = proficiency

# 从文件中加载单词条目
def load_word_entries(filename):
    word_entry_dict = {}
    
    with open(filename, 'r', encoding='utf-8') as file:
        next(file)
        next(file)
        for line in file:
            parts = line.strip().split('|')
            word = parts[1].strip()
            meanings = parts[2].strip()
            proficiency = float(parts[3])
            
            if word in word_entry_dict:
                # 如果单词已存在，合并新的翻译，去除重复
                existing_entry = word_entry_dict[word]
                existing_meanings = existing_entry.meanings.split('，')
                new_meanings = meanings.split('，')
                for meaning in new_meanings:
                    if meaning not in existing_meanings:
                        existing_meanings.append(meaning)
                existing_entry.meanings = '，'.join(existing_meanings)
            else:
                # 如果单词不存在，添加新的单词条目
                word_entry_dict[word] = WordEntry(word, meanings, proficiency)
    
    entries = list(word_entry_dict.values())
    entries.sort(key=lambda x: x.word)
    return entries

# 保存单词条目到文件
def save_word_entries(filename, entries):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write("| 单词 | 翻译 | 熟练度 |\n")
        file.write("| :---: | :---: | :---: |\n")
        for entry in entries:
            file.write(f"| {entry.word} | {entry.meanings} | {entry.proficiency:.4f} |\n")

# 初始化训练数据
def init_training_logs():
    # 打开或创建log.json文件
    try:
        with open('log.json', 'r') as log_file:
            training_data = json.load(log_file)
    except FileNotFoundError:
        training_data = {}

    # 获取日期列表并按日期降序排序
    dates = sorted(training_data.keys(), reverse=True)

    # 保留最近的10次数据，删除其余数据
    for date in dates[10:]:
        del training_data[date]

    # 写回log.json文件
    with open('log.json', 'w') as log_file:
        json.dump(training_data, log_file, indent=4)
    
# 加载训练数据
def load_training_logs():
    try:
        with open('log.json', 'r', encoding='utf-8') as log_file:
            training_data = json.load(log_file)
        return training_data
    except FileNotFoundError:
        return {}

# 在主窗口之前加载训练数据
init_training_logs()
training_log = load_training_logs()

# 创建统计信息文件
stats_filename = "training_stats.md"

# 创建折线图
def create_line_chart(dates, total_tests_data, total_words_data, avg_proficiency_data):
    fig = Figure(figsize=(5, 4), dpi=100)  # 创建Figure对象
    ax = fig.add_subplot(111)  # 添加子图

    ax2 = ax.twinx()  # 创建第二个纵轴

    # 调整柱状图的样式
    ax.bar(dates, avg_proficiency_data, color='lightgreen', label='平均熟练度', width=0.7, alpha=0.7)

    # 调整折线图的样式
    ax2.plot(dates, total_tests_data, marker='o', linestyle='-', color='orange', label='总训练次数')
    ax2.plot(dates, total_words_data, marker='o', linestyle='-', color='blue', label='总单词数')

    # 设置标签
    ax.set_xlabel('日期')
    ax.set_ylabel('熟练度', color='black')
    ax2.set_ylabel('次数', color='black')

    return fig

# 更新折线图
def update_training_plot():
    training_log = load_training_logs()
    dates = list(training_log.keys())
    total_tests_data = [training_log[date]["total_tests"] for date in dates]
    total_words_data = [training_log[date]["total_words"] for date in dates]
    avg_proficiency_data = [training_log[date]["avg_proficiency"] for date in dates]

    for widget in right_frame.winfo_children():
        widget.destroy()

    line_chart = create_line_chart(dates, total_tests_data, total_words_data, avg_proficiency_data)
    canvas = FigureCanvasTkAgg(line_chart, right_frame)
    canvas.get_tk_widget().pack()

# 从文件中加载统计信息
def load_training_stats():
    try:
        with open(stats_filename, 'r', encoding='utf-8') as stats_file:
            lines = stats_file.read().splitlines()
            last_line = lines[-1]
            parts = last_line.split('|')
            current_training_start = str(parts[1].strip())
            total_tests = int(parts[3].strip())
            total_words = int(parts[4].strip())
            avg_proficiency = float(parts[5].strip())
            return current_training_start, total_tests, total_words, avg_proficiency
    except FileNotFoundError:
        return datetime.datetime.now(), 0, 0.0

# 更新统计信息标签
def update_stats_label():
    global user_translation_waiting, total_tests, avg_proficiency
    total_words = len(word_entries)
    total_proficiency = sum(word.proficiency for word in word_entries)
    avg_proficiency = (total_proficiency / total_words if total_words > 0 else 0) * 100
    stats_label.config(text=f"训练次数: {total_tests}  平均熟练度: {avg_proficiency:.2f}%")

# 从翻译中分词匹配
def check_translation(user_translation, current_word):
    parts = current_word.meanings.strip().split('，')  # 将含义分割成部分
    for check in parts:
        if user_translation == check:
            return True  # 如果找到匹配的部分，返回True
    return False  # 如果没有找到匹配的部分，返回False

def write_training_stats():
    global user_translation_waiting, total_tests, avg_proficiency
    total_words = len(word_entries)
    total_proficiency = sum(word.proficiency for word in word_entries)
    avg_proficiency = (total_proficiency / total_words if total_words > 0 else 0) * 100
    with open(stats_filename, 'w', encoding='utf-8') as stats_file:
        stats_file.write("| 开始训练时间 | 最后训练时间 | 总训练次数 | 总单词数 | 平均熟练度 |\n")
        stats_file.write("| :---: | :---: | :---: | :---: | :---: |\n")
        stats_file.write(f"| {current_training_start} | {datetime.datetime.now()} | {total_tests} | {total_words} | {avg_proficiency:.2f} |\n")
    
    # 获取今天的日期
    today = datetime.datetime.now().strftime('%m-%d')

    # 创建一个新的统计记录
    new_stats = {
        "total_tests": total_tests,
        "total_words": len(word_entries),
        "avg_proficiency": avg_proficiency
    }

    try:
        # 从log.json中读取之前的数据
        with open('log.json', 'r') as log_file:
            log_data = json.load(log_file)
    except FileNotFoundError:
        # 如果文件不存在，创建一个空的log_data字典
        log_data = {}

    # 更新或添加今天的记录
    log_data[today] = new_stats

    # 写回log.json文件
    with open('log.json', 'w') as log_file:
        json.dump(log_data, log_file, indent=4)

def check_result():
    global current_state
    global user_translation_waiting, total_tests, avg_proficiency
    user_translation = entry.get()
    user_translation_waiting = entry.get()
    entry.delete(0, tk.END) 
    if not user_translation:
        result_label.config(text=f"请输入翻译！")
    else:
        if check_translation(user_translation, current_word):
            current_word.proficiency = min(1.0, current_word.proficiency * (2.0 - current_word.proficiency))
            result_label.config(text=f"✔️翻译正确，熟练度提升至 {current_word.proficiency*100:.2f}%")
            save_word_entries("word_list.md", word_entries)
            current_state = True
        else:
            result_label.config(text=f"✖️翻译错误。正确的翻译是：{current_word.meanings}")
            add_button.config(state=tk.NORMAL)
            decrease_button.config(state=tk.NORMAL)
            current_state = False
    total_tests += 1
    avg_proficiency = (sum(word.proficiency for word in word_entries) / total_tests) * 100
    update_stats_label()
    write_training_stats()

def save_translation():
    global user_translation_waiting, total_tests, avg_proficiency
    current_word.meanings += f"，{user_translation_waiting}"
    save_word_entries("word_list.md", word_entries)
    result_label.config(text="已保存新的翻译。")
    add_button.config(state=tk.DISABLED)
    decrease_button.config(state=tk.DISABLED)
    total_tests += 1
    avg_proficiency = sum(word.proficiency for word in word_entries) / total_tests
    update_stats_label()
    write_training_stats()

def decrease_proficiency():
    global current_state, total_tests, avg_proficiency
    current_state = True
    current_word.proficiency = max(0.0, current_word.proficiency * (1.0 - current_word.proficiency))
    if current_word.proficiency == 1:
        current_word.proficiency = 0.5000
    save_word_entries("word_list.md", word_entries)
    result_label.config(text=f"熟练度降低至 {current_word.proficiency*100:.2f}%")
    add_button.config(state=tk.DISABLED)
    decrease_button.config(state=tk.DISABLED)
    total_tests += 1
    avg_proficiency = sum(word.proficiency for word in word_entries) / total_tests
    update_stats_label()
    write_training_stats()

def show_next_word():
    global current_word
    global current_state
    current_state = True
    if word_entries:
        weights = [1 / word.proficiency for word in word_entries]
        total_weight = sum(weights)
        probabilities = [weight / total_weight for weight in weights]
        current_word = random.choices(word_entries, probabilities)[0]

        word_label.config(text=current_word.word)
        entry.delete(0, tk.END)
        result_label.config(text="")
        add_button.config(state=tk.DISABLED)
        decrease_button.config(state=tk.DISABLED)
    else:
        word_label.config(text="没有更多单词了")
    write_training_stats();
    # update_training_plot()

def on_enter_key(event):
    global current_state
    user_translation = entry.get()
    if current_state:
        if not user_translation:
            show_next_word()
        else:
            check_result()
    else:
        decrease_proficiency()

# 初始化单词列表
current_training_start, total_tests, total_words, avg_proficiency = load_training_stats()
word_entries = load_word_entries("word_list.md")
user_translation_waiting = None
current_word = None

# 更新单词列表
save_word_entries("word_list.md", word_entries)

# 创建主窗口
root = tk.Tk()
root.title("单词测试")

# 初始化 ttkbootstrap 样式
style = Style(theme="litera")

# 创建框架以容纳内容
main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

# 创建左侧菜单框架
menu_frame = ttk.Frame(main_frame)
menu_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)

# 创建右侧内容框架
content_frame = ttk.Frame(main_frame)
content_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

# 创建右侧空间以容纳折线图
right_frame = ttk.Frame(main_frame)
right_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)

# 添加用于显示统计信息的标签
stats_label = ttk.Label(content_frame, text="", font=("微软雅黑", 12))
stats_label.pack(pady=10)

# 更新统计信息标签初始状态
update_stats_label()

# 创建一个 ttk.Style 对象
style = ttk.Style()

# 配置按钮字体
style.configure("TButton", font=("微软雅黑", 14))

# 创建跳过按钮
skip_button = ttk.Button(menu_frame, text="跳过当前", command=show_next_word)
skip_button.pack(pady=10)
skip_button.configure(style="TButton")

# 创建检查按钮
check_button = ttk.Button(menu_frame, text="检查翻译", command=check_result)
check_button.pack(pady=10)
check_button.configure(style="TButton")

# 创建添加按钮
add_button = ttk.Button(menu_frame, text="添加单词", state="disabled", command=save_translation)
add_button.pack(pady=10)
add_button.configure(style="TButton")

# 创建承认错误按钮
decrease_button = ttk.Button(menu_frame, text="承认错误", state="disabled", command=decrease_proficiency)
decrease_button.pack(pady=10)
decrease_button.configure(style="TButton")

# 创建一个按钮，用于触发在线查询
search_button = ttk.Button(menu_frame, text="查询单词", command=lambda: search_word_online(current_word.word))
search_button.pack(pady=10)
search_button.configure(style="TButton")

# 创建一个按钮，用于更新图表
search_button = ttk.Button(menu_frame, text="更新图表", command=update_training_plot)
search_button.pack(pady=10)
search_button.configure(style="TButton")

# 创建单词标签
word_label = ttk.Label(content_frame, text="", font=("微软雅黑", 24))
word_label.pack(pady=20)

# 创建文本输入框
entry = ttk.Entry(content_frame, font=("微软雅黑", 18), width=20)
entry.pack(pady=20)

# 创建结果标签
result_label = ttk.Label(content_frame, text="", font=("微软雅黑", 16), wraplength=300)  # 设置 wraplength 的值
result_label.pack()

# 显示第一个单词
show_next_word()
update_training_plot()
entry.focus()
entry.bind("<Return>", on_enter_key)

root.mainloop()
