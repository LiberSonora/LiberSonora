import asyncio
import subprocess
import sys
import os

async def read_output(stream, prefix):
    while True:
        line = await stream.readline()
        if not line:
            break
        print(f"{prefix}: {line.decode().strip()}")

async def run_scripts():
    # 运行 python server.py
    process1 = await asyncio.create_subprocess_exec(
        'python',
        'server.py',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # 运行 streamlit
    process2 = await asyncio.create_subprocess_exec(
        'python',
        '-m',
        'streamlit',
        'run',
        'ui.py',
        '--server.port=8501',
        '--server.address=0.0.0.0',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # 创建读取输出的任务
    tasks = [
        asyncio.create_task(read_output(process1.stdout, "Server")),
        asyncio.create_task(read_output(process1.stderr, "Server Error")),
        asyncio.create_task(read_output(process2.stdout, "Streamlit")),
        asyncio.create_task(read_output(process2.stderr, "Streamlit Error"))
    ]
    
    # 等待所有任务完成
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    # 检查是否在Docker环境中
    if os.path.exists('/.dockerenv'):
        print("Running in Docker container")
    
    try:
        asyncio.run(run_scripts())
    except KeyboardInterrupt:
        print("Shutting down services...")
        sys.exit(0)
