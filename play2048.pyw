import pygame
import random
import time
import os
import sys

# 初始化 Pygame
pygame.init()

# 遊戲視窗設定
WIDTH = 600
HEIGHT = 930 # 總高度以容納所有UI元素

GRID_SIZE = 4
TILE_SIZE = 120
PADDING = 15
FONT_SIZE_TITLE = 50
FONT_SIZE_SCORE_TIME = 30
FONT_SIZE_MENU = 40 # 選單按鈕字體大小
SCORE_HEIGHT = 100 # 分數和時間區域的高度
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2048 遊戲")

# 顏色定義
BACKGROUND_COLOR = (187, 173, 160)
GRID_COLOR = (205, 192, 180)
TEXT_COLOR_LIGHT = (249, 246, 242)
TEXT_COLOR_DARK = (119, 110, 101)
BUTTON_COLOR = (90, 80, 70)
BUTTON_HOVER_COLOR = (110, 100, 90) # 按鈕懸停顏色
PAUSE_OVERLAY_COLOR = (0, 0, 0, 180) # 更深一點的半透明黑色
PAUSE_BUTTON_COLOR = (70, 70, 70) # 暫停按鈕顏色
PAUSE_BUTTON_HOVER_COLOR = (100, 100, 100) # 暫停按鈕懸停顏色
BUTTON_BORDER_COLOR = (40, 40, 40) # 按鈕邊框顏色 (深灰色)
BUTTON_BORDER_WIDTH = 3 # 按鈕邊框寬度


TILE_COLORS = {
    0: (205, 192, 180),
    2: (238, 228, 218),
    4: (237, 224, 200),
    8: (242, 177, 121),
    16: (245, 149, 99),
    32: (246, 124, 95),
    64: (246, 94, 59),
    128: (237, 207, 114),
    256: (237, 204, 97),
    512: (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46),
    4096: (60, 58, 50),
    8192: (60, 58, 50),
}

# 字體設定
FONT = None
SMALL_FONT = None
MENU_FONT = None

chinese_fonts_priority = []
if sys.platform == "win32":
    chinese_fonts_priority = ['Microsoft YaHei', 'SimHei', 'KaiTi', 'FangSong', 'msjh', 'DengXian']
elif sys.platform == "darwin":
    chinese_fonts_priority = ['PingFang SC', 'STHeiti', 'Apple LiGothic', 'LiHei Pro']
else:
    chinese_fonts_priority = ['Noto Sans CJK JP', 'Noto Sans CJK SC', 'wqy-zenhei', 'WenQuanYi Zen Hei', 'AR PL UMing CN', 'AR PL KaitiM GB']

found_font_path = None
for font_name in chinese_fonts_priority:
    match = pygame.font.match_font(font_name, bold=False, italic=False)
    if match:
        found_font_path = match
        print(f"成功找到並載入字體: {font_name} (路徑: {found_font_path})")
        break

if found_font_path:
    try:
        FONT = pygame.font.Font(found_font_path, FONT_SIZE_TITLE)
        SMALL_FONT = pygame.font.Font(found_font_path, FONT_SIZE_SCORE_TIME)
        MENU_FONT = pygame.font.Font(found_font_path, FONT_SIZE_MENU)
    except pygame.error as e:
        print(f"載入字體 {found_font_path} 時發生錯誤: {e}")
        FONT = None
        SMALL_FONT = None
        MENU_FONT = None
else:
    print("未在系統中找到任何推薦的中文字體。")

if FONT is None:
    print("未能載入任何中文字體，將使用 Pygame 預設字體。部分中文字符可能無法正確顯示。")
    FONT = pygame.font.Font(None, FONT_SIZE_TITLE)
    SMALL_FONT = pygame.font.Font(None, FONT_SIZE_SCORE_TIME)
    MENU_FONT = pygame.font.Font(None, FONT_SIZE_MENU)


# --- 動畫相關常數和類別 ---
ANIMATION_DURATION_VALUES = [0.15, 0.08, 0.03] # 動畫持續時間選項：慢，正常，快
ANIMATION_DURATION_LABELS = ["慢", "中", "快"]
FPS_VALUES = [30, 60, 90, 120] # FPS 選項
FPS_LABELS = ["30 FPS", "60 FPS", "90 FPS", "120 FPS"]


class TileAnimation:
    """用於追蹤單個方塊動畫的狀態。"""
    def __init__(self, value, start_r, start_c, end_r, end_c, anim_type='slide', current_animation_duration=0.08):
        self.value = value
        self.start_r = start_r
        self.start_c = start_c
        self.end_r = end_r
        self.end_c = end_c
        self.anim_type = anim_type
        self.start_time = time.time()
        self.duration = current_animation_duration # 使用動態的動畫持續時間

    def get_current_visual_state(self, current_time, base_x_offset, base_y_offset):
        elapsed = current_time - self.start_time
        t = min(1, elapsed / self.duration)

        start_pixel_x = base_x_offset + self.start_c * (TILE_SIZE + PADDING)
        start_pixel_y = base_y_offset + self.start_r * (TILE_SIZE + PADDING)
        end_pixel_x = base_x_offset + self.end_c * (TILE_SIZE + PADDING)
        end_pixel_y = base_y_offset + self.end_r * (TILE_SIZE + PADDING)

        current_x, current_y = start_pixel_x + (end_pixel_x - start_pixel_x) * t, \
                                start_pixel_y + (end_pixel_y - start_pixel_y) * t
        scale = 1.0
        alpha = 255

        if self.anim_type == 'new_appear' or self.anim_type == 'merge_scale_up':
            current_x, current_y = end_pixel_x, end_pixel_y
            scale = 0.2 + (1.0 - 0.2) * t # TILE_POP_SCALE_START 和 TILE_POP_SCALE_END
        elif self.anim_type == 'disappear':
            current_x, current_y = start_pixel_x, start_pixel_y
            scale = 1.0 - t * 0.5
            alpha = int(255 * (1.0 - t))

        scaled_tile_size = TILE_SIZE * scale
        adjusted_x = current_x + (TILE_SIZE - scaled_tile_size) / 2
        adjusted_y = current_y + (TILE_SIZE - scaled_tile_size) / 2

        return adjusted_x, adjusted_y, scaled_tile_size, scaled_tile_size, alpha

    def is_finished(self, current_time):
        return (current_time - self.start_time) >= self.duration

class ButtonFlash:
    """用於追蹤單個按鈕閃爍動畫的狀態。"""
    def __init__(self, rect):
        self.rect = rect
        self.start_time = time.time()
        self.duration = 0.1 # 閃爍動畫持續時間 (秒)

    def get_current_alpha(self, current_time):
        elapsed = current_time - self.start_time
        t = min(1, elapsed / self.duration)
        # 調整起始透明度，讓閃爍效果更柔和
        initial_max_alpha = 180 # 從較低的透明度開始，例如 180 (最大 255)
        alpha = int(initial_max_alpha * (1.0 - t))
        return alpha

    def is_finished(self, current_time):
        return (current_time - self.start_time) >= self.duration

class Dropdown:
    """自定義下拉選單 UI 元件。"""
    def __init__(self, rect, options, initial_index, font, main_button_text=""):
        self.rect = rect
        self.options = options
        self.selected_index = initial_index
        self.font = font
        self.is_open = False
        self.option_rects = []
        self.main_button_text = main_button_text # 主按鈕顯示的固定文字 (例如 "FPS:")

    def draw(self, surface, mouse_pos):
        # 繪製主按鈕
        display_text = f"{self.main_button_text} {self.options[self.selected_index]}" if self.main_button_text else self.options[self.selected_index]
        main_color = BUTTON_HOVER_COLOR if self.rect.collidepoint(mouse_pos) else BUTTON_COLOR
        # 根據您的要求，這裡主下拉選單按鈕也套用邊框
        draw_button(self.rect, display_text, self.font, main_color, TEXT_COLOR_LIGHT, BUTTON_BORDER_COLOR, BUTTON_BORDER_WIDTH)

    def draw_options(self, surface, mouse_pos): # 新增的方法，用於單獨繪製選項
        """只繪製下拉選單的選項部分。"""
        self.option_rects = []
        if self.is_open:
            start_y = self.rect.y + self.rect.height 
            for i, option in enumerate(self.options):
                option_rect = pygame.Rect(self.rect.x, start_y + i * self.rect.height, self.rect.width, self.rect.height)
                self.option_rects.append(option_rect)
                
                option_color = BUTTON_HOVER_COLOR if option_rect.collidepoint(mouse_pos) else BUTTON_COLOR
                # 這裡為下拉選單的選項按鈕套用邊框
                draw_button(option_rect, option, self.font, option_color, TEXT_COLOR_LIGHT, BUTTON_BORDER_COLOR, BUTTON_BORDER_WIDTH)

    def handle_click(self, mouse_pos):
        # 點擊主按鈕
        if self.rect.collidepoint(mouse_pos):
            self.is_open = not self.is_open
            return self.selected_index # 返回當前選中項的索引，表示主按鈕被點擊

        # 如果下拉選單打開，檢查是否點擊了選項
        if self.is_open:
            for i, option_rect in enumerate(self.option_rects):
                if option_rect.collidepoint(mouse_pos):
                    self.selected_index = i
                    self.is_open = False # 選擇後關閉下拉選單
                    return self.selected_index # 返回新的選中項索引
        return None # 沒有點擊下拉選單或點擊了外部

    def close(self):
        """強制關閉下拉選單。"""
        self.is_open = False


# 全域遊戲狀態變數
GAME_STATE = 'start_menu' # 'start_menu', 'playing', 'paused', 'settings_menu', 'game_summary'
is_animating = False
active_animations = []
# 將 active_button_flash 定義為全域變數
active_button_flash = None 

# 遊戲數據變數
board = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
score = 0
start_time = 0
elapsed_time_on_pause = 0 # 暫停時累計的遊戲時間
game_over = False
high_score = 0 # 假設最高紀錄在當前會話中保持

# 設定相關變數
current_fps_index = FPS_VALUES.index(60) # 預設 60 FPS
current_animation_duration_index = ANIMATION_DURATION_VALUES.index(0.08) # 預設正常動畫速度
vsync_enabled = False # 垂直同步開關


# ----------------- 遊戲邏輯輔助函數 -----------------

def get_column(board_data, c):
    return [board_data[r][c] for r in range(GRID_SIZE)]

def get_row(board_data, r):
    return board_data[r]

def set_column(board_data, c, new_col):
    for r in range(GRID_SIZE):
        board_data[r][c] = new_col[r]

def set_row(board_data, r, new_row):
    board_data[r] = new_row

def simulate_slide_and_merge_for_animation(line_cells_with_original_indices, is_reversed=False):
    active_cells = [(val, orig_idx) for val, orig_idx in line_cells_with_original_indices if val != 0]
    final_values = [0] * GRID_SIZE
    operations = []
    score_gain = 0
    k = 0
    i = 0

    while i < len(active_cells):
        current_val, current_orig_idx = active_cells[i]
        if i + 1 < len(active_cells) and active_cells[i+1][0] == current_val:
            merged_value = current_val * 2
            final_values[k] = merged_value
            score_gain += merged_value
            operations.append({
                'type': 'merge',
                'value': merged_value,
                'from_idx1': current_orig_idx,
                'from_idx2': active_cells[i+1][1],
                'to_idx': k
            })
            i += 2
        else:
            final_values[k] = current_val
            operations.append({
                'type': 'slide',
                'value': current_val,
                'from_idx': current_orig_idx,
                'to_idx': k
            })
            i += 1
        k += 1
    return final_values, score_gain, operations

# ----------------- 遊戲核心邏輯 -----------------

def initialize_board():
    """初始化棋盤和遊戲狀態。"""
    global board, score, start_time, elapsed_time_on_pause, game_over, active_animations, is_animating, active_button_flash 
    board = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    score = 0
    start_time = time.time()
    elapsed_time_on_pause = 0
    game_over = False
    active_animations = []
    active_button_flash = None 
    is_animating = False
    
    add_new_tile(initial_setup=True)
    add_new_tile(initial_setup=True)

def add_new_tile(initial_setup=False):
    """
    在隨機的空位添加一個新的 2 或 4 方塊，並為其創建動畫。
    """
    empty_cells = []
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] == 0:
                empty_cells.append((r, c))
    if empty_cells:
        r, c = random.choice(empty_cells)
        new_tile_value = random.choice([2, 4])
        board[r][c] = new_tile_value
        
        active_animations.append(TileAnimation(
            value=new_tile_value,
            start_r=r, start_c=c,
            end_r=r, end_c=c,
            anim_type='new_appear',
            current_animation_duration=ANIMATION_DURATION_VALUES[current_animation_duration_index]
        ))
        if not initial_setup:
            global is_animating
            is_animating = True

def move(direction):
    """
    根據方向移動方塊，並生成相應的動畫。
    """
    global board, score, active_animations, is_animating

    if is_animating:
        return False

    original_board = [row[:] for row in board]
    temp_board = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    total_score_gain = 0
    current_move_animations = []

    axis_is_rows = (direction == "LEFT" or direction == "RIGHT")
    is_reversed_op = (direction == "RIGHT" or direction == "DOWN")

    for i in range(GRID_SIZE):
        line_values_with_indices = []
        if axis_is_rows:
            line_values_with_indices = [(original_board[i][c], c) for c in range(GRID_SIZE)]
            if is_reversed_op:
                line_values_with_indices.reverse()
            
            final_line, score_gain_line, operations = simulate_slide_and_merge_for_animation(line_values_with_indices)
            total_score_gain += score_gain_line

            if is_reversed_op:
                set_row(temp_board, i, final_line[::-1])
            else:
                set_row(temp_board, i, final_line)
            
            for op in operations:
                if op['type'] == 'slide':
                    current_move_animations.append(TileAnimation(
                        value=op['value'],
                        start_r=i, start_c=op['from_idx'],
                        end_r=i, end_c=op['to_idx'],
                        anim_type='slide',
                        current_animation_duration=ANIMATION_DURATION_VALUES[current_animation_duration_index]
                    ))
                elif op['type'] == 'merge':
                    current_move_animations.append(TileAnimation(
                        value=op['value'],
                        start_r=i, start_c=op['to_idx'],
                        end_r=i, end_c=op['to_idx'],
                        anim_type='merge_scale_up',
                        current_animation_duration=ANIMATION_DURATION_VALUES[current_animation_duration_index]
                    ))
                    current_move_animations.append(TileAnimation(
                        value=original_board[i][op['from_idx1']],
                        start_r=i, start_c=op['from_idx1'],
                        end_r=i, end_c=op['to_idx'],
                        anim_type='disappear',
                        current_animation_duration=ANIMATION_DURATION_VALUES[current_animation_duration_index]
                    ))
                    current_move_animations.append(TileAnimation(
                        value=original_board[i][op['from_idx2']],
                        start_r=i, start_c=op['from_idx2'],
                        end_r=i, end_c=op['to_idx'],
                        anim_type='disappear',
                        current_animation_duration=ANIMATION_DURATION_VALUES[current_animation_duration_index]
                    ))
        else: # 處理列 (垂直移動)
            line_values_with_indices = [(original_board[r][i], r) for r in range(GRID_SIZE)]
            if is_reversed_op:
                line_values_with_indices.reverse()
            
            final_line, score_gain_line, operations = simulate_slide_and_merge_for_animation(line_values_with_indices)
            total_score_gain += score_gain_line

            if is_reversed_op:
                set_column(temp_board, i, final_line[::-1])
            else:
                set_column(temp_board, i, final_line)
            
            for op in operations:
                if op['type'] == 'slide':
                    current_move_animations.append(TileAnimation(
                        value=op['value'],
                        start_r=op['from_idx'], start_c=i,
                        end_r=op['to_idx'], end_c=i,
                        anim_type='slide',
                        current_animation_duration=ANIMATION_DURATION_VALUES[current_animation_duration_index]
                    ))
                elif op['type'] == 'merge':
                    current_move_animations.append(TileAnimation(
                        value=op['value'],
                        start_r=op['to_idx'], start_c=i,
                        end_r=op['to_idx'], end_c=i,
                        anim_type='merge_scale_up',
                        current_animation_duration=ANIMATION_DURATION_VALUES[current_animation_duration_index]
                    ))
                    current_move_animations.append(TileAnimation(
                        value=original_board[op['from_idx1']][i],
                        start_r=op['from_idx1'], start_c=i,
                        end_r=op['to_idx'], end_c=i,
                        anim_type='disappear',
                        current_animation_duration=ANIMATION_DURATION_VALUES[current_animation_duration_index]
                    ))
                    current_move_animations.append(TileAnimation(
                        value=original_board[op['from_idx2']][i],
                        start_r=op['from_idx2'], start_c=i,
                        end_r=op['to_idx'], end_c=i,
                        anim_type='disappear',
                        current_animation_duration=ANIMATION_DURATION_VALUES[current_animation_duration_index]
                    ))
    
    moved_anything = False
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if original_board[r][c] != temp_board[r][c]:
                moved_anything = True
                break
        if moved_anything:
            break

    if moved_anything:
        score += total_score_gain
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                board[r][c] = temp_board[r][c]

        add_new_tile()
        active_animations.extend(current_move_animations)
        is_animating = True

    return moved_anything

def check_game_over():
    """檢查遊戲是否結束 (沒有空位且沒有可合併的方塊)"""
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] == 0:
                return False
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if c < GRID_SIZE - 1 and board[r][c] == board[r][c+1]:
                return False
            if r < GRID_SIZE - 1 and board[r][c] == board[r+1][c]:
                return False
    return True

# ----------------- 繪圖函數 -----------------

def draw_button(rect, text, font, color, text_color, border_color=None, border_width=0):
    """繪製通用按鈕，可選帶有邊框。"""
    if border_color and border_width > 0:
        # Draw the border rectangle first, slightly larger
        border_rect = pygame.Rect(rect.x - border_width, rect.y - border_width,
                                  rect.width + 2 * border_width, rect.height + 2 * border_width)
        # 邊框的圓角可以比按鈕本身稍大，使其看起來更自然
        pygame.draw.rect(SCREEN, border_color, border_rect, border_radius=10 + border_width)
    
    # Draw the main button fill
    pygame.draw.rect(SCREEN, color, rect, border_radius=10)
    
    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=rect.center)
    SCREEN.blit(text_surface, text_rect)

def draw_start_menu():
    """繪製遊戲開始選單。"""
    SCREEN.fill(BACKGROUND_COLOR)
    
    title_text = FONT.render("2048 遊戲", True, TEXT_COLOR_DARK)
    title_rect = title_text.get_rect(center=(WIDTH / 2, HEIGHT / 4))
    SCREEN.blit(title_text, title_rect)

    start_button_rect = pygame.Rect(WIDTH / 2 - 120, HEIGHT / 2 - 30, 240, 60)
    # 套用邊框
    draw_button(start_button_rect, "開始遊戲", MENU_FONT, BUTTON_COLOR, TEXT_COLOR_LIGHT, BUTTON_BORDER_COLOR, BUTTON_BORDER_WIDTH)

    settings_button_rect = pygame.Rect(WIDTH / 2 - 120, HEIGHT / 2 + 50, 240, 60)
    # 套用邊框
    draw_button(settings_button_rect, "設定", MENU_FONT, BUTTON_COLOR, TEXT_COLOR_LIGHT, BUTTON_BORDER_COLOR, BUTTON_BORDER_WIDTH)

    # 新增的「離開遊戲」按鈕
    quit_game_button_rect = pygame.Rect(WIDTH / 2 - 120, HEIGHT / 2 + 130, 240, 60)
    # 套用邊框
    draw_button(quit_game_button_rect, "離開遊戲", MENU_FONT, BUTTON_COLOR, TEXT_COLOR_LIGHT, BUTTON_BORDER_COLOR, BUTTON_BORDER_WIDTH)

    return {"start": start_button_rect, "settings": settings_button_rect, "quit_game": quit_game_button_rect}

# 聲明為全域變數，以便在事件處理循環中訪問
fps_dropdown_instance = None
anim_dropdown_instance = None


def draw_settings_menu(mouse_pos):
    """繪製設定選單。"""
    global fps_dropdown_instance, anim_dropdown_instance, vsync_enabled

    SCREEN.fill(BACKGROUND_COLOR)

    title_text = FONT.render("設定", True, TEXT_COLOR_DARK)
    title_rect = title_text.get_rect(center=(WIDTH / 2, HEIGHT / 4 - 50))
    SCREEN.blit(title_text, title_rect)

    # FPS 設定 (下拉選單) 的標籤和位置
    fps_label_x = WIDTH / 2 - 220 
    fps_label_y = HEIGHT / 2 - 90
    fps_label = SMALL_FONT.render("幀數 (FPS):", True, TEXT_COLOR_DARK)
    SCREEN.blit(fps_label, (fps_label_x, fps_label_y))
    
    # FPS 下拉選單主按鈕的位置
    # 調整為更小的寬度以騰出更多空間給 V-Sync 按鈕
    fps_dropdown_rect = pygame.Rect(fps_label_x + 150, fps_label_y, 100, 40) 
    if fps_dropdown_instance is None:
        fps_dropdown_instance = Dropdown(fps_dropdown_rect, FPS_LABELS, current_fps_index, SMALL_FONT)
    else: 
        fps_dropdown_instance.rect = fps_dropdown_rect
    
    # 這裡只繪製主按鈕部分，選項列表會在後面單獨繪製，以確保其在最上層
    fps_dropdown_instance.draw(SCREEN, mouse_pos) 

    # 垂直同步 (V-Sync) 切換按鈕，緊鄰 FPS 下拉選單的右側
    # 調整寬度以確保文字顯示完整
    vsync_button_width = 180 # 增加寬度以適應 "垂直同步: 開/關"，比 170 更寬
    vsync_button_height = 40
    vsync_button_rect = pygame.Rect(
        fps_dropdown_rect.x + fps_dropdown_rect.width + PADDING, 
        fps_label_y, 
        vsync_button_width,
        vsync_button_height
    )
    vsync_text = f"垂直同步: {'開' if vsync_enabled else '關'}" 
    # 套用邊框
    draw_button(vsync_button_rect, vsync_text, SMALL_FONT, BUTTON_COLOR, TEXT_COLOR_LIGHT, BUTTON_BORDER_COLOR, BUTTON_BORDER_WIDTH)


    # 動畫速度設定 (下拉選單) 的標籤和位置
    anim_label_x = WIDTH / 2 - 180
    anim_label_y = HEIGHT / 2 + 30 
    anim_label = SMALL_FONT.render("動畫速度:", True, TEXT_COLOR_DARK)
    SCREEN.blit(anim_label, (anim_label_x, anim_label_y))

    # 動畫速度下拉選單主按鈕的位置
    anim_dropdown_rect = pygame.Rect(WIDTH / 2 - 20, anim_label_y, 180, 40)
    if anim_dropdown_instance is None:
        anim_dropdown_instance = Dropdown(anim_dropdown_rect, ANIMATION_DURATION_LABELS, current_animation_duration_index, SMALL_FONT)
    else: 
        anim_dropdown_instance.rect = anim_dropdown_rect
    
    # 這裡只繪製主按鈕部分，選項列表會在後面單獨繪製，以確保其在最上層
    anim_dropdown_instance.draw(SCREEN, mouse_pos) 


    # 返回按鈕
    back_button_rect = pygame.Rect(WIDTH / 2 - 100, HEIGHT / 2 + 190, 200, 60) 
    # 套用邊框
    draw_button(back_button_rect, "返回", MENU_FONT, BUTTON_COLOR, TEXT_COLOR_LIGHT, BUTTON_BORDER_COLOR, BUTTON_BORDER_WIDTH)

    return {
        "fps_dropdown": fps_dropdown_instance,
        "anim_dropdown": anim_dropdown_instance,
        "vsync_button": vsync_button_rect,
        "back_button": back_button_rect
    }


def draw_pause_menu(mouse_pos):
    """
    繪製暫停選單的按鈕和文字。不再繪製疊加層，由主迴圈負責。
    """
    # 暫停標題
    pause_text = FONT.render("遊戲暫停", True, TEXT_COLOR_LIGHT)
    # 調整文字位置，使其更高，為按鈕騰出空間
    text_rect = pause_text.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 220)) 
    SCREEN.blit(pause_text, text_rect)

    button_width = 280
    button_height = 70
    button_gap = 25 # 按鈕之間的間距

    # 計算按鈕起始Y座標，使其位於文字下方且垂直居中
    # 將第一個按鈕的 Y 座標設置在畫面上方一點，確保與標題不重疊
    first_button_y = HEIGHT / 2 - 50 # 調整此值以控制按鈕組的垂直位置
    
    continue_button_rect = pygame.Rect(WIDTH / 2 - button_width / 2, first_button_y, button_width, button_height)
    restart_button_rect = pygame.Rect(WIDTH / 2 - button_width / 2, first_button_y + button_height + button_gap, button_width, button_height)
    quit_button_rect = pygame.Rect(WIDTH / 2 - button_width / 2, first_button_y + 2 * (button_height + button_gap), button_width, button_height)

    # 根據滑鼠位置改變按鈕顏色，提供視覺回饋
    continue_color = PAUSE_BUTTON_HOVER_COLOR if continue_button_rect.collidepoint(mouse_pos) else PAUSE_BUTTON_COLOR
    restart_color = PAUSE_BUTTON_HOVER_COLOR if restart_button_rect.collidepoint(mouse_pos) else PAUSE_BUTTON_COLOR
    quit_color = PAUSE_BUTTON_HOVER_COLOR if quit_button_rect.collidepoint(mouse_pos) else PAUSE_BUTTON_COLOR

    # 繪製帶有邊框的按鈕
    draw_button(continue_button_rect, "繼續遊戲", MENU_FONT, continue_color, TEXT_COLOR_LIGHT, BUTTON_BORDER_COLOR, BUTTON_BORDER_WIDTH)
    draw_button(restart_button_rect, "重新開始", MENU_FONT, restart_color, TEXT_COLOR_LIGHT, BUTTON_BORDER_COLOR, BUTTON_BORDER_WIDTH)
    draw_button(quit_button_rect, "停止遊玩", MENU_FONT, quit_color, TEXT_COLOR_LIGHT, BUTTON_BORDER_COLOR, BUTTON_BORDER_WIDTH)

    return {"continue": continue_button_rect, "restart": restart_button_rect, "quit": quit_button_rect}

def draw_game_summary_screen():
    """繪製遊戲總結畫面。"""
    global score, high_score, elapsed_time_on_pause # 從暫停時的時間開始計算

    SCREEN.fill(BACKGROUND_COLOR)

    title_text = FONT.render("遊戲結束!", True, TEXT_COLOR_DARK)
    title_rect = title_text.get_rect(center=(WIDTH / 2, HEIGHT / 4 - 50))
    SCREEN.blit(title_text, title_rect)

    # 總分數
    final_score_text = MENU_FONT.render(f"總分數: {score}", True, TEXT_COLOR_DARK)
    final_score_rect = final_score_text.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 50))
    SCREEN.blit(final_score_text, final_score_rect)

    # 使用時間
    total_time_seconds = elapsed_time_on_pause
    minutes = int(total_time_seconds // 60)
    seconds = int(total_time_seconds % 60)
    milliseconds = int((total_time_seconds * 100) % 100)
    time_text = MENU_FONT.render(f"使用時間: {minutes:02}:{seconds:02}.{milliseconds:02}", True, TEXT_COLOR_DARK)
    time_rect = time_text.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 10))
    SCREEN.blit(time_text, time_rect)

    # 最高紀錄
    if score > high_score:
        high_score = score # 更新最高紀錄
        new_record_text = SMALL_FONT.render("(新紀錄!)", True, (255, 0, 0)) # 紅色提示
        new_record_rect = new_record_text.get_rect(center=(WIDTH / 2 + 80, HEIGHT / 2 + 70))
        SCREEN.blit(new_record_text, new_record_rect)

    high_score_text = MENU_FONT.render(f"最高紀錄: {high_score}", True, TEXT_COLOR_DARK)
    high_score_rect = high_score_text.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 70))
    SCREEN.blit(high_score_text, high_score_rect)

    # 返回主選單按鈕
    back_to_menu_button_rect = pygame.Rect(WIDTH / 2 - 120, HEIGHT / 2 + 150, 240, 60)
    # 套用邊框
    draw_button(back_to_menu_button_rect, "返回主選單", MENU_FONT, BUTTON_COLOR, TEXT_COLOR_LIGHT, BUTTON_BORDER_COLOR, BUTTON_BORDER_WIDTH)

    return {"back_to_menu": back_to_menu_button_rect}


def draw_game_board_only():
    """繪製遊戲棋盤和方塊，不包括分數、時間和暫停按鈕。"""
    global active_animations, is_animating

    # 先填充背景色，清除上一次的繪圖
    SCREEN.fill(BACKGROUND_COLOR)

    board_offset_y = SCORE_HEIGHT + PADDING

    # 1. 繪製棋盤背景 (空的方塊)
    pygame.draw.rect(SCREEN, GRID_COLOR, (PADDING, board_offset_y, WIDTH - 2 * PADDING, WIDTH - 2 * PADDING), border_radius=10)
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            x = PADDING + c * (TILE_SIZE + PADDING)
            y = board_offset_y + r * (TILE_SIZE + PADDING)
            pygame.draw.rect(SCREEN, TILE_COLORS[0], (x, y, TILE_SIZE, TILE_SIZE), border_radius=8)

    # 2. 確定哪些位置有正在播放動畫的方塊，這些位置的靜態方塊不應該被繪製
    animated_positions = set()
    for anim in active_animations:
        animated_positions.add((anim.start_r, anim.start_c))
        animated_positions.add((anim.end_r, anim.end_c))

    # 3. 繪製靜態方塊 (不在動畫中的方塊)
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] != 0 and (r, c) not in animated_positions:
                value = board[r][c]
                x = PADDING + c * (TILE_SIZE + PADDING)
                y = board_offset_y + r * (TILE_SIZE + PADDING)

                tile_color = TILE_COLORS.get(value, TILE_COLORS[4096])
                pygame.draw.rect(SCREEN, tile_color, (x, y, TILE_SIZE, TILE_SIZE), border_radius=8)

                text_color = TEXT_COLOR_DARK if value < 8 else TEXT_COLOR_LIGHT
                text = FONT.render(str(value), True, text_color)
                text_rect = text.get_rect(center=(x + TILE_SIZE / 2, y + TILE_SIZE / 2))
                SCREEN.blit(text, text_rect)

    # 4. 繪製所有活躍的動畫方塊
    current_frame_time = time.time()
    new_animations_list = []

    animations_to_draw_disappear = [a for a in active_animations if a.anim_type == 'disappear']
    animations_to_draw_others = [a for a in active_animations if a.anim_type != 'disappear']

    for anim_list in [animations_to_draw_disappear, animations_to_draw_others]:
        for anim in anim_list:
            if not anim.is_finished(current_frame_time):
                new_animations_list.append(anim)

                current_x, current_y, current_width, current_height, alpha = anim.get_current_visual_state(
                    current_frame_time, PADDING, board_offset_y
                )

                tile_color = list(TILE_COLORS.get(anim.value, TILE_COLORS[4096]))
                
                if anim.anim_type == 'disappear':
                    tile_surface = pygame.Surface((current_width, current_height), pygame.SRCALPHA)
                    tile_surface.fill(tile_color + [alpha])
                    SCREEN.blit(tile_surface, (current_x, current_y))
                else:
                    pygame.draw.rect(SCREEN, tile_color, 
                                     (current_x, current_y, current_width, current_height), 
                                     border_radius=8)
                
                if anim.value != 0:
                    text_color = TEXT_COLOR_DARK if anim.value < 8 else TEXT_COLOR_LIGHT
                    text_surface = FONT.render(str(anim.value), True, text_color)
                    
                    text_rect = text_surface.get_rect(center=(current_x + current_width / 2, current_y + current_height / 2))
                    SCREEN.blit(text_surface, text_rect)

    active_animations = new_animations_list

    if not active_animations:
        is_animating = False

# 新增的函式，用於繪製頂部計分板區域（分數、時間和暫停按鈕）
def draw_top_bar():
    """繪製頂部計分板區域（分數、時間和暫停按鈕）。"""
    # 繪製分數和時間區域的背景
    pygame.draw.rect(SCREEN, (50, 50, 50), (0, 0, WIDTH, SCORE_HEIGHT), border_radius=10)

    # 顯示分數
    score_text = SMALL_FONT.render(f"分數: {score}", True, TEXT_COLOR_LIGHT)
    SCREEN.blit(score_text, (PADDING, PADDING))

    # 顯示時間
    current_time_display = time.time() - start_time + elapsed_time_on_pause if GAME_STATE == 'playing' else elapsed_time_on_pause
    minutes = int(current_time_display // 60)
    seconds = int(current_time_display % 60)
    milliseconds = int((current_time_display * 100) % 100)
    timer_text_str = f"時間: {minutes:02}:{seconds:02}.{milliseconds:02}"
    timer_text = SMALL_FONT.render(timer_text_str, True, TEXT_COLOR_LIGHT)
    
    # 獲取碼表文字的矩形，然後強制其中心點在指定位置
    timer_rect = timer_text.get_rect()
    timer_rect.center = (WIDTH / 2, SCORE_HEIGHT / 2) # 置中，不抖動

    SCREEN.blit(timer_text, timer_rect)

    # 暫停按鈕位置計算 (右上角)
    pause_button_width = 80
    pause_button_height = 40
    pause_button_x = WIDTH - PADDING - pause_button_width
    pause_button_y = PADDING 
    pause_button_rect = pygame.Rect(pause_button_x, pause_button_y, pause_button_width, pause_button_height)

    # 繪製暫停按鈕
    draw_button(pause_button_rect, "暫停", SMALL_FONT, BUTTON_COLOR, TEXT_COLOR_LIGHT, BUTTON_BORDER_COLOR, BUTTON_BORDER_WIDTH)
    
    return {"pause_button": pause_button_rect}


def draw_control_buttons():
    """繪製方向按鈕及閃爍動畫。"""
    global active_button_flash 

    button_width = 80
    button_height = 80

    board_offset_y = SCORE_HEIGHT + PADDING
    board_visual_bottom_y = board_offset_y + (WIDTH - 2 * PADDING)

    vertical_gap_after_board = 40

    button_block_start_y = board_visual_bottom_y + vertical_gap_after_board

    buttons = {
        "UP": pygame.Rect(WIDTH / 2 - button_width / 2, button_block_start_y, button_width, button_height),
        "LEFT": pygame.Rect(WIDTH / 2 - button_width * 1.5 - PADDING, button_block_start_y + button_height + PADDING, button_width, button_height),
        "RIGHT": pygame.Rect(WIDTH / 2 + button_width * 0.5 + PADDING, button_block_start_y + button_height + PADDING, button_width, button_height),
        "DOWN": pygame.Rect(WIDTH / 2 - button_width / 2, button_block_start_y + button_height + PADDING, button_width, button_height)
    }

    # 繪製靜態按鈕背景和文字 (套用邊框)
    for direction, rect in buttons.items():
        draw_button(rect, "", FONT, BUTTON_COLOR, TEXT_COLOR_LIGHT, BUTTON_BORDER_COLOR, BUTTON_BORDER_WIDTH) # 使用 draw_button 並套用邊框
        
        text = ""
        if direction == "UP": text = "↑"
        elif direction == "LEFT": text = "←"
        elif direction == "RIGHT": text = "→"
        elif direction == "DOWN": text = "↓"

        arrow_text = FONT.render(text, True, TEXT_COLOR_LIGHT)
        arrow_text_rect = arrow_text.get_rect(center=rect.center)
        SCREEN.blit(arrow_text, arrow_text_rect)

    # 繪製活躍的按鈕閃爍動畫
    current_time = time.time()
    if active_button_flash and not active_button_flash.is_finished(current_time):
        alpha = active_button_flash.get_current_alpha(current_time)
        flash_surface = pygame.Surface(active_button_flash.rect.size, pygame.SRCALPHA)
        flash_surface.fill((255, 255, 255, alpha)) 
        SCREEN.blit(flash_surface, active_button_flash.rect.topleft)
    else:
        active_button_flash = None # 如果動畫結束，則清除

    return buttons

# ----------------- 主遊戲迴圈 -----------------

running = True
clock = pygame.time.Clock()
last_frame_time = time.time() # 用於精確計算暫停時間
current_frame_buttons = {} # 全局變量，用於存儲當前幀的按鈕 Rects

while running:
    delta_time = time.time() - last_frame_time # 計算幀之間的時間差
    last_frame_time = time.time()

    # 根據遊戲狀態更新計時器
    if GAME_STATE == 'playing':
        pass # 時間在 draw_top_bar 裡面更新
    elif GAME_STATE == 'paused':
        start_time += delta_time # 抵消暫停期間的時鐘運行，讓 elapsed_time_on_pause 保持不變

    # --- 繪圖 (並獲取按鈕 Rects) ---
    mouse_pos = pygame.mouse.get_pos() # 獲取滑鼠位置，用於懸停效果

    if GAME_STATE == 'start_menu':
        current_frame_buttons = draw_start_menu()
    elif GAME_STATE == 'settings_menu':
        settings_elements = draw_settings_menu(mouse_pos)
        current_frame_buttons = {
            "fps_dropdown": settings_elements["fps_dropdown"],
            "anim_dropdown": settings_elements["anim_dropdown"],
            "vsync_button": settings_elements["vsync_button"],
            "back_button": settings_elements["back_button"]
        }
        # 在所有靜態元素繪製完畢後，單獨繪製打開的下拉選單選項，確保其在最上層
        if fps_dropdown_instance.is_open:
            # 這裡繪製下拉選單的選項，套用邊框
            fps_dropdown_instance.draw_options(SCREEN, mouse_pos) 
        if anim_dropdown_instance.is_open:
            # 這裡繪製下拉選單的選項，套用邊框
            anim_dropdown_instance.draw_options(SCREEN, mouse_pos) 

    elif GAME_STATE == 'playing':
        draw_game_board_only() # 繪製遊戲棋盤和方塊
        top_bar_elements = draw_top_bar() # 繪製頂部條，並獲取暫停按鈕 Rect
        control_buttons_rects = draw_control_buttons() # 繪製方向按鈕
        # 合併所有按鈕 Rects
        current_frame_buttons = {**top_bar_elements, **control_buttons_rects} 

    elif GAME_STATE == 'paused':
        # 1. 繪製遊戲棋盤和方塊（作為背景）
        draw_game_board_only()
        
        # 2. 繪製覆蓋遊戲棋盤和方向按鈕區域的半透明疊加層
        # 疊加層從 SCORE_HEIGHT (分數條下方) 開始，覆蓋到畫面底部
        overlay_rect = pygame.Rect(0, SCORE_HEIGHT, WIDTH, HEIGHT - SCORE_HEIGHT)
        overlay_surface = pygame.Surface(overlay_rect.size, pygame.SRCALPHA)
        overlay_surface.fill(PAUSE_OVERLAY_COLOR) 
        SCREEN.blit(overlay_surface, overlay_rect.topleft)

        # 3. 繪製頂部條（分數、時間、暫停按鈕），這部分不應被模糊或覆蓋
        top_bar_elements = draw_top_bar() 
        
        # 4. 繪製暫停選單（按鈕和文字）在疊加層之上
        pause_menu_buttons = draw_pause_menu(mouse_pos) 
        
        # 5. 合併所有按鈕 Rects
        current_frame_buttons = {**top_bar_elements, **pause_menu_buttons} 

    elif GAME_STATE == 'game_summary':
        current_frame_buttons = draw_game_summary_screen()


    # --- 事件處理 (使用 current_frame_buttons) ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 處理開始選單按鈕
            if GAME_STATE == 'start_menu':
                if current_frame_buttons["start"].collidepoint(mouse_pos):
                    GAME_STATE = 'playing'
                    initialize_board()
                elif current_frame_buttons["settings"].collidepoint(mouse_pos):
                    GAME_STATE = 'settings_menu'
                elif current_frame_buttons["quit_game"].collidepoint(mouse_pos):
                    running = False 

            # 處理設定選單按鈕和下拉選單
            elif GAME_STATE == 'settings_menu':
                click_handled_by_ui = False

                # 處理 FPS 下拉選單點擊
                fps_selection_changed = fps_dropdown_instance.handle_click(mouse_pos)
                if fps_selection_changed is not None:
                    current_fps_index = fps_selection_changed
                    anim_dropdown_instance.close() # 關閉另一個下拉選單
                    click_handled_by_ui = True
                
                # 如果 FPS 下拉選單沒有處理點擊，嘗試處理動畫速度下拉選單
                if not click_handled_by_ui:
                    anim_selection_changed = anim_dropdown_instance.handle_click(mouse_pos)
                    if anim_selection_changed is not None:
                        current_animation_duration_index = anim_selection_changed
                        fps_dropdown_instance.close() # 關閉另一個下拉選單
                        click_handled_by_ui = True

                # 如果點擊沒有被任何下拉選單處理，再檢查其他按鈕
                if not click_handled_by_ui:
                    if current_frame_buttons["vsync_button"].collidepoint(mouse_pos):
                        vsync_enabled = not vsync_enabled
                        click_handled_by_ui = True
                    elif current_frame_buttons["back_button"].collidepoint(mouse_pos):
                        GAME_STATE = 'start_menu'
                        click_handled_by_ui = True
                    
                    # 如果點擊了 settings_menu 的空白區域，關閉所有打開的下拉選單
                    if not click_handled_by_ui:
                        if fps_dropdown_instance.is_open:
                            fps_dropdown_instance.close()
                        if anim_dropdown_instance.is_open:
                            anim_dropdown_instance.close()

            # 處理遊戲中畫面按鈕 (暫停和方向鍵)
            elif GAME_STATE == 'playing' and not is_animating:
                # 處理暫停按鈕點擊
                # 確保 "pause_button" 在 current_frame_buttons 中，因為 draw_top_bar 會返回它
                if "pause_button" in current_frame_buttons and current_frame_buttons["pause_button"].collidepoint(mouse_pos):
                    GAME_STATE = 'paused'
                    elapsed_time_on_pause += (time.time() - start_time)
                    start_time = time.time()
                # 處理方向按鈕點擊
                for direction, rect in {k: v for k, v in current_frame_buttons.items() if k in ["UP", "DOWN", "LEFT", "RIGHT"]}.items():
                    if rect.collidepoint(mouse_pos):
                        active_button_flash = ButtonFlash(rect) # 添加被點擊按鈕的閃爍動畫
                        if move(direction):
                            if check_game_over():
                                GAME_STATE = 'game_summary'
                                elapsed_time_on_pause += (time.time() - start_time) 
                        break # 只處理一個按鈕點擊
            
            # 處理暫停畫面按鈕
            elif GAME_STATE == 'paused':
                # current_frame_buttons 已經包含了暫停選單按鈕的 rects
                if "continue" in current_frame_buttons and current_frame_buttons["continue"].collidepoint(mouse_pos):
                    GAME_STATE = 'playing'
                    start_time = time.time()
                elif "restart" in current_frame_buttons and current_frame_buttons["restart"].collidepoint(mouse_pos):
                    GAME_STATE = 'playing'
                    initialize_board()
                elif "quit" in current_frame_buttons and current_frame_buttons["quit"].collidepoint(mouse_pos):
                    GAME_STATE = 'game_summary'

            # 處理遊戲總結畫面按鈕
            elif GAME_STATE == 'game_summary':
                if current_frame_buttons["back_to_menu"].collidepoint(mouse_pos):
                    GAME_STATE = 'start_menu' 

        # 鍵盤事件處理
        if event.type == pygame.KEYDOWN:
            if GAME_STATE == 'playing' and not is_animating:
                direction_map = {
                    pygame.K_UP: "UP",
                    pygame.K_DOWN: "DOWN",
                    pygame.K_LEFT: "LEFT",
                    pygame.K_RIGHT: "RIGHT"
                }
                if event.key in direction_map:
                    direction = direction_map[event.key]
                    
                    # 鍵盤按下時，觸發對應按鈕的閃爍效果
                    # 確保 current_frame_buttons 已經包含了正確的方向按鈕 Rect
                    if direction in current_frame_buttons:
                        active_button_flash = ButtonFlash(current_frame_buttons[direction])
                    
                    if move(direction):
                        if check_game_over():
                            GAME_STATE = 'game_summary'
                            elapsed_time_on_pause += (time.time() - start_time)

            # 處理暫停鍵 (Escape)
            if event.key == pygame.K_ESCAPE:
                if GAME_STATE == 'playing':
                    GAME_STATE = 'paused'
                    elapsed_time_on_pause += (time.time() - start_time)
                    start_time = time.time()
                elif GAME_STATE == 'paused':
                    GAME_STATE = 'playing'
                    start_time = time.time()

            # 處理遊戲總結畫面中的返回主選單鍵 (Enter 或 Escape)
            if GAME_STATE == 'game_summary':
                if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                    GAME_STATE = 'start_menu'

    pygame.display.flip()
    
    # 根據 V-Sync 設定調整 FPS 限制
    if vsync_enabled:
        clock.tick(0) # 垂直同步開啟時不限制 FPS，交由系統處理 (Pygame 內部處理 V-Sync)
    else:
        clock.tick(FPS_VALUES[current_fps_index]) # 使用設定的 FPS

pygame.quit()
