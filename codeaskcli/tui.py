"""
终端用户界面(TUI)模块
实现进度条和其他终端UI元素
"""
from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.progress import (
    Progress, 
    TextColumn, 
    BarColumn, 
    TaskProgressColumn, 
    TimeElapsedColumn, 
    TimeRemainingColumn,
    SpinnerColumn
)
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout


class AnalysisTUI:
    """分析任务终端用户界面"""
    
    def __init__(self):
        self.console = Console()
        self.task_progresses: Dict[str, int] = {}  # 保存每个文件任务的ID和进度
        self.total_progress_id = None
        self.summary_progress_id = None
        self.progress = None
        self.live = None
    
    def setup_progress_display(self, total_files: int):
        """设置进度显示"""
        self.progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            "[",
            TimeElapsedColumn(),
            "|",
            TimeRemainingColumn(),
            "]",
            expand=True,
            console=self.console
        )
        
        # 添加总进度任务
        self.total_progress_id = self.progress.add_task(
            "[bold green]总进度", 
            total=100,  # 总进度以百分比显示
            completed=0
        )
        
        # 创建进度显示的Live上下文
        self.live = Live(self.progress, refresh_per_second=10)
        self.live.start()
    
    def add_file_task(self, file_path: str) -> int:
        """
        为文件添加进度任务
        
        Args:
            file_path: 文件路径
            
        Returns:
            任务ID
        """
        if not self.progress:
            return -1
            
        task_id = self.progress.add_task(
            f"[cyan]分析 {file_path}", 
            total=100,  # 以百分比显示
            completed=0
        )
        self.task_progresses[file_path] = task_id
        return task_id
    
    def update_file_progress(self, file_path: str, status: str, progress: float = 100.0):
        """
        更新文件分析进度
        
        Args:
            file_path: 文件路径
            status: 状态描述
            progress: 完成百分比
        """
        if not self.progress or file_path not in self.task_progresses:
            return
            
        task_id = self.task_progresses[file_path]
        
        # 根据状态设置颜色
        if status == "success":
            status_prefix = "[green]✓"
        elif status == "error":
            status_prefix = "[red]✗"
        elif status == "retry":
            status_prefix = "[yellow]⟳"
        else:
            status_prefix = "[blue]⟳"
        
        # 更新任务描述和进度
        self.progress.update(
            task_id, 
            description=f"{status_prefix} {file_path} - {status}",
            completed=progress
        )
    
    def update_total_progress(self, completed: float):
        """
        更新总进度条
        
        Args:
            completed: 完成百分比，0-100
        """
        if not self.progress or self.total_progress_id is None:
            return
            
        self.progress.update(self.total_progress_id, completed=completed)
    
    def start_summary_generation(self):
        """开始生成总结的进度显示"""
        if not self.progress:
            return
            
        self.summary_progress_id = self.progress.add_task(
            "[magenta]生成项目总结", 
            total=None,  # 不确定的总量，显示为循环进度条
            completed=0
        )
    
    def complete_summary_generation(self, success: bool = True):
        """完成总结生成的进度显示"""
        if not self.progress or self.summary_progress_id is None:
            return
            
        status_prefix = "[green]✓" if success else "[red]✗"
        self.progress.update(
            self.summary_progress_id,
            description=f"{status_prefix} 项目总结生成{'成功' if success else '失败'}",
            completed=100 if success else 0,
            total=100  # 设置总量，使进度条显示完成
        )
    
    def finish(self):
        """完成并关闭进度显示"""
        if self.live:
            self.live.stop()
            
        self.console.print("[bold green]分析完成!")