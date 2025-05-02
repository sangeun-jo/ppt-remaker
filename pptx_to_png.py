import os
import sys
from pptx import Presentation
from PIL import Image
import comtypes.client
import time
import argparse

def convert_pptx_to_png(pptx_path, output_dir):
    # 출력 디렉토리가 없으면 생성
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # PowerPoint 애플리케이션 시작
    powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
    powerpoint.Visible = True
    
    try:
        # PPTX 파일 열기
        presentation = powerpoint.Presentations.Open(os.path.abspath(pptx_path))
        time.sleep(1)  # 파일이 완전히 열릴 때까지 대기
        
        # 파일명 추출 (확장자 제외)
        base_name = os.path.splitext(os.path.basename(pptx_path))[0]
        
        # 각 슬라이드를 PNG로 저장
        for i in range(1, presentation.Slides.Count + 1):
            slide = presentation.Slides.Item(i)
            
            # 임시 파일로 저장
            temp_path = os.path.abspath(os.path.join(output_dir, f"temp_{i}.png"))
            slide.Export(temp_path, "PNG")
            time.sleep(0.5)  # 파일이 저장될 때까지 대기
            
            # 이미지 크기 조정
            with Image.open(temp_path) as img:
                # 원본 비율 유지하면서 긴 쪽을 640으로 맞춤
                if img.width > img.height:
                    new_width = 640
                    new_height = int(img.height * (640 / img.width))
                else:
                    new_height = 640
                    new_width = int(img.width * (640 / img.height))
                
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 최종 파일 저장
                output_path = os.path.join(output_dir, f"{base_name}_slide_{i:03d}.png")
                resized_img.save(output_path, "PNG")
            
            # 임시 파일 삭제
            try:
                os.remove(temp_path)
            except:
                pass
            
            print(f"슬라이드 {i} 변환 완료")
        
        print(f"변환 완료: {pptx_path}")
        
    finally:
        # PowerPoint 종료
        try:
            presentation.Close()
            powerpoint.Quit()
        except:
            pass

def main():
    parser = argparse.ArgumentParser(description='PPTX 파일을 PNG 이미지로 변환합니다.')
    parser.add_argument('input_dir', help='PPTX 파일이 있는 디렉토리 경로')
    parser.add_argument('output_dir', help='PNG 파일을 저장할 디렉토리 경로')
    
    args = parser.parse_args()
    
    # 입력 디렉토리의 모든 PPTX 파일 처리
    for filename in os.listdir(args.input_dir):
        if filename.endswith('.pptx'):
            pptx_path = os.path.join(args.input_dir, filename)
            print(f"변환 중: {filename}")
            convert_pptx_to_png(pptx_path, args.output_dir)

if __name__ == "__main__":
    main() 