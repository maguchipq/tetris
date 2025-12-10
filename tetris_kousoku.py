import tkinter as tk
import random
import copy

# --- 1. 定数とテトリミノの定義 ---

# ゲーム設定
CELL_SIZE = 30  # 1セルの大きさ (ピクセル)
BOARD_WIDTH = 10  # 横のセル数
BOARD_HEIGHT = 20 # 縦のセル数
FALL_SPEED_MS = 1000 # 落下間隔（ミリ秒）

# 色の定義 (インデックス 0は空)
COLORS = [
    "black",    # 0: 空のセル
    "cyan",     # 1: I
    "blue",     # 2: J
    "orange",   # 3: L
    "yellow",   # 4: O
    "lime green", # 5: S
    "purple",   # 6: T
    "red",      # 7: Z
]

# テトリミノの形状
# 1はブロックが存在するセルを示す。各要素は4x4グリッド内の形状。
# I, J, L, O, S, T, Z の順に対応。
TETROMINOS = [
    # 1. I (Cyan)
    [
        [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]], # 0度
        [[0, 0, 1, 0], [0, 0, 1, 0], [0, 0, 1, 0], [0, 0, 1, 0]], # 90度
        [[0, 0, 0, 0], [0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0]], # 180度
        [[0, 1, 0, 0], [0, 1, 0, 0], [0, 1, 0, 0], [0, 1, 0, 0]]  # 270度
    ],
    # 2. J (Blue)
    [
        [[2, 0, 0], [2, 2, 2], [0, 0, 0]],
        [[0, 2, 2], [0, 2, 0], [0, 2, 0]],
        [[0, 0, 0], [2, 2, 2], [0, 0, 2]],
        [[0, 2, 0], [0, 2, 0], [2, 2, 0]]
    ],
    # 3. L (Orange)
    [
        [[0, 0, 3], [3, 3, 3], [0, 0, 0]],
        [[0, 3, 0], [0, 3, 0], [0, 3, 3]],
        [[0, 0, 0], [3, 3, 3], [3, 0, 0]],
        [[3, 3, 0], [0, 3, 0], [0, 3, 0]]
    ],
    # 4. O (Yellow)
    [
        [[4, 4], [4, 4]],
    ],
    # 5. S (Green)
    [
        [[0, 5, 5], [5, 5, 0], [0, 0, 0]],
        [[0, 5, 0], [0, 5, 5], [0, 0, 5]],
        [[0, 0, 0], [0, 5, 5], [5, 5, 0]],
        [[5, 0, 0], [5, 5, 0], [0, 5, 0]]
    ],
    # 6. T (Purple)
    [
        [[0, 6, 0], [6, 6, 6], [0, 0, 0]],
        [[0, 6, 0], [0, 6, 6], [0, 6, 0]],
        [[0, 0, 0], [6, 6, 6], [0, 6, 0]],
        [[0, 6, 0], [6, 6, 0], [0, 6, 0]]
    ],
    # 7. Z (Red)
    [
        [[7, 7, 0], [0, 7, 7], [0, 0, 0]],
        [[0, 0, 7], [0, 7, 7], [0, 7, 0]],
        [[0, 0, 0], [7, 7, 0], [0, 7, 7]],
        [[0, 7, 0], [7, 7, 0], [7, 0, 0]]
    ]
]


# --- 2. TetrisGame クラス ---

class TetrisGame:
    def __init__(self, master):
        self.master = master
        master.title("Tkinter Tetris")
        self.running = True

        # キャンバスとゲームボードの初期化
        self.canvas = tk.Canvas(master, 
                                width=BOARD_WIDTH * CELL_SIZE, 
                                height=BOARD_HEIGHT * CELL_SIZE, 
                                bg="black")
        self.canvas.pack()

        # ゲームボードの状態 (0:空, 1-7:固定されたブロックの色インデックス)
        self.board = [[0] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)]
        self.score = 0
        self.score_label = tk.Label(master, text=f"Score: {self.score}", font=("Arial", 16))
        self.score_label.pack()

        # 現在のテトリミノの状態
        self.current_shape_index = 0
        self.current_rotation = 0
        self.current_x = 0
        self.current_y = 0

        # キーバインドの設定
        master.bind('<Left>', lambda event: self.move_piece(-1, 0))
        master.bind('<Right>', lambda event: self.move_piece(1, 0))
        master.bind('<Down>', lambda event: self.move_piece(0, 1))
        master.bind('<Up>', lambda event: self.rotate_piece())

        self.new_piece()
        self.game_loop()

    def get_current_shape(self):
        """現在のテトリミノの形状（2次元リスト）を返す"""
        # Oミノは回転パターンが1つしかないため、modでインデックス調整
        shape_patterns = TETROMINOS[self.current_shape_index]
        return shape_patterns[self.current_rotation % len(shape_patterns)]

    def new_piece(self):
        """新しいテトリミノを生成し、初期位置に配置する"""
        self.current_shape_index = random.randrange(len(TETROMINOS))
        shape = self.get_current_shape()
        shape_size = len(shape)
        
        # 初期位置 (上部中央)
        self.current_x = BOARD_WIDTH // 2 - shape_size // 2
        self.current_y = 0
        self.current_rotation = 0
        
        # 設置時に衝突したらゲームオーバー
        if self.check_collision(0, 0, self.get_current_shape()):
            self.running = False
            self.game_over()


    def check_collision(self, dx, dy, shape):
        """
        指定された移動量(dx, dy)でテトリミノが衝突するかを判定する
        (壁、床、固定されたブロック)
        """
        for r in range(len(shape)):
            for c in range(len(shape[0])):
                if shape[r][c] != 0:
                    # 移動後のセル座標
                    new_x = self.current_x + c + dx
                    new_y = self.current_y + r + dy

                    # 1. 境界（壁と床）との衝突
                    if new_x < 0 or new_x >= BOARD_WIDTH or new_y >= BOARD_HEIGHT:
                        return True
                    
                    # 2. ボード上部の見えない部分（天井）との衝突（Y座標が負の場合）
                    if new_y < 0:
                        continue # 天井は無視して良い（固定時のみ問題）

                    # 3. 固定されたブロックとの衝突
                    if self.board[new_y][new_x] != 0:
                        return True
                        
        return False

    def move_piece(self, dx, dy):
        """テトリミノを移動させる"""
        if not self.running:
            return

        if not self.check_collision(dx, dy, self.get_current_shape()):
            self.current_x += dx
            self.current_y += dy
            self.draw_board() # 移動したら再描画
        elif dy == 1:
            # 下に移動できず、dy=1（落下）なら固定する
            self.freeze_piece()

    def rotate_piece(self):
        """テトリミノを回転させる"""
        if not self.running:
            return

        original_rotation = self.current_rotation
        self.current_rotation = (self.current_rotation + 1) % len(TETROMINOS[self.current_shape_index])
        new_shape = self.get_current_shape()

        if self.check_collision(0, 0, new_shape):
            # 衝突した場合は、回転を元に戻す（キックシステムは省略）
            self.current_rotation = original_rotation
        else:
            self.draw_board() # 回転成功したら再描画
    
    def freeze_piece(self):
        """テトリミノをボードに固定し、ライン消去をチェックする"""
        shape = self.get_current_shape()
        color_index = shape[0][0] # 形状リストの最初の非ゼロ値（色インデックス）
        
        for r in range(len(shape)):
            for c in range(len(shape[0])):
                if shape[r][c] != 0:
                    board_y = self.current_y + r
                    board_x = self.current_x + c
                    
                    # ボードの境界外 (Yが負の領域) のブロックは無視
                    if 0 <= board_y < BOARD_HEIGHT:
                        self.board[board_y][board_x] = shape[r][c]

        self.clear_lines()
        self.new_piece() # 新しいテトリミノを生成

    def clear_lines(self):
        """ラインが揃っているかチェックし、消去する"""
        lines_cleared = 0
        new_board = []
        
        # 下から上に走査
        for row in self.board[::-1]: 
            if 0 not in row:
                # ラインが揃っている (0がない) -> 消去
                lines_cleared += 1
            else:
                # ラインが揃っていない -> 新しいボードに追加
                new_board.insert(0, row) 

        # 消去された行数分、上部に空行を追加
        for _ in range(lines_cleared):
            new_board.insert(0, [0] * BOARD_WIDTH)

        self.board = new_board

        if lines_cleared > 0:
            # スコアリング
            if lines_cleared == 1: score_gain = 100
            elif lines_cleared == 2: score_gain = 300
            elif lines_cleared == 3: score_gain = 500
            elif lines_cleared == 4: score_gain = 800 # Tetris!
            else: score_gain = 0
            
            self.score += score_gain
            self.score_label.config(text=f"Score: {self.score}")


    def draw_cell(self, x, y, color_index):
        """指定されたセル座標に色付きの四角を描画する"""
        if color_index == 0:
            return # 空のセルは描画しない

        x1 = x * CELL_SIZE
        y1 = y * CELL_SIZE
        x2 = x1 + CELL_SIZE
        y2 = y1 + CELL_SIZE
        
        self.canvas.create_rectangle(x1, y1, x2, y2, 
                                     fill=COLORS[color_index], 
                                     outline="black", 
                                     width=1)


    def draw_board(self):
        """ボード全体と現在のテトリミノを描画する"""
        self.canvas.delete("all")

        # 1. 固定されたボードのブロックを描画
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                color_index = self.board[y][x]
                self.draw_cell(x, y, color_index)
        
        # 2. 現在操作中のテトリミノを描画
        shape = self.get_current_shape()
        color_index = shape[0][0]
        
        for r in range(len(shape)):
            for c in range(len(shape[0])):
                if shape[r][c] != 0:
                    board_x = self.current_x + c
                    board_y = self.current_y + r
                    
                    # ボード内にあるブロックのみ描画
                    if 0 <= board_x < BOARD_WIDTH and 0 <= board_y < BOARD_HEIGHT:
                        self.draw_cell(board_x, board_y, shape[r][c])


    def game_loop(self):
        """ゲームのメインループ（自動落下処理）"""
        if self.running:
            # 1マス落下させる
            self.move_piece(0, 1) 
            
            # 再描画
            self.draw_board()
            
            # 指定時間後に再度実行
            self.master.after(FALL_SPEED_MS, self.game_loop)
        else:
            self.game_over()

    def game_over(self):
        """ゲームオーバー処理"""
        # 落下処理を停止
        self.running = False
        
        # キャンバスにメッセージを表示
        self.canvas.create_text(BOARD_WIDTH * CELL_SIZE / 2, 
                                BOARD_HEIGHT * CELL_SIZE / 2, 
                                text="GAME OVER", 
                                fill="white", 
                                font=("Arial", 30))
        tk.messagebox.showinfo("ゲームオーバー", f"スコア: {self.score}\nもう一度プレイしますか？")
        # （TODO: リスタート処理などを追加可能）


# --- 3. メインの実行部分 ---

if __name__ == "__main__":
    root = tk.Tk()
    game = TetrisGame(root)
    root.mainloop()
