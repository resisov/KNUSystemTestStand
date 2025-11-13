import pyfiglet

def print_colored_ascii_art(text, highlight):
    # 폰트 설정
    font_style = 'slant'
    
    # ASCII 아트로 전체 텍스트 변환
    ascii_art = pyfiglet.figlet_format(text, font=font_style)

    # 색상 코드 설정
    red_color = '\033[91m'  # 빨간색
    blue_color = '\033[91m' # 파란색
    reset_color = '\033[0m' # 색상 리셋
    
    # 강조할 텍스트를 색상 코드로 둘러싸기
    colored_art = ''
    lines = ascii_art.split('\n')
    for line in lines:
        if highlight in line:
            start_index = line.index(highlight)
            end_index = start_index + len(highlight)
            # 강조할 텍스트 전후로 색상 적용
            colored_line = f"{red_color}{line[:start_index]}{blue_color}{line[start_index:end_index]}{red_color}{line[end_index:]}{reset_color}"
            colored_art += colored_line + '\n'
        else:
            colored_art += f"{blue_color}{line}{reset_color}\n"

    print(colored_art)

# 원하는 텍스트와 강조할 단어 입력
print_colored_ascii_art("KNU\n DAQSystem", "KNU")