"""
代码分析器核心功能
"""
import os
import json
import time
import concurrent.futures
from typing import List, Dict, Any, Optional, Union, Set

from codeaskcli.api import BaseAIClient, AIApiClient
from codeaskcli.file_utils import get_file_hash, read_file, find_matching_files, save_analysis_results
from codeaskcli.tui import AnalysisTUI


class CodeAnalyzer:
    """
    代码分析器，实现与CodeAsk相同的分析逻辑，但不依赖于GUI
    """
    def __init__(
        self, 
        api_client: Union[BaseAIClient, AIApiClient],
        concurrency: int = 1
    ):
        self.api_client = api_client
        self.concurrency = concurrency

    def analyze_single_file(self, file_path: str, prompt: str, folder_path: str, 
                          tui: Optional[AnalysisTUI] = None) -> Dict[str, Any]:
        """分析单个文件，生成分析结果"""
        max_retries = 3
        retry_count = 0
        last_error = None
        relative_path = os.path.relpath(file_path, folder_path)
        
        # 更新文件分析开始状态
        if tui:
            tui.update_file_progress(relative_path, "开始分析", 5)
        
        while retry_count < max_retries:
            try:
                # 更新文件读取进度
                if tui:
                    tui.update_file_progress(relative_path, "读取文件", 10)
                
                content = read_file(file_path)
                file_hash = get_file_hash(file_path)
                
                # 更新API请求状态
                if tui:
                    tui.update_file_progress(relative_path, "发送请求", 30)
                
                # 调用API进行分析
                messages = [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"File: {relative_path}\n\nCode:\n{content}"}
                ]
                
                response = self.api_client.chat_completion(messages)
                
                # 更新响应处理状态
                if tui:
                    tui.update_file_progress(relative_path, "处理响应", 80)
                
                result = self.api_client.clean_response(response)
                
                # 更新完成状态
                if tui:
                    tui.update_file_progress(relative_path, "success", 100)
                
                return {
                    "filename": relative_path,
                    "content": result,
                    "fileHash": file_hash,
                    "status": "success"
                }
            except Exception as e:
                last_error = e
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count  # 指数退避: 2, 4, 8秒
                    # 更新重试状态
                    if tui:
                        tui.update_file_progress(relative_path, f"retry-{retry_count}", 20 * retry_count)
                    else:
                        print(f"分析文件失败: {file_path}, 错误: {e}")
                        print(f"将在{wait_time}秒后进行第{retry_count+1}次重试...")
                    
                    time.sleep(wait_time)
                else:
                    error_msg = f"分析失败: {str(e)} (已重试{retry_count}次)"
                    # 更新错误状态
                    if tui:
                        tui.update_file_progress(relative_path, "error", 100)
                    else:
                        print(f"分析文件失败: {file_path}, 已重试{retry_count}次, 放弃分析。错误: {e}")
                    
                    return {
                        "filename": relative_path,
                        "content": error_msg,
                        "fileHash": file_hash,
                        "status": "error"
                    }
        
        # 这段代码不应该被执行到，添加以确保安全
        if tui:
            tui.update_file_progress(relative_path, "error", 100)
            
        return {
            "filename": relative_path,
            "content": f"分析失败: {str(last_error)}",
            "fileHash": get_file_hash(file_path),
            "status": "error"
        }

    def generate_summary(self, single_file_results: List[Dict[str, Any]], summary_prompt: str, 
                        tui: Optional[AnalysisTUI] = None) -> str:
        """基于单文件分析结果生成总结"""
        max_retries = 3
        retry_count = 0
        last_error = None
        
        # 开始生成总结的进度显示
        if tui:
            tui.start_summary_generation()
        
        # 提取每个文件的分析内容
        files_content = []
        for result in single_file_results:
            filename = result.get("filename", "未知文件")
            content = result.get("content", "")
            status = result.get("status", "unknown")
            
            if status == "success" and content:
                files_content.append(f"## 文件: {filename}\n\n{content}\n\n")
        
        # 将所有文件内容拼接为一个字符串
        all_content = "\n".join(files_content)
        
        while retry_count < max_retries:
            try:
                # 构造给AI的消息
                messages = [
                    {"role": "system", "content": summary_prompt},
                    {"role": "user", "content": f"以下是对项目中各个文件的分析结果，请根据这些分析生成整个项目的总结分析报告：\n\n{all_content}"}
                ]
                
                response = self.api_client.chat_completion(messages)
                result = self.api_client.clean_response(response)
                
                # 更新总结生成完成状态
                if tui:
                    tui.complete_summary_generation(True)
                
                return result
            except Exception as e:
                last_error = e
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count  # 指数退避: 2, 4, 8秒
                    print(f"生成总结失败: {e}")
                    print(f"将在{wait_time}秒后进行第{retry_count+1}次重试...")
                    time.sleep(wait_time)
                else:
                    error_msg = f"生成总结失败: {str(e)} (已重试{retry_count}次)"
                    # 更新总结生成失败状态
                    if tui:
                        tui.complete_summary_generation(False)
                    else:
                        print(f"生成总结失败, 已重试{retry_count}次, 放弃总结生成。错误: {e}")
                    
                    return error_msg
        
        # 这段代码不应该被执行到，添加以确保安全
        if tui:
            tui.complete_summary_generation(False)
        return f"生成总结失败: {str(last_error)}"

    def load_previous_analysis(self, output_file: str) -> Dict[str, Any]:
        """
        加载之前的分析结果
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            之前的分析结果，如果不存在则返回空字典
        """
        import json
        
        # 确定输出路径
        result_path = output_file
        if os.path.isdir(output_file):
            result_path = os.path.join(output_file, '.codeaskdata')
            
        # 加载已有的分析结果    
        if os.path.exists(result_path):
            try:
                with open(result_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 检查是否包含单文件分析结果
                    if "singleFileResults" in data:
                        return data
                    else:
                        # 旧版格式兼容
                        return {}
            except Exception as e:
                print(f"加载之前的分析结果失败: {e}")
                return {}
        return {}
    
    def remove_analysis_file(self, base_dir: str, filename: str) -> None:
        """
        删除不存在文件的分析结果
        
        Args:
            base_dir: 分析结果所在基础目录
            filename: 相对于项目根目录的文件路径
        """
        try:
            # 构建分析文件路径
            analysis_file_path = os.path.join(base_dir, f"{filename}.md")
            if os.path.exists(analysis_file_path):
                os.remove(analysis_file_path)
                print(f"删除不存在文件的分析结果: {filename}.md")
        except Exception as e:
            print(f"删除分析文件失败: {filename}.md, 错误: {e}")

    def analyze_project(
        self, 
        folder_path: str, 
        file_patterns: List[str],
        single_page_prompt: str,
        summary_prompt: str,
        output_file: Optional[str] = None,
        incremental: bool = True,
        config_file: Optional[str] = None,
        config_hash: Optional[str] = None,
        use_tui: bool = True
    ) -> Dict[str, Any]:
        """
        分析整个项目，生成分析报告
        
        Args:
            folder_path: 项目文件夹路径
            file_patterns: 文件匹配模式
            single_page_prompt: 单页分析提示词
            summary_prompt: 总结分析提示词
            output_file: 输出文件路径
            incremental: 是否进行增量分析（仅分析变化的文件）
            config_file: 配置文件路径
            config_hash: 配置文件的哈希值
            use_tui: 是否使用TUI界面
            
        Returns:
            分析结果字典
        """
        start_time = time.time()
        
        # 初始化TUI显示
        tui = None
        if use_tui:
            try:
                tui = AnalysisTUI()
            except Exception as e:
                print(f"初始化TUI失败: {e}，将使用普通终端输出")
                use_tui = False
        
        # 收集匹配的文件
        all_files = find_matching_files(folder_path, file_patterns)
        if tui:
            tui.console.print(f"[blue]找到 {len(all_files)} 个文件匹配模式 {file_patterns}")
        else:
            print(f"找到 {len(all_files)} 个文件匹配模式 {file_patterns}")
        
        # 获取所有匹配文件的相对路径
        all_relative_paths = set(os.path.relpath(file_path, folder_path) for file_path in all_files)
        
        # 如果启用增量分析，加载之前的分析结果
        previous_analysis = {}
        previous_file_hashes = {}
        previous_single_file_results = []
        previous_config_hash = None
        removed_files = []
        
        if incremental and output_file:
            previous_analysis = self.load_previous_analysis(output_file)
            
            # 从之前的分析中提取文件哈希信息
            if "singleFileResults" in previous_analysis:
                previous_single_file_results = previous_analysis.get("singleFileResults", [])
                for result in previous_single_file_results:
                    filename = result.get("filename")
                    filehash = result.get("fileHash")
                    if filename and filehash:
                        previous_file_hashes[filename] = filehash
                        
                        # 检查文件是否不再存在
                        if filename not in all_relative_paths:
                            removed_files.append(filename)
                
                # 获取之前保存的配置文件哈希值
                previous_config_hash = previous_analysis.get("globalAnalysis", {}).get("results", {}).get(
                    "cli_analysis", {}).get("configHash")
                
                if tui:
                    tui.console.print(f"[green]已加载之前的分析结果（{len(previous_file_hashes)}个文件）")
                    if removed_files:
                        tui.console.print(f"[yellow]检测到 {len(removed_files)} 个已分析的文件不再存在")
                else:
                    print(f"已加载之前的分析结果（{len(previous_file_hashes)}个文件）")
                    if removed_files:
                        print(f"检测到 {len(removed_files)} 个已分析的文件不再存在")
        
        # 检查配置文件是否发生变化
        config_changed = False
        if config_hash and previous_config_hash and config_hash != previous_config_hash:
            config_changed = True
            if tui:
                tui.console.print("[yellow]检测到配置文件已更改，将执行完整分析")
            else:
                print(f"检测到配置文件已更改，将执行完整分析")
            incremental = False
        
        # 需要重新分析的文件列表
        files_to_analyze = []
        existing_results = []
        
        # 确定哪些文件需要重新分析
        if incremental and previous_file_hashes and not config_changed:
            for file_path in all_files:
                relative_path = os.path.relpath(file_path, folder_path)
                current_hash = get_file_hash(file_path)
                
                # 如果文件是新的或已更改，则需要分析
                if relative_path not in previous_file_hashes or previous_file_hashes[relative_path] != current_hash:
                    files_to_analyze.append(file_path)
                else:
                    # 文件未更改，使用之前的结果
                    for result in previous_single_file_results:
                        if result.get("filename") == relative_path:
                            existing_results.append(result)
                            break
            
            # 删除已不存在文件的分析结果
            if removed_files and output_file:
                base_dir = output_file
                if os.path.isfile(output_file):
                    base_dir = os.path.dirname(output_file)
                
                for filename in removed_files:
                    self.remove_analysis_file(base_dir, filename)
            
            if tui:
                tui.console.print(f"[green]增量分析: 需要重新分析 {len(files_to_analyze)} 个文件，保留 {len(existing_results)} 个未更改文件的分析结果")
            else:
                print(f"增量分析: 需要重新分析 {len(files_to_analyze)} 个文件，保留 {len(existing_results)} 个未更改文件的分析结果")
        else:
            # 不是增量分析、没有之前的结果或配置文件已更改，分析所有文件
            files_to_analyze = all_files
            
            # 如果是从增量分析切换到完整分析，删除不存在的文件结果
            if removed_files and output_file:
                base_dir = output_file
                if os.path.isfile(output_file):
                    base_dir = os.path.dirname(output_file)
                
                for filename in removed_files:
                    self.remove_analysis_file(base_dir, filename)
        
        # 设置TUI进度显示
        if tui and files_to_analyze:
            tui.setup_progress_display(len(files_to_analyze))
            
            # 为每个文件创建进度任务
            for file_path in files_to_analyze:
                relative_path = os.path.relpath(file_path, folder_path)
                tui.add_file_task(relative_path)
        
        # 分析需要更新的文件
        new_single_file_results = []
        
        if files_to_analyze:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrency) as executor:
                future_to_file = {
                    executor.submit(
                        self.analyze_single_file, 
                        file_path, 
                        single_page_prompt, 
                        folder_path,
                        tui
                    ): file_path
                    for file_path in files_to_analyze
                }
                
                total_files = len(files_to_analyze)
                processed_files = 0
                
                for future in concurrent.futures.as_completed(future_to_file):
                    file_path = future_to_file[future]
                    relative_path = os.path.relpath(file_path, folder_path)
                    try:
                        result = future.result()
                        new_single_file_results.append(result)
                    except Exception as e:
                        if tui:
                            tui.console.print(f"[red]处理文件 {relative_path} 时发生错误: {e}")
                        else:
                            print(f"处理文件 {file_path} 时发生错误: {e}")
                            
                        new_single_file_results.append({
                            "filename": relative_path,
                            "content": f"处理失败: {str(e)}",
                            "fileHash": get_file_hash(file_path),
                            "status": "error"
                        })
                        
                        # 更新出错的文件状态
                        if tui:
                            tui.update_file_progress(relative_path, "error", 100)
                    
                    processed_files += 1
                    progress = (processed_files / total_files) * 90  # 单文件分析占总进度的90%
                    
                    # 更新总进度
                    if tui:
                        tui.update_total_progress(progress)
                    else:
                        print(f"进度: {progress:.1f}%, 正在分析文件... ({processed_files}/{total_files})")
        
        # 从结果中过滤掉已删除的文件
        filtered_existing_results = []
        if incremental and not config_changed:
            filtered_existing_results = [r for r in existing_results if r.get("filename") not in removed_files]
        
        # 合并新旧分析结果
        single_file_results = filtered_existing_results + new_single_file_results
        
        # 重新生成总结
        if tui:
            tui.console.print("\n[bold magenta]开始生成总结...")
        else:
            print("开始生成总结...")
            
        summary = self.generate_summary(single_file_results, summary_prompt, tui)
        
        # 更新总进度到100%
        if tui:
            tui.update_total_progress(100)
        
        # 构建结果
        result = {
            "globalAnalysisName": "CLI Analysis",
            "singlePagePrompt": single_page_prompt,
            "summaryPrompt": summary_prompt,
            "summary": summary,
            "timestamp": int(time.time()),
            "configHash": config_hash,  # 保存配置文件哈希值
            "configFile": config_file,  # 保存配置文件路径
            "single_file_results": single_file_results  # 额外添加单文件结果方便后续处理
        }
        
        # 输出结果
        if output_file:
            save_analysis_results(output_file, result, summary)
            
        end_time = time.time()
        
        if tui:
            tui.finish()
            tui.console.print(f"[bold green]分析完成，用时: {end_time - start_time:.2f} 秒")
        else:
            print(f"分析完成，用时: {end_time - start_time:.2f} 秒")
        
        return result