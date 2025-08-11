import subprocess
import tempfile
import os
import time
import signal
import logging
from typing import Dict, List, Tuple, Any

class CodeExecutor:
    """Secure code execution service for contest submissions"""
    
    def __init__(self):
        self.supported_languages = {
            'python': {
                'extension': '.py',
                'command': ['python3', '{filename}'],
                'timeout': 5
            },
            'java': {
                'extension': '.java',
                'command': ['javac', '{filename}', '&&', 'java', '{classname}'],
                'timeout': 10
            },
            'cpp': {
                'extension': '.cpp',
                'command': ['g++', '-o', '{output}', '{filename}', '&&', '{output}'],
                'timeout': 10
            },
            'c': {
                'extension': '.c',
                'command': ['gcc', '-o', '{output}', '{filename}', '&&', '{output}'],
                'timeout': 10
            }
        }
    
    def execute_code(self, code: str, language: str, input_data: str = "", 
                    time_limit: int = 5, memory_limit: int = 256) -> Dict[str, Any]:
        """
        Execute code with input and return results
        
        Args:
            code: The source code to execute
            language: Programming language (python, java, cpp, c)
            input_data: Input to provide to the program
            time_limit: Maximum execution time in seconds
            memory_limit: Maximum memory usage in MB
            
        Returns:
            Dictionary containing execution results
        """
        if language not in self.supported_languages:
            return {
                'success': False,
                'status': 'error',
                'output': '',
                'error': f'Unsupported language: {language}',
                'execution_time': 0.0,
                'memory_used': 0
            }
        
        lang_config = self.supported_languages[language]
        
        # Create temporary directory for execution
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                return self._execute_in_sandbox(code, language, input_data, 
                                              time_limit, memory_limit, temp_dir)
            except Exception as e:
                logging.error(f"Code execution error: {e}")
                return {
                    'success': False,
                    'status': 'error',
                    'output': '',
                    'error': str(e),
                    'execution_time': 0.0,
                    'memory_used': 0
                }
    
    def _execute_in_sandbox(self, code: str, language: str, input_data: str,
                           time_limit: int, memory_limit: int, temp_dir: str) -> Dict[str, Any]:
        """Execute code in a sandboxed environment"""
        lang_config = self.supported_languages[language]
        
        # Write code to file
        filename = f"solution{lang_config['extension']}"
        filepath = os.path.join(temp_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(code)
        
        # Prepare execution command
        if language == 'python':
            cmd = ['python3', filepath]
        elif language == 'java':
            # Extract class name from Java code
            classname = self._extract_java_classname(code)
            compile_cmd = ['javac', filepath]
            run_cmd = ['java', '-cp', temp_dir, classname]
            return self._execute_java(compile_cmd, run_cmd, input_data, time_limit)
        elif language in ['cpp', 'c']:
            output_file = os.path.join(temp_dir, 'solution')
            compiler = 'g++' if language == 'cpp' else 'gcc'
            compile_cmd = [compiler, '-o', output_file, filepath]
            run_cmd = [output_file]
            return self._execute_compiled(compile_cmd, run_cmd, input_data, time_limit)
        else:
            cmd = ['python3', filepath]  # Default fallback
        
        # Execute for interpreted languages (Python)
        start_time = time.time()
        
        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=temp_dir,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Set timeout using communicate
            try:
                stdout, stderr = process.communicate(
                    input=input_data, 
                    timeout=time_limit
                )
                execution_time = time.time() - start_time
                
                if process.returncode == 0:
                    return {
                        'success': True,
                        'status': 'success',
                        'output': stdout.strip(),
                        'error': stderr.strip() if stderr else '',
                        'execution_time': execution_time,
                        'memory_used': 0  # Memory tracking not implemented yet
                    }
                else:
                    return {
                        'success': False,
                        'status': 'runtime_error',
                        'output': stdout.strip(),
                        'error': stderr.strip(),
                        'execution_time': execution_time,
                        'memory_used': 0
                    }
                    
            except subprocess.TimeoutExpired:
                # Kill the process group
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait()
                return {
                    'success': False,
                    'status': 'time_limit_exceeded',
                    'output': '',
                    'error': f'Time limit exceeded ({time_limit}s)',
                    'execution_time': time_limit,
                    'memory_used': 0
                }
                
        except Exception as e:
            return {
                'success': False,
                'status': 'error',
                'output': '',
                'error': str(e),
                'execution_time': time.time() - start_time,
                'memory_used': 0
            }
    
    def _execute_java(self, compile_cmd: List[str], run_cmd: List[str], 
                     input_data: str, time_limit: int) -> Dict[str, Any]:
        """Execute Java code with compilation step"""
        start_time = time.time()
        
        # Compile
        try:
            compile_process = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if compile_process.returncode != 0:
                return {
                    'status': 'compilation_error',
                    'output': '',
                    'error': compile_process.stderr,
                    'execution_time': time.time() - start_time,
                    'memory_used': 0
                }
        except subprocess.TimeoutExpired:
            return {
                'status': 'compilation_error',
                'output': '',
                'error': 'Compilation timeout',
                'execution_time': 10,
                'memory_used': 0
            }
        
        # Run
        try:
            process = subprocess.Popen(
                run_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid
            )
            
            stdout, stderr = process.communicate(input=input_data, timeout=time_limit)
            execution_time = time.time() - start_time
            
            if process.returncode == 0:
                return {
                    'status': 'success',
                    'output': stdout.strip(),
                    'error': stderr.strip() if stderr else '',
                    'execution_time': execution_time,
                    'memory_used': 0
                }
            else:
                return {
                    'status': 'runtime_error',
                    'output': stdout.strip(),
                    'error': stderr.strip(),
                    'execution_time': execution_time,
                    'memory_used': 0
                }
                
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait()
            return {
                'status': 'time_limit_exceeded',
                'output': '',
                'error': f'Time limit exceeded ({time_limit}s)',
                'execution_time': time_limit,
                'memory_used': 0
            }
    
    def _execute_compiled(self, compile_cmd: List[str], run_cmd: List[str], 
                         input_data: str, time_limit: int) -> Dict[str, Any]:
        """Execute compiled languages (C/C++)"""
        return self._execute_java(compile_cmd, run_cmd, input_data, time_limit)
    
    def _extract_java_classname(self, code: str) -> str:
        """Extract the main class name from Java code"""
        import re
        match = re.search(r'public\s+class\s+(\w+)', code)
        return match.group(1) if match else 'Main'
    
    def run_test_cases(self, code: str, language: str, test_cases: List[Tuple[str, str]], 
                      time_limit: int = 5) -> List[Dict[str, Any]]:
        """
        Run code against multiple test cases
        
        Args:
            code: Source code
            language: Programming language
            test_cases: List of (input, expected_output) tuples
            time_limit: Time limit per test case
            
        Returns:
            List of test results
        """
        results = []
        
        for i, (input_data, expected_output) in enumerate(test_cases):
            result = self.execute_code(code, language, input_data, time_limit)
            
            if result['status'] == 'success':
                actual_output = result['output'].strip()
                expected_output = expected_output.strip()
                
                if actual_output == expected_output:
                    test_result = {
                        'test_case': i + 1,
                        'status': 'passed',
                        'input': input_data,
                        'expected': expected_output,
                        'actual': actual_output,
                        'execution_time': result['execution_time'],
                        'error': ''
                    }
                else:
                    test_result = {
                        'test_case': i + 1,
                        'status': 'failed',
                        'input': input_data,
                        'expected': expected_output,
                        'actual': actual_output,
                        'execution_time': result['execution_time'],
                        'error': 'Wrong answer'
                    }
            else:
                test_result = {
                    'test_case': i + 1,
                    'status': 'error',
                    'input': input_data,
                    'expected': expected_output,
                    'actual': '',
                    'execution_time': result['execution_time'],
                    'error': result['error']
                }
            
            results.append(test_result)
        
        return results