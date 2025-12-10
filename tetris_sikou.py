import tkinter as tk
import random

# --- 設定定数 ---
COLS = 10          # 横のブロック数
ROWS = 20          # 縦のブロック数
BLOCK_SIZE = 30    # ブロックのピクセルサイズ
SPEED = 500        # 落下速度 (ミリ秒)

# テトリミノの形状定義 (中心からの相対座標)
SHAPES = [
    [(-1, 0), (0, 0), (1, 0), (2, 0)],   # I (水色)
    [(-1, -1), (-1, 0), (0, 0), (1, 0)], # J (青)
    [(1, -1), (-1, 0), (0, 0), (1, 0)],  # L (オレンジ)
    [(0, 0), (1, 0), (0, 1), (1, 1)],    # O (黄色)
    [(-1, 0), (0, 0), (0, -1), (1, -1)], # S (緑)
    [(-1, 0), (0, 0), (1, 0), (0, -1)],  # T (紫)
    [(-1, -1), (0, -1), (0, 0), (1, 0)], # Z (赤)
]

# テトリミノの色
COLORS = [
    "cyan", "blue", "orange", "yellow", "green", "purple", "red"
]

class TetrisGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Tetris - Python & Tkinter")
        
        # キャンバスの作成
        self.canvas_width = COLS * BLOCK_SIZE
        self.canvas_height = ROWS * BLOCK_SIZE
        self.canvas = tk.Canvas(root, width=self.canvas_width, height=self.canvas_height, bg="black")
        self.canvas.pack()

        # スコア表示
        self.score_label = tk.Label(root, text="Score: 0", font=("Arial", 14))
        self.score_label.pack()

        # ゲーム変数の初期化
        self.board = [[0 for _ in range(COLS)] for _ in range(ROWS)] # 0は空、それ以外は色ID
        self.score = 0
        self.game_over = False
        self.current_piece = None
        self.current_color = ""
        self.piece_x = 0
        self.piece_y = 0

        # キー操作のバインド
        self.root.bind("<Left>", lambda e: self.move(-1, 0))
        self.root.bind("<Right>", lambda e: self.move(1, 0))
        self.root.bind("<Down>", lambda e: self.move(0, 1))
        self.root.bind("<Up>", lambda e: self.rotate())
        
        # ゲーム開始
        self.spawn_piece()
        self.update_clock()

    def spawn_piece(self):
        """新しいピースを生成する"""
        shape_idx = random.randint(0, len(SHAPES) - 1)
        self.current_piece = SHAPES[shape_idx]
        self.current_color = COLORS[shape_idx]
        self.piece_x = COLS // 2
        self.piece_y = 0

        # 出現直後に衝突していたらゲームオーバー
        if self.check_collision(self.current_piece, self.piece_x, self.piece_y):
            self.game_over = True
            # ここでの描画は draw_board で消されてしまうため削除し、draw_board 側に移動しました

    def check_collision(self, shape, offset_x, offset_y):
        """衝突判定 (壁、床、他のブロック)"""
        for x, y in shape:
            new_x = x + offset_x
            new_y = y + offset_y
            
            # 壁と床の判定
            if new_x < 0 or new_x >= COLS or new_y >= ROWS:
                return True
            
            # 他のブロックとの衝突判定 (yが0以上の場合のみチェック)
            if new_y >= 0 and self.board[new_y][new_x] != 0:
                return True
        return False

    def move(self, dx, dy):
        """ピースを移動させる"""
        if self.game_over: return

        if not self.check_collision(self.current_piece, self.piece_x + dx, self.piece_y + dy):
            self.piece_x += dx
            self.piece_y += dy
            self.draw_board()
        elif dy > 0:
            # 下移動で衝突した場合は固定する
            self.lock_piece()

    def rotate(self):
        """ピースを回転させる"""
        if self.game_over: return
        
        # 回転後の座標を計算 (x, y) -> (-y, x)
        new_piece = [(-y, x) for x, y in self.current_piece]
        
        if not self.check_collision(new_piece, self.piece_x, self.piece_y):
            self.current_piece = new_piece
            self.draw_board()

    def lock_piece(self):
        """ピースを盤面に固定し、ライン消去判定を行う"""
        for x, y in self.current_piece:
            if self.piece_y + y >= 0:
                self.board[self.piece_y + y][self.piece_x + x] = self.current_color
        
        self.clear_lines()
        self.spawn_piece()
        self.draw_board()

    def clear_lines(self):
        """揃ったラインを消去する"""
        new_board = [row for row in self.board if 0 in row] # 空きがある行だけ残す
        lines_cleared = ROWS - len(new_board)
        
        if lines_cleared > 0:
            self.score += lines_cleared * 100
            self.score_label.config(text=f"Score: {self.score}")
            # 消えた分だけ上に空行を追加
            for _ in range(lines_cleared):
                new_board.insert(0, [0 for _ in range(COLS)])
            self.board = new_board

    def draw_board(self):
        """画面全体の描画"""
        self.canvas.delete("all")

        # 固定されたブロックの描画
        for y, row in enumerate(self.board):
            for x, color in enumerate(row):
                if color:
                    self.draw_block(x, y, color)

        # 現在落下中のブロックの描画
        if self.current_piece and not self.game_over:
            for x, y in self.current_piece:
                self.draw_block(self.piece_x + x, self.piece_y + y, self.current_color)
        
        # ゲームオーバー時の表示 (修正箇所: 最後に描画することで上書きを防ぐ)
        if self.game_over:
            self.canvas.create_text(
                self.canvas_width // 2, self.canvas_height // 2,
                text="GAME OVER", fill="white", font=("Arial", 24, "bold")
            )

    def draw_block(self, x, y, color):
        """1つのブロックを描画する"""
        x1 = x * BLOCK_SIZE
        y1 = y * BLOCK_SIZE
        x2 = x1 + BLOCK_SIZE
        y2 = y1 + BLOCK_SIZE
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="white")

    def update_clock(self):
        """ゲームループ (一定時間ごとに落下)"""
        if not self.game_over:
            self.move(0, 1)
            self.root.after(SPEED, self.update_clock)

if __name__ == "__main__":
    root = tk.Tk()
    game = TetrisGame(root)
    root.mainloop()
