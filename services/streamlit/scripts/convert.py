import os
import json
import time
import argparse
import sys
import asyncio
import traceback
from io import StringIO
app_path = os.path.join(os.path.dirname(__file__), '../')
sys.path.append(app_path)
from packages.process import process_single_audio

class LogManager:
    """日志管理器，负责日志的捕获和写入"""
    def __init__(self, output_dir: str):
        self.log_buffer = StringIO()
        self.log_file = os.path.join(output_dir, 'libersonora.log')
        self.output_dir = output_dir
        self.has_error = False

    def write(self, message: str):
        """写入日志并实时保存到文件"""
        self.log_buffer.write(message)
        print(message)  # 同时输出到控制台
        
        # 实时写入日志文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(message)

    def get_logs(self) -> str:
        """获取捕获的日志"""
        return self.log_buffer.getvalue()

    def clean_up(self):
        """清理日志文件，如果任务成功则删除日志文件"""
        if not self.has_error and os.path.exists(self.log_file):
            os.remove(self.log_file)

async def convert_audio_files(config_path: str, input_dir: str, output_dir: str, audio_files_path: str = None):
    """转换音频文件
    
    参数:
        config_path: 配置文件路径
        input_dir: 输入目录路径
        output_dir: 输出目录路径
        audio_files_path: 音频文件列表JSON文件路径
    """
    # 初始化日志管理器
    log_manager = LogManager(output_dir)
    
    try:
        # 读取配置文件
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 创建输出目录（如果不存在）
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取音频文件列表
        if audio_files_path:
            # 如果传入了音频文件列表路径，则读取该文件
            with open(audio_files_path, 'r', encoding='utf-8') as f:
                audio_files = json.load(f)
        else:
            # 否则扫描输入目录获取音频文件
            audio_files = []
            for root, _, files in os.walk(input_dir):
                for file in files:
                    if file.endswith(('.mp3', '.wav', '.pcm')):
                        audio_files.append(os.path.join(root, file))
        
        if not audio_files:
            log_manager.write("Error: No audio files found\n")
            return
        
        log_manager.write(f"Found {len(audio_files)} audio files to process\n")
        
        start_time = time.time()
        success_count = 0
        
        # 顺序处理每个文件
        for index, file_path in enumerate(audio_files):
            try:
                file_start_time = time.time()  # 记录单个文件开始处理时间
                
                with open(file_path, 'rb') as f:
                    # 创建类似Streamlit上传文件的对象
                    file_obj = type('StreamlitUploadedFile', (), {
                        'name': os.path.basename(file_path),
                        'body': f.read()
                    })()
                    
                    # 计算相对路径
                    relative_path = os.path.relpath(os.path.dirname(file_path), input_dir)
                    # 创建对应的输出目录
                    target_dir = os.path.join(output_dir, relative_path)
                    os.makedirs(target_dir, exist_ok=True)
                    
                    # 处理单个音频文件
                    audio_path = await process_single_audio(
                        index=index,
                        audio_file=file_obj,
                        config=config,
                        temp_dir=target_dir
                    )
                    
                    if audio_path:
                        success_count += 1
                        file_end_time = time.time()  # 记录单个文件处理结束时间
                        file_processing_time = file_end_time - file_start_time  # 计算单个文件处理时间
                        log_manager.write(f"Successfully processed: {os.path.basename(file_path)} (Time: {file_processing_time:.2f}s)\n")
                        
            except Exception as e:
                file_end_time = time.time()  # 记录单个文件处理结束时间
                file_processing_time = file_end_time - file_start_time  # 计算单个文件处理时间
                error_msg = f"Error processing file {os.path.basename(file_path)}: {str(e)} (Time: {file_processing_time:.2f}s)\n"
                log_manager.write(error_msg)
                log_manager.has_error = True
                continue
        
        end_time = time.time()
        processing_time = end_time - start_time
        log_manager.write(f"Processing completed! Successfully processed {success_count}/{len(audio_files)} files\n")
        log_manager.write(f"Total processing time: {processing_time:.2f} seconds\n")
        log_manager.write(f"Results saved to: {output_dir}\n")
        
    except Exception as e:
        error_msg = f"Error during processing: {str(e)}\n"
        traceback_msg = traceback.format_exc()
        log_manager.write(error_msg)
        log_manager.write(traceback_msg)
        log_manager.has_error = True
        raise e
    finally:
        # 清理日志文件
        log_manager.clean_up()

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Convert audio files")
    parser.add_argument('--config', required=True, help="Path to config JSON file")
    parser.add_argument('--input-dir', required=True, help="Input directory containing audio files")
    parser.add_argument('--output-dir', required=True, help="Output directory for processed files")
    parser.add_argument('--audio-files', help="Path to JSON file containing list of audio files to process")
    
    args = parser.parse_args()
    
    # 运行转换任务
    asyncio.run(convert_audio_files(args.config, args.input_dir, args.output_dir, args.audio_files))

if __name__ == "__main__":
    main()
