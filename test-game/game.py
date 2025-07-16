#!/usr/bin/env python3
import urwid
import random
import time
from collections import namedtuple

# ======================
# 基础数据结构定义
# ======================
Position = namedtuple('Position', ['x', 'y'])
Terrain = namedtuple('Terrain', ['name', 'symbol', 'passable', 'color'])

# 地形类型定义
TERRAIN_TYPES = {
    'grass': Terrain('草地', '░', True, 'light green'),
    'hills': Terrain('丘陵', '▲', True, 'brown'),
    'forest': Terrain('森林', '♣', True, 'dark green'),
    'water': Terrain('水域', '≈', False, 'light blue'),
    'mountain': Terrain('山脉', '▲', False, 'dark gray'),
    'desert': Terrain('沙漠', '▒', True, 'yellow')
}

# ======================
# 游戏实体类定义
# ======================
class Tile:
    """地图格子类"""
    def __init__(self, terrain_type):
        self.terrain = TERRAIN_TYPES[terrain_type]
        self.entities = []  # 存储当前格子上的实体（角色、城市等）

class Character:
    """角色基类"""
    def __init__(self, name, symbol, color, x, y):
        self.name = name
        self.symbol = symbol
        self.color = color
        self.x = x
        self.y = y
        self.hp = 100
    
    def move(self, dx, dy, game_world):
        """移动角色"""
        new_x, new_y = self.x + dx, self.y + dy
        
        # 检查目标位置是否可通行
        if (0 <= new_y < len(game_world.map) and 
            0 <= new_x < len(game_world.map) and 
            game_world.map[new_y][new_x].terrain.passable):
            self.x, self.y = new_x, new_y
            return True
        return False

class Player(Character):
    """玩家角色"""
    def __init__(self, x, y):
        super().__init__("主角", "@", "yellow", x, y)

class NPC(Character):
    """非玩家角色"""
    def __init__(self, name, x, y):
        symbols = ['☺', '☻', '♠', '♥', '♦', '♣']
        colors = ['light red', 'light magenta', 'light cyan']
        super().__init__(name, random.choice(symbols), random.choice(colors), x, y)
    
    def random_move(self, game_world):
        """NPC随机移动"""
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        dx, dy = random.choice(directions)
        self.move(dx, dy, game_world)

class City:
    """城市类"""
    def __init__(self, name, x, y, width=3, height=2):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.symbol = '◙'
        self.color = 'light blue'
    
    def contains(self, x, y):
        """检查坐标是否在城市范围内"""
        return (self.x <= x < self.x + self.width and 
                self.y <= y < self.y + self.height)

# ======================
# 游戏世界类
# ======================
class GameWorld:
    """游戏世界管理类"""
    def __init__(self, width=100, height=50):
        self.width = width
        self.height = height
        self.map = self.generate_map()
        self.cities = self.generate_cities()
        self.player = Player(width // 2, height // 2)
        self.npcs = self.generate_npcs(10)
        self.turn_count = 0
    
    def generate_map(self):
        """生成随机地形地图"""
        # 使用加权随机选择创建更有趣的地形分布
        terrain_weights = {
            'grass': 40,
            'hills': 20,
            'forest': 15,
            'water': 10,
            'mountain': 10,
            'desert': 5
        }
        
        # 创建基础地图（大部分是草地）
        game_map = [[Tile('grass') for _ in range(self.width)] 
                   for _ in range(self.height)]
        
        # 添加其他地形
        for _ in range(int(self.width * self.height * 0.3)):
            x, y = random.randint(0, self.width-1), random.randint(0, self.height-1)
            terrain = random.choices(
                list(terrain_weights.keys()), 
                weights=list(terrain_weights.values())
            )
            game_map[y][x] = Tile(terrain)
        
        return game_map
    
    def generate_cities(self):
        """生成随机城市"""
        cities = []
        city_names = ["长安", "洛阳", "金陵", "汴梁", "临安", "大都", "成都", "襄阳"]
        
        for name in city_names:
            x = random.randint(10, self.width - 10)
            y = random.randint(10, self.height - 10)
            cities.append(City(name, x, y))
        
        return cities
    
    def generate_npcs(self, count):
        """生成NPC"""
        npcs = []
        npc_names = ["商人", "士兵", "农夫", "旅人", "巫师", "盗贼", "僧侣", "贵族"]
        
        for i in range(count):
            name = f"{random.choice(npc_names)}{i+1}"
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            # 确保NPC生成在可通行区域
            while not self.map[y][x].terrain.passable:
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
            npcs.append(NPC(name, x, y))
        
        return npcs
    
    def move_player(self, dx, dy):
        """移动玩家"""
        if self.player.move(dx, dy, self):
            # 玩家移动后，NPC进行移动
            for npc in self.npcs:
                npc.random_move(self)
            self.turn_count += 1
    
    def get_visible_map(self, view_width, view_height):
        """获取以玩家为中心的可见区域"""
        start_x = max(0, self.player.x - view_width // 2)
        end_x = min(self.width, start_x + view_width)
        
        start_y = max(0, self.player.y - view_height // 2)
        end_y = min(self.height, start_y + view_height)
        
        # 调整边界情况
        if end_x - start_x < view_width:
            start_x = max(0, end_x - view_width)
        if end_y - start_y < view_height:
            start_y = max(0, end_y - view_height)
        
        return start_x, start_y, end_x, end_y
    
    def render_tile(self, x, y):
        """渲染单个地图格子"""
        # 检查玩家
        if x == self.player.x and y == self.player.y:
            return (self.player.symbol, 'player')
        
        # 检查NPC
        for npc in self.npcs:
            if npc.x == x and npc.y == y:
                return (npc.symbol, npc.color)
        
        # 检查城市
        for city in self.cities:
            if city.contains(x, y):
                return (city.symbol, city.color)
        
        # 返回地形
        tile = self.map[y][x]
        return (tile.terrain.symbol, tile.terrain.color)

# ======================
# Urwid界面类
# ======================
class GameDisplay(urwid.WidgetWrap):
    """游戏主界面"""
    def __init__(self):
        # 创建游戏世界
        self.world = GameWorld()
        
        # 设置视图大小
        self.view_width = 80
        self.view_height = 24
        
        # 创建地图显示部件
        self.map_walker = urwid.SimpleListWalker([])
        self.map_listbox = urwid.ListBox(self.map_walker)
        
        # 创建状态栏
        self.status_text = urwid.Text("准备开始游戏...")
        self.status_bar = urwid.AttrMap(self.status_text, 'status')
        
        # 创建主框架
        self.frame = urwid.Frame(
            body=urwid.AttrMap(self.map_listbox, 'bg'),
            footer=self.status_bar
        )
        
        super().__init__(self.frame)
        self.refresh_map()
        self.update_status()
    
    def refresh_map(self):
        """刷新地图显示"""
        # 获取可见区域
        start_x, start_y, end_x, end_y = self.world.get_visible_map(
            self.view_width, self.view_height
        )
        
        # 清空当前显示
        del self.map_walker[:]
        
        # 渲染可见区域
        for y in range(start_y, end_y):
            row_widgets = []
            for x in range(start_x, end_x):
                symbol, color_attr = self.world.render_tile(x, y)
                # 创建带颜色的文本部件
                row_widgets.append(urwid.AttrMap(
                    urwid.Text(symbol, align='center'), 
                    color_attr
                ))
            # 将一行中的所有格子组合成Columns
            self.map_walker.append(urwid.Columns(row_widgets))
    
    def update_status(self):
        """更新状态栏信息"""
        player = self.world.player
        status = (
            f"回合: {self.world.turn_count} | 位置: ({player.x}, {player.y}) | "
            f"HP: {player.hp} | 地形: {self.world.map[player.y][player.x].terrain.name}"
        )
        self.status_text.set_text(status)
    
    def keypress(self, size, key):
        """处理键盘输入"""
        # 移动控制
        if key == 'w':
            self.world.move_player(0, -1)
        elif key == 's':
            self.world.move_player(0, 1)
        elif key == 'a':
            self.world.move_player(-1, 0)
        elif key == 'd':
            self.world.move_player(1, 0)
        elif key == 'q':
            raise urwid.ExitMainLoop()
        
        # 刷新界面
        self.refresh_map()
        self.update_status()
        return key

# ======================
# 主函数
# ======================
def main():
    # 创建调色板
    palette = [
        ('bg', 'black', 'black'),
        ('status', 'white', 'dark blue'),
        ('player', 'yellow,bold', 'black'),
        ('light green', 'light green', 'black'),
        ('brown', 'brown', 'black'),
        ('dark green', 'dark green', 'black'),
        ('light blue', 'light blue', 'black'),
        ('dark gray', 'dark gray', 'black'),
        ('yellow', 'yellow', 'black'),
        ('light red', 'light red', 'black'),
        ('light magenta', 'light magenta', 'black'),
        ('light cyan', 'light cyan', 'black'),
    ]
    
    # 添加地形颜色
    for terrain in TERRAIN_TYPES.values():
        if terrain.color not in [p for p in palette]:
            palette.append((terrain.color, terrain.color, 'black'))
    
    # 创建游戏界面
    game = GameDisplay()
    
    # 设置主循环
    loop = urwid.MainLoop(
        game,
        palette,
        unhandled_input=game.keypress,
        handle_mouse=False
    )
    
    # 启动游戏
    loop.run()

if __name__ == '__main__':
    main()
