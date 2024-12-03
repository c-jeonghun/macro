import tkinter as tk
import pyautogui
import threading
import time
import cv2
import numpy as np
import json

# 설정 파일 경로
CONFIG_FILE = 'area_config.json'

# 적대 영역 및 HP 영역 정보
red_zone_area = {"x": 0, "y": 0, "width": 40, "height": 20}
white_zone_area = {"x": 0, "y": 0, "width": 40, "height": 20}
hp_zone_area = {"x": 0, "y": 0, "width": 40, "height": 20}
monitoring = False
selected_key = 'f1'

# 추가: 8초 딜레이를 관리하기 위한 변수
last_action_time = 0

# 영역 설정 저장 함수
def save_area_config():
    area_config = {"red_zone_area": red_zone_area, "white_zone_area": white_zone_area, "hp_zone_area": hp_zone_area}
    with open(CONFIG_FILE, 'w') as config_file:
        json.dump(area_config, config_file)
    print("영역 설정이 저장되었습니다.")

# 영역 설정 불러오기 함수
def load_area_config():
    global red_zone_area, white_zone_area, hp_zone_area
    try:
        with open(CONFIG_FILE, 'r') as config_file:
            area_config = json.load(config_file)
            if "red_zone_area" in area_config:
                red_zone_area = area_config["red_zone_area"]
            if "white_zone_area" in area_config:
                white_zone_area = area_config["white_zone_area"]
            if "hp_zone_area" in area_config:
                hp_zone_area = area_config["hp_zone_area"]
            print("영역 설정이 로드되었습니다.")
    except (FileNotFoundError, json.JSONDecodeError):
        print("이전 영역 설정이 없습니다. 새로 설정하세요.")

# 영역을 드래그하여 선택하는 클래스
class DragSelectZone(tk.Toplevel):
    def __init__(self, parent, zone):
        super().__init__(parent)
        self.zone = zone
        self.geometry(f"{parent.winfo_screenwidth()}x{parent.winfo_screenheight()}+0+0")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes('-alpha', 0.3)
        self.config(bg='black')
        self.wm_attributes('-transparentcolor', 'black')

        # 투명한 캔버스 설정
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 마우스 이벤트 바인딩
        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_drag_end)

        self.start_x = 0
        self.start_y = 0
        self.rect = None

    def on_drag_start(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='blue', width=2)

    def on_drag_motion(self, event):
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_drag_end(self, event):
        end_x, end_y = (event.x, event.y)
        self.zone['x'] = min(self.start_x, end_x)
        self.zone['y'] = min(self.start_y, end_y)
        self.zone['width'] = abs(self.start_x - end_x)
        self.zone['height'] = abs(self.start_y - end_y)
        print(f"영역이 설정되었습니다: {self.zone}")
        self.destroy()

def show_zone_selector(zone_type):
    global red_zone_area, white_zone_area, hp_zone_area
    if zone_type == 'red_zone':
        zone_window = DragSelectZone(root, red_zone_area)
    elif zone_type == 'white_zone':
        zone_window = DragSelectZone(root, white_zone_area)
    elif zone_type == 'hp_zone':
        zone_window = DragSelectZone(root, hp_zone_area)
    root.wait_window(zone_window)

def save_and_hide_zone():
    save_area_config()
    print("영역 설정이 완료되었습니다.")

def start_monitoring():
    global monitoring
    if not monitoring:
        monitoring = True
        threading.Thread(target=monitor_red_zone).start()
        threading.Thread(target=monitor_hp_zone).start()

def stop_monitoring():
    global monitoring
    monitoring = False
    print("모니터링이 중지되었습니다.")

# 적대 영역 모니터링 함수
def monitor_red_zone():
    global monitoring, last_action_time
    while monitoring:
        current_time = time.time()
        action_performed = False  # 행동 수행 여부 확인 변수

        if current_time - last_action_time >= 8:
            if red_zone_enabled.get():
              screenshot_red = pyautogui.screenshot(region=(red_zone_area["x"], red_zone_area["y"], red_zone_area["width"], red_zone_area["height"]))
              image_red = cv2.cvtColor(np.array(screenshot_red), cv2.COLOR_RGB2BGR)

              hsv_image_red = cv2.cvtColor(image_red, cv2.COLOR_BGR2HSV)
              lower_red1 = np.array([0, 100, 100])
              upper_red1 = np.array([10, 255, 255])
              red_mask1 = cv2.inRange(hsv_image_red, lower_red1, upper_red1)

              lower_red2 = np.array([170, 100, 100])
              upper_red2 = np.array([180, 255, 255])
              red_mask2 = cv2.inRange(hsv_image_red, lower_red2, upper_red2)

              red_mask = cv2.bitwise_or(red_mask1, red_mask2)
              red_ratio = np.sum(red_mask > 0) / (red_zone_area["width"] * red_zone_area["height"])

              if red_ratio > 0.1:
                print(f"적대 발견(빨간색). 선택된 키 '{selected_key.upper()}'를 누릅니다.")
                pyautogui.press(selected_key)
                last_action_time = current_time

        # 흰색 탐지 (활성화 상태 확인)
            if white_zone_enabled.get():
              screenshot_white = pyautogui.screenshot(region=(white_zone_area["x"], white_zone_area["y"], white_zone_area["width"], white_zone_area["height"]))
              image_white = cv2.cvtColor(np.array(screenshot_white), cv2.COLOR_RGB2BGR)

              hsv_image_white = cv2.cvtColor(image_white, cv2.COLOR_BGR2HSV)
              lower_white = np.array([0, 0, 200])  # 흰색 HSV 범위 설정
              upper_white = np.array([180, 30, 255])
              white_mask = cv2.inRange(hsv_image_white, lower_white, upper_white)
              white_ratio = np.sum(white_mask > 0) / (white_zone_area["width"] * white_zone_area["height"])

              if white_ratio > 0.1:
                print(f"적대 발견(흰색). 선택된 키 '{selected_key.upper()}'를 누릅니다.")
                pyautogui.press(selected_key)
                last_action_time = current_time
        # 8초 이내에 행동 수행 안된 경우 추가 처리
        else:
            if red_zone_enabled.get():
              screenshot_red = pyautogui.screenshot(region=(red_zone_area["x"], red_zone_area["y"], red_zone_area["width"], red_zone_area["height"]))
              image_red = cv2.cvtColor(np.array(screenshot_red), cv2.COLOR_RGB2BGR)

              hsv_image_red = cv2.cvtColor(image_red, cv2.COLOR_BGR2HSV)
              lower_red1 = np.array([0, 100, 100])
              upper_red1 = np.array([10, 255, 255])
              red_mask1 = cv2.inRange(hsv_image_red, lower_red1, upper_red1)

              lower_red2 = np.array([170, 100, 100])
              upper_red2 = np.array([180, 255, 255])
              red_mask2 = cv2.inRange(hsv_image_red, lower_red2, upper_red2)

              red_mask = cv2.bitwise_or(red_mask1, red_mask2)
              red_ratio = np.sum(red_mask > 0) / (red_zone_area["width"] * red_zone_area["height"])

              if red_ratio > 0.1:
                print(f"적대 발견(빨간색). 선택된 키 '{selected_key.upper()}'를 누릅니다.")
                pyautogui.press(selected_key)
                last_action_time = current_time

        # 흰색 탐지 (활성화 상태 확인)
            if white_zone_enabled.get():
              screenshot_white = pyautogui.screenshot(region=(white_zone_area["x"], white_zone_area["y"], white_zone_area["width"], white_zone_area["height"]))
              image_white = cv2.cvtColor(np.array(screenshot_white), cv2.COLOR_RGB2BGR)

              hsv_image_white = cv2.cvtColor(image_white, cv2.COLOR_BGR2HSV)
              lower_white = np.array([0, 0, 200])  # 흰색 HSV 범위 설정
              upper_white = np.array([180, 30, 255])
              white_mask = cv2.inRange(hsv_image_white, lower_white, upper_white)
              white_ratio = np.sum(white_mask > 0) / (white_zone_area["width"] * white_zone_area["height"])

              if white_ratio > 0.1:
                print(f"적대 발견(흰색). 선택된 키 '{selected_key.upper()}'를 누릅니다.")
                pyautogui.press(selected_key)
                last_action_time = current_time

        time.sleep(1)


# HP 영역 모니터링 함수
def monitor_hp_zone():
    global monitoring, last_action_time
    while monitoring:
        current_time = time.time()
        if current_time - last_action_time >= 8:
            screenshot = pyautogui.screenshot(region=(hp_zone_area["x"], hp_zone_area["y"], hp_zone_area["width"], hp_zone_area["height"]))
            image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lower_red1 = np.array([0, 100, 100])
            upper_red1 = np.array([10, 255, 255])
            red_mask1 = cv2.inRange(hsv_image, lower_red1, upper_red1)

            lower_red2 = np.array([170, 100, 100])
            upper_red2 = np.array([180, 255, 255])
            red_mask2 = cv2.inRange(hsv_image, lower_red2, upper_red2)

            red_mask = cv2.bitwise_or(red_mask1, red_mask2)

            red_ratio = np.sum(red_mask > 0) / (hp_zone_area["width"] * hp_zone_area["height"])

            if red_ratio < 0.3:
                print(f"HP 영역에서 빨간색 비율이 30% 미만. 선택된 키 '{selected_key.upper()}'를 누릅니다.")
                pyautogui.press(selected_key)
                last_action_time = current_time

        time.sleep(1)

def update_selected_key(event=None):
    global selected_key
    selected_key = key_var.get()
    print(f"선택된 키: {selected_key}")

def create_ui():
    global root, key_var, red_zone_enabled, white_zone_enabled

    # 루트 윈도우 생성
    root = tk.Tk()
    root.title("Candy")
    root.geometry("250x300")

    # 루트 윈도우 생성 후 Tkinter 변수 초기화
    red_zone_enabled = tk.BooleanVar(value=True)  # 초기값 설정
    white_zone_enabled = tk.BooleanVar(value=True)  # 흰색 영역도 사용 여부

    # GUI 구성 요소들 추가 (예: 버튼, 체크박스 등)
    # 적대범위(상단) 버튼과 체크박스를 같은 프레임에 배치
    red_zone_frame = tk.Frame(root)
    zone_button = tk.Button(red_zone_frame, text="적대범위(상단)", command=lambda: show_zone_selector('red_zone'))
    zone_button.pack(side=tk.LEFT, padx=5)

    red_zone_checkbox = tk.Checkbutton(red_zone_frame, variable=red_zone_enabled)
    red_zone_checkbox.pack(side=tk.LEFT)
    red_zone_frame.pack(pady=5)

    # 적대범위(적대) 버튼과 체크박스를 같은 프레임에 배치
    white_zone_frame = tk.Frame(root)
    zone_button = tk.Button(white_zone_frame, text="적대범위(적대)", command=lambda: show_zone_selector('white_zone'))
    zone_button.pack(side=tk.LEFT, padx=5)

    white_zone_checkbox = tk.Checkbutton(white_zone_frame, variable=white_zone_enabled)
    white_zone_checkbox.pack(side=tk.LEFT)
    white_zone_frame.pack(pady=5)

    # 설정 완료 버튼
    save_button = tk.Button(root, text="설정완료", command=save_and_hide_zone)
    save_button.pack(pady=5)

    # 키 선택 (한 줄로 표시)
    key_var = tk.StringVar(value='f1')
    key_menu = tk.OptionMenu(root, key_var, 'f1', 'f2', 'f3', 'f4', 'f5', command=update_selected_key)
    key_menu.pack(pady=5)

    # 시작 및 중지 버튼
    start_button = tk.Button(root, text="시작", command=start_monitoring)
    start_button.pack(pady=5)
    stop_button = tk.Button(root, text="중지", command=stop_monitoring)
    stop_button.pack(pady=5)

    # 종료 버튼
    quit_button = tk.Button(root, text="종료", command=root.quit)
    quit_button.pack(pady=5)

    load_area_config()

    # 루프 실행
    root.mainloop()

if __name__ == "__main__":
    create_ui()
