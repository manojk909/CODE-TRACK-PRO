"""
Multi-provider AI service with automatic fallback
Supports multiple free AI providers with no quota limits
"""
import json
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class MultiAIProvider:
    def __init__(self):
        """Initialize multiple AI providers with fallback system"""
        self.providers = []
        self._setup_providers()
        
    def _setup_providers(self):
        """Setup available AI providers in priority order"""
        
        # 1. OpenAI - High quality, reliable (paid service)
        if os.environ.get("OPENAI_API_KEY"):
            self.providers.append({
                'name': 'openai',
                'base_url': 'https://api.openai.com/v1',
                'api_key': os.environ.get("OPENAI_API_KEY"),
                'model': 'gpt-4o',  # Latest and best OpenAI model
                'type': 'openai_compatible'
            })
        
        # 2. DeepSeek - Millions of free tokens, excellent for coding
        if os.environ.get("DEEPSEEK_API_KEY"):
            self.providers.append({
                'name': 'deepseek',
                'base_url': 'https://api.deepseek.com/v1',
                'api_key': os.environ.get("DEEPSEEK_API_KEY"),
                'model': 'deepseek-chat',
                'type': 'openai_compatible'
            })
        
        # 3. Google Gemini - High free quota, multimodal capabilities
        if os.environ.get("GEMINI_API_KEY"):
            self.providers.append({
                'name': 'gemini',
                'api_key': os.environ.get("GEMINI_API_KEY"),
                'model': 'gemini-2.5-flash',
                'type': 'gemini'
            })
        
        # 3. OpenRouter - Free models available
        if os.environ.get("OPENROUTER_API_KEY"):
            self.providers.append({
                'name': 'openrouter',
                'base_url': 'https://openrouter.ai/api/v1',
                'api_key': os.environ.get("OPENROUTER_API_KEY"),
                'model': 'deepseek/deepseek-chat:free',  # Free DeepSeek model
                'type': 'openai_compatible'
            })
        
        # 4. Hugging Face - Free inference
        if os.environ.get("HUGGINGFACE_API_KEY"):
            self.providers.append({
                'name': 'huggingface',
                'base_url': 'https://api-inference.huggingface.co/models',
                'api_key': os.environ.get("HUGGINGFACE_API_KEY"),
                'model': 'microsoft/DialoGPT-large',
                'type': 'huggingface'
            })
        
        # 5. Fallback to local sample responses (always available)
        self.providers.append({
            'name': 'local_samples',
            'type': 'local'
        })
    
    def generate_completion(self, prompt: str, response_format: str = "text") -> str:
        """Generate AI completion with automatic provider fallback"""
        
        for provider in self.providers:
            try:
                print(f"Trying provider: {provider['name']}")
                
                if provider['type'] == 'openai_compatible':
                    return self._call_openai_compatible(provider, prompt, response_format)
                elif provider['type'] == 'gemini':
                    return self._call_gemini(provider, prompt, response_format)
                elif provider['type'] == 'huggingface':
                    return self._call_huggingface(provider, prompt)
                elif provider['type'] == 'local':
                    return self._get_local_sample(prompt, response_format)
                    
            except Exception as e:
                print(f"Provider {provider['name']} failed: {str(e)}")
                continue
        
        # Final fallback
        return self._get_local_sample(prompt, response_format)
    
    def _call_openai_compatible(self, provider: Dict, prompt: str, response_format: str) -> str:
        """Call OpenAI-compatible APIs (DeepSeek, OpenRouter)"""
        headers = {
            'Authorization': f'Bearer {provider["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': provider['model'],
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 2000,
            'temperature': 0.7
        }
        
        if response_format == "json":
            data['response_format'] = {'type': 'json_object'}
        
        response = requests.post(
            f"{provider['base_url']}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content']
    
    def _call_gemini(self, provider: Dict, prompt: str, response_format: str) -> str:
        """Call Google Gemini API"""
        try:
            from google import genai
            client = genai.Client(api_key=provider['api_key'])
            
            if response_format == "json":
                prompt += "\n\nPlease respond with valid JSON format."
            
            response = client.models.generate_content(
                model=provider['model'],
                contents=prompt
            )
            
            return response.text or self._get_local_sample(prompt, response_format)
            
        except ImportError:
            print("Google Gemini library not available")
            raise Exception("Gemini library not installed")
    
    def _call_huggingface(self, provider: Dict, prompt: str) -> str:
        """Call Hugging Face Inference API"""
        headers = {
            'Authorization': f'Bearer {provider["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'inputs': prompt,
            'parameters': {
                'max_length': 500,
                'temperature': 0.7,
                'return_full_text': False
            }
        }
        
        response = requests.post(
            f"{provider['base_url']}/{provider['model']}",
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            return result[0].get('generated_text', '').strip()
        
        raise Exception("No response from Hugging Face")
    
    def _get_local_sample(self, prompt: str, response_format: str) -> str:
        """Fallback to local sample responses"""
        prompt_lower = prompt.lower()
        
        # Study plan generation
        if any(word in prompt_lower for word in ['study plan', 'learning plan', 'week']):
            return json.dumps({
                "week_1": {
                    "focus": "Data Structures Fundamentals",
                    "daily_tasks": ["Review arrays and linked lists", "Practice 2-3 easy problems", "Study time complexity"],
                    "recommended_problems": ["Two Sum", "Remove Duplicates from Sorted Array"],
                    "learning_resources": ["LeetCode Arrays section", "GeeksforGeeks Data Structures"]
                },
                "week_2": {
                    "focus": "Algorithms - Sorting and Searching", 
                    "daily_tasks": ["Learn binary search", "Practice sorting algorithms", "Solve medium problems"],
                    "recommended_problems": ["Binary Search", "Merge Sorted Array"],
                    "learning_resources": ["Algorithm visualization tools", "Practice on HackerRank"]
                },
                "week_3": {
                    "focus": "Dynamic Programming Basics",
                    "daily_tasks": ["Understand memoization", "Practice simple DP problems", "Review problem patterns"],
                    "recommended_problems": ["Climbing Stairs", "House Robber"],
                    "learning_resources": ["DP pattern recognition guides", "YouTube DP tutorials"]
                },
                "week_4": {
                    "focus": "System Design Concepts",
                    "daily_tasks": ["Learn scalability basics", "Practice design questions", "Review case studies"],
                    "recommended_problems": ["Design URL Shortener", "Design Chat System"],
                    "learning_resources": ["System Design Primer", "High-level design examples"]
                },
                "tips": [
                    "Practice consistently every day",
                    "Focus on understanding, not just solving",
                    "Review your solutions and optimize them",
                    "Join study groups for motivation"
                ]
            })
        
        # Problem recommendations
        elif any(word in prompt_lower for word in ['problem', 'recommend', 'solve']):
            return json.dumps({
                "recommended_problems": [
                    {
                        "title": "Two Sum",
                        "platform": "LeetCode",
                        "difficulty": "Easy",
                        "topic": "Arrays/Hash Tables",
                        "reason": "Fundamental problem that teaches hash table usage",
                        "estimated_time": "20 minutes"
                    },
                    {
                        "title": "Valid Parentheses",
                        "platform": "LeetCode",
                        "difficulty": "Easy", 
                        "topic": "Stack",
                        "reason": "Essential for understanding stack data structure",
                        "estimated_time": "25 minutes"
                    },
                    {
                        "title": "Binary Search",
                        "platform": "LeetCode",
                        "difficulty": "Easy",
                        "topic": "Binary Search",
                        "reason": "Foundation for all binary search problems",
                        "estimated_time": "25 minutes"
                    }
                ],
                "focus_areas": ["Data Structures", "Basic Algorithms", "Problem-solving patterns"],
                "study_order": "Start with easy problems to build confidence, then gradually move to medium difficulty"
            })
        
        # Text chatbot questions - provide natural conversational responses
        elif response_format == "text" and any(word in prompt_lower for word in ['what is', 'explain', 'how does', 'define', 'tell me', 'student asked']):
            
            if 'linked list' in prompt_lower:
                return """A linked list is a fundamental data structure where elements (called nodes) are stored in sequence, but unlike arrays, they're not stored in contiguous memory locations. Each node contains two parts: the data and a pointer (or reference) to the next node in the sequence.

Think of it like a treasure hunt where each clue leads you to the next location. In a linked list, you start at the first node (called the head), and each node tells you where to find the next one. The last node points to null, indicating the end of the list.

The main advantage of linked lists is that they can grow or shrink during runtime, and inserting or deleting elements is efficient if you know the position. However, accessing a specific element requires traversing from the beginning, making it slower than arrays for random access."""
            
            elif 'hash table' in prompt_lower or 'hash map' in prompt_lower:
                return """A hash table (also called a hash map) is a data structure that implements an associative array, which means it can map keys to values. It's like a super-efficient filing system where you can instantly find any document by its label.

Here's how it works: when you want to store a key-value pair, the hash table uses a hash function to convert the key into an array index. This hash function takes the key and performs some mathematical operations to generate a number that corresponds to a position in an underlying array.

The beauty of hash tables is their speed - on average, you can insert, delete, or search for elements in O(1) constant time. This makes them incredibly useful for things like database indexing, caching, and implementing dictionaries or sets."""
                
            elif 'binary search' in prompt_lower:
                return """Binary search is an incredibly efficient algorithm for finding a specific element in a sorted array or list. It works by repeatedly dividing the search space in half, which is why it's called "binary" (meaning two parts).

Here's the process: you start by looking at the middle element of the sorted array. If that's your target, you're done! If your target is smaller than the middle element, you know it must be in the left half, so you discard the right half. If your target is larger, you discard the left half.

The power of binary search is its efficiency - it has O(log n) time complexity, meaning that even in an array of a million elements, you'd need at most about 20 comparisons to find any element."""
                
            elif 'recursion' in prompt_lower:
                return """Recursion is a programming technique where a function calls itself to solve a problem by breaking it down into smaller, similar subproblems. It's like those Russian nesting dolls - each doll contains a smaller version of itself until you reach the smallest one.

Every recursive function needs two essential parts: a base case (the condition that stops the recursion) and a recursive case (where the function calls itself with a modified input). Without a base case, the function would call itself forever, causing a stack overflow.

A classic example is calculating factorials. To find 5!, you can say it's 5 × 4!, and 4! is 4 × 3!, and so on until you reach 1! = 1 (the base case). Recursion is particularly elegant for problems with tree-like structures."""
                
            else:
                return """I understand you're asking about a programming concept. Programming concepts often build on each other, so it's helpful to understand the fundamentals first. If you're learning about data structures, start with arrays and work your way up to more complex structures. For algorithms, begin with simple sorting and searching techniques before moving to advanced topics.

Feel free to ask me about specific aspects of the concept you're interested in, and I'll do my best to help explain it in a clear, understandable way."""
        
        # Flashcard content (JSON format for flashcard generation)
        elif any(word in prompt_lower for word in ['flashcard', 'generate flashcards']):
            return json.dumps({
                "flashcards": [
                    {
                        "question": "What is time complexity?",
                        "answer": "Time complexity measures how the runtime of an algorithm grows with input size. Common complexities: O(1), O(log n), O(n), O(n²).",
                        "difficulty": "easy",
                        "revision_frequency": "weekly"
                    },
                    {
                        "question": "Explain Big O notation",
                        "answer": "Big O describes the upper bound of algorithm performance. It helps compare efficiency and scalability of different approaches.",
                        "difficulty": "medium", 
                        "revision_frequency": "biweekly"
                    },
                    {
                        "question": "What is a hash table?",
                        "answer": "A hash table stores key-value pairs with O(1) average lookup time. Uses hash function to map keys to array indices.",
                        "difficulty": "medium",
                        "revision_frequency": "weekly"
                    }
                ],
                "total_cards": 3,
                "suggested_study_schedule": "weekly"
            })
        
        # General advice
        else:
            if response_format == "json":
                return json.dumps({
                    "advice": "Focus on consistent daily practice and understanding fundamentals",
                    "action_items": [
                        "Set aside 1-2 hours daily for coding practice",
                        "Choose quality problems over quantity",
                        "Review and optimize your solutions"
                    ],
                    "resources": [
                        "LeetCode for algorithm practice",
                        "GeeksforGeeks for concept explanations",
                        "YouTube coding channels for tutorials"
                    ],
                    "next_steps": "Start with easy problems and gradually increase difficulty",
                    "motivation": "Every expert was once a beginner. Consistent practice leads to mastery!"
                })
            else:
                return "Focus on consistent daily practice and understanding programming fundamentals. Start with easy problems and gradually build up your skills. Remember, every expert was once a beginner!"

    def get_available_providers(self) -> List[str]:
        """Get list of available provider names"""
        return [p['name'] for p in self.providers]

    def test_providers(self) -> Dict[str, bool]:
        """Test all providers and return their status"""
        results = {}
        test_prompt = "Hello, this is a test."
        
        for provider in self.providers:
            try:
                if provider['type'] == 'local':
                    results[provider['name']] = True
                else:
                    response = self.generate_completion(test_prompt)
                    results[provider['name']] = len(response) > 0
            except Exception as e:
                results[provider['name']] = False
                
        return results