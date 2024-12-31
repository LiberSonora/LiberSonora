import os
import json
import time
import argparse
from packages.process import process_single_audio

async def convert_audio_files(config_path: str, input_dir: str, output_dir: str):
    """转换音频文件
    
    参数:
        config_path: 配置文件路径
        input_dir: 输入目录路径
        output_dir: 输出目录路径
    """
    try:
        # 读取配置文件
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 创建输出目录（如果不存在）
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取输入目录下的所有音频文件
        audio_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) 
                      if f.endswith(('.mp3', '.wav', '.pcm'))]
        
        if not audio_files:
            print("Error: No audio files found in input directory")
            return
        
        print(f"Found {len(audio_files)} audio files to process")
        
        start_time = time.time()
        success_count = 0
        
        # 顺序处理每个文件
        for index, file_path in enumerate(audio_files):
            try:
                with open(file_path, 'rb') as f:
                    # 创建类似Streamlit上传文件的对象
                    file_obj = type('StreamlitUploadedFile', (), {
                        'name': os.path.basename(file_path),
                        'body': f.read()
                    })()
                    
                    # 处理单个音频文件
                    audio_path = await process_single_audio(
                        index=index,
                        audio_file=file_obj,
                        config=config,
                        temp_dir=output_dir
                    )
                    
                    if audio_path:
                        success_count += 1
                        print(f"Successfully processed: {os.path.basename(file_path)}")
                        
            except Exception as e:
                print(f"Error processing file {os.path.basename(file_path)}: {str(e)}")
                raise e
        
        end_time = time.time()
        processing_time = end_time - start_time
        print(f"Processing completed! Successfully processed {success_count}/{len(audio_files)} files")
        print(f"Total processing time: {processing_time:.2f} seconds")
        print(f"Results saved to: {output_dir}")
        
    except Exception as e:
        print(f"Error during processing: {str(e)}")

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Convert audio files")
    parser.add_argument('--config', required=True, help="Path to config JSON file")
    parser.add_argument('--input-dir', required=True, help="Input directory containing audio files")
    parser.add_argument('--output-dir', required=True, help="Output directory for processed files")
    
    args = parser.parse_args()
    
    # 运行转换任务
    asyncio.run(convert_audio_files(args.config, args.input_dir, args.output_dir))

if __name__ == "__main__":
    main()
