import urwid
import random
import time
from collections import OrderedDict

# ======================
# 游戏数据模型
# ======================
class CultivationGame:
    def __init__(self):
        self.year = 0
        self.resources = {
            '灵石': 1000,
            '药材': 200,
            '矿石': 300,
            '灵田': 5
        }
        self.disciples = []
        self.buildings = {
            '练功房': 1,
            '炼丹房': 0,
            '炼器室': 0
        }
        self.events = []
        self.selected_disciple = None

    def add_disciple(self, name, talent):
        """添加新弟子"""
        self.disciples.append({
            'name': name,
            'talent': talent,  # 资质 (1-5)
            'cultivation': 0,  # 修为
            'stage': '凡人',   # 境界
            'task': '修炼'     # 当前任务
        })
        self.log_event(f"{name}加入门派！")

    def build_facility(self, name):
        """建造设施"""
        cost = {'练功房': 200, '炼丹房': 300, '炼器室': 400}[name]
        if self.resources['灵石'] >= cost:
            self.resources['灵石'] -= cost
            self.buildings[name] += 1
            self.log_event(f"建造了{name}！")
            return True
        return False

    def cultivate(self):
        """修炼推进"""
        # 资源产出
        self.resources['灵石'] += self.buildings['练功房'] * 50
        self.resources['药材'] += self.resources['灵田'] * 10
        
        # 弟子修炼
        for d in self.disciples:
            if d['task'] == '修炼':
                d['cultivation'] += d['talent'] * self.buildings['练功房']
                # 境界突破判定
                if d['cultivation'] > 100 and d['stage'] == '凡人':
                    if random.random() > 0.7:
                        d['stage'] = '炼气期'
                        self.log_event(f"{d['name']}突破到炼气期！")
        
        self.year += 1
        # 随机事件
        if random.random() > 0.8:
            self.random_event()

    def random_event(self):
        """随机事件系统"""
        events = [
            ("发现灵矿", "灵石+500", lambda: self.resources.update({'灵石': self.resources['灵石']+500})),
            ("外敌入侵", "损失200灵石", lambda: self.resources.update({'灵石': max(0, self.resources['灵石']-200)})),
            ("天才弟子", "新弟子加入", lambda: self.add_disciple(random.choice(["林风", "云瑶", "玄夜"]), random.randint(3,5)))
        ]
        event = random.choice(events)
        self.log_event(f"事件：{event} - {event}")
        event()

    def log_event(self, msg):
        """记录事件"""
        self.events.insert(0, f"[{self.year}年] {msg}")
        if len(self.events) > 10:
            self.events.pop()

# ======================
# UI组件
# ======================
class GameUI:
    PALETTE = [
        ('header', 'white,bold', 'dark blue'),
        ('footer', 'light gray', 'black'),
        ('button', 'yellow', 'dark blue'),
        ('button_focus', 'black', 'light green'),
        ('progress', 'white', 'dark green'),
        ('warning', 'white,bold', 'dark red')
    ]

    def __init__(self, game):
        self.game = game
        self.main_loop = None
        self.setup_ui()

    def setup_ui(self):
        # 顶部状态栏
        header_text = urwid.Text(
            ("header", f" 修仙门派模拟器 | 年份: {self.game.year} | "
                      f"灵石: {self.game.resources['灵石']} 药材: {self.game.resources['药材']}  "
                      f"灵田: {self.game.resources['灵田']}"), 
            align='center'
        )
        
        # 中央内容区
        self.body_pile = urwid.Pile([])
        self.update_body()
        
        # 底部菜单
        menu_items = [
            urwid.Button("招收弟子", self.recruit_disciple),
            urwid.Button("建造设施", self.build_facility),
            urwid.Button("弟子管理", self.manage_disciples),
            urwid.Button("结束年份", self.end_year)
        ]
        menu = urwid.GridFlow(
            [urwid.AttrMap(btn, 'button', 'button_focus') for btn in menu_items],
            cell_width=15, h_sep=2, v_sep=1, align='center'
        )
        
        # 事件日志
        self.event_log = urwid.ListBox(urwid.SimpleListWalker([]))
        
        # 整体布局
        frame = urwid.Frame(
            body=urwid.Pile([
                ('weight', 2, urwid.LineBox(self.body_pile, title="门派状态")),
                ('weight', 1, urwid.LineBox(self.event_log, title="事件日志"))
            ]),
            header=header_text,
            footer=urwid.AttrMap(menu, 'footer')
        )
        
        self.layout = frame

    def update_body(self):
        """更新主体内容"""
        content = []
        
        # 建筑状态
        buildings = "\n".join([f"{name}: Lv.{lv}" for name, lv in self.game.buildings.items()])
        content.append(urwid.Text(("progress", f"门派建筑:\n{buildings}")))
        
        # 弟子列表
        if self.game.disciples:
            disciples = "\n".join([
                f"{d['name']} ({d['stage']}) - 修为: {d['cultivation']}"
                for d in self.game.disciples
            ])
            content.append(urwid.Text(f"\n门派弟子:\n{disciples}"))
        else:
            content.append(urwid.Text(("warning", "\n尚无弟子！请尽快招收")))
        
        self.body_pile.contents = [(item, ('pack', None)) for item in content]

    def update_events(self):
        """更新事件日志"""
        self.event_log.body[:] = [
            urwid.Text(event) for event in self.game.events
        ]

    def refresh_ui(self):
        """刷新所有UI元素"""
        self.update_body()
        self.update_events()
        self.layout.header.set_text(
            ("header", f" 修仙门派模拟器 | 年份: {self.game.year} | "
                      f"灵石: {self.game.resources['灵石']} 药材: {self.game.resources['药材']}  "
                      f"灵田: {self.game.resources['灵田']}")
        )

    # ======================
    # 游戏操作处理
    # ======================
    def recruit_disciple(self, button):
        """招收弟子弹窗"""
        names = ["云天河", "韩立", "叶凡", "萧炎", "石昊"]
        name = random.choice(names)
        talent = random.randint(1, 5)
        
        def recruit(btn):
            self.game.add_disciple(name, talent)
            self.refresh_ui()
            self.main_loop.widget = self.layout
        
        text = urwid.Text(f"发现弟子: {name}\n资质: {'★'*talent}\n是否招收？")
        yes_btn = urwid.Button("招收", recruit)
        no_btn = urwid.Button("放弃", lambda btn: setattr(self.main_loop, 'widget', self.layout))
        
        grid = urwid.GridFlow([urwid.AttrMap(yes_btn, 'button', 'button_focus'),
                              urwid.AttrMap(no_btn, 'button', 'button_focus')],
                             cell_width=10, h_sep=2, align='center')
        
        popup = urwid.LineBox(urwid.Pile([
            text,
            urwid.Divider(),
            grid
        ]), title="招收弟子")
        
        overlay = urwid.Overlay(
            popup, self.layout,
            align='center', width=('relative', 50),
            valign='middle', height=('relative', 40)
        )
        self.main_loop.widget = overlay

    def build_facility(self, button):
        """建造设施弹窗"""
        choices = OrderedDict({
            '练功房': "提升修炼效率\n消耗200灵石",
            '炼丹房': "解锁炼丹功能\n消耗300灵石",
            '炼器室': "解锁炼器功能\n消耗400灵石"
        })
        
        buttons = []
        for name, desc in choices.items():
            def make_callback(bname):
                def callback(btn):
                    if self.game.build_facility(bname):
                        self.refresh_ui()
                    self.main_loop.widget = self.layout
                return callback
                
            btn = urwid.Button(f"{name}: {desc}", make_callback(name))
            buttons.append(urwid.AttrMap(btn, 'button', 'button_focus'))
        
        cancel_btn = urwid.Button("取消", lambda btn: setattr(self.main_loop, 'widget', self.layout))
        buttons.append(urwid.AttrMap(cancel_btn, 'button', 'button_focus'))
        
        popup = urwid.LineBox(urwid.ListBox(buttons), title="建造设施")
        
        overlay = urwid.Overlay(
            popup, self.layout,
            align='center', width=('relative', 70),
            valign='middle', height=('relative', 60)
        )
        self.main_loop.widget = overlay

    def manage_disciples(self, button):
        """弟子管理界面"""
        if not self.game.disciples:
            self.game.log_event("尚无弟子可管理！")
            self.refresh_ui()
            return
        
        disciple_list = []
        for d in self.game.disciples:
            btn = urwid.Button(
                f"{d['name']} ({d['stage']}) - 修为: {d['cultivation']}",
                lambda btn, disc=d: self.show_disciple_detail(disc)
            )
            disciple_list.append(urwid.AttrMap(btn, 'button', 'button_focus'))
        
        back_btn = urwid.Button("返回", lambda btn: setattr(self.main_loop, 'widget', self.layout))
        disciple_list.append(urwid.AttrMap(back_btn, 'button', 'button_focus'))
        
        popup = urwid.LineBox(urwid.ListBox(disciple_list), title="弟子管理")
        
        overlay = urwid.Overlay(
            popup, self.layout,
            align='center', width=('relative', 80),
            valign='middle', height=('relative', 70)
        )
        self.main_loop.widget = overlay

    def show_disciple_detail(self, disciple):
        """弟子详情界面"""
        tasks = ["修炼", "炼丹", "炼器", "种植"]
        
        def set_task(task):
            disciple['task'] = task
            self.game.log_event(f"{disciple['name']}开始{task}")
            self.main_loop.widget = self.layout
            self.refresh_ui()
        
        task_btns = []
        for task in tasks:
            btn = urwid.Button(task, lambda btn, t=task: set_task(t))
            task_btns.append(urwid.AttrMap(btn, 'button', 'button_focus'))
        
        back_btn = urwid.Button("返回", lambda btn: self.manage_disciples(None))
        task_btns.append(urwid.AttrMap(back_btn, 'button', 'button_focus'))
        
        content = [
            urwid.Text(f"弟子: {disciple['name']}"),
            urwid.Text(f"境界: {disciple['stage']}"),
            urwid.Text(f"修为: {disciple['cultivation']}"),
            urwid.Text(f"当前任务: {disciple['task']}"),
            urwid.Divider(),
            urwid.Text("分配任务:"),
            urwid.GridFlow(task_btns, cell_width=10, h_sep=2, v_sep=1, align='center')
        ]
        
        popup = urwid.LineBox(urwid.Pile(content), title="弟子详情")
        
        overlay = urwid.Overlay(
            popup, self.layout,
            align='center', width=('relative', 60),
            valign='middle', height=('relative', 50)
        )
        self.main_loop.widget = overlay

    def end_year(self, button):
        """结束当前年份"""
        self.game.cultivate()
        self.refresh_ui()

    def run(self):
        self.main_loop = urwid.MainLoop(
            self.layout,
            palette=self.PALETTE,
            unhandled_input=self.handle_global_input
        )
        self.main_loop.run()

    def handle_global_input(self, key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()

# ======================
# 游戏启动
# ======================
if __name__ == '__main__':
    game = CultivationGame()
    # 初始添加两名弟子
    game.add_disciple("张凡", 3)
    game.add_disciple("李逍遥", 4)
    
    ui = GameUI(game)
    ui.run()
