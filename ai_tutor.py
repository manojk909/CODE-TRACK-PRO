import os
import json
from openai import OpenAI
from models import User, PlatformStats, ProblemSolved
from app import db
from ai_providers import MultiAIProvider

class AITutor:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
        self.multi_ai = MultiAIProvider()  # Free AI providers with no limits
        
    def get_recommendation(self, user_id, recommendation_type, user_query=""):
        """Generate AI-powered recommendations for users"""
        user = User.query.get(user_id)
        if not user:
            return "User not found"
        
        # Get user's coding data for context
        platform_stats = PlatformStats.query.filter_by(user_id=user_id).all()
        recent_problems = ProblemSolved.query.filter_by(user_id=user_id).order_by(ProblemSolved.solved_at.desc()).limit(10).all()
        
        # Build context about user's progress
        context = self._build_user_context(user, platform_stats, recent_problems)
        
        # Generate recommendation based on type
        if recommendation_type == 'study_plan':
            return self._generate_study_plan(context, user_query)
        elif recommendation_type == 'problem':
            return self._recommend_problems(context, user_query)
        elif recommendation_type == 'topic':
            return self._recommend_topics(context, user_query)
        elif recommendation_type == 'weakness':
            return self._identify_weaknesses(context, user_query)
        else:
            return self._general_recommendation(context, user_query)
    
    def _build_user_context(self, user, platform_stats, recent_problems):
        """Build context string about user's coding journey"""
        context = f"User: {user.username}\n"
        context += f"Learning Goals: {user.learning_goals or 'Not specified'}\n"
        context += f"Target Companies: {user.target_companies or 'Not specified'}\n"
        
        # Platform statistics
        if platform_stats:
            context += "\nPlatform Progress:\n"
            for stat in platform_stats:
                context += f"- {stat.platform}: {stat.total_problems} problems solved "
                context += f"(Easy: {stat.easy_solved}, Medium: {stat.medium_solved}, Hard: {stat.hard_solved})\n"
        
        # Recent problem-solving patterns
        if recent_problems:
            context += "\nRecent Problems Solved:\n"
            for problem in recent_problems[:5]:
                context += f"- {problem.problem.title if problem.problem else 'Unknown'} "
                context += f"({problem.problem.difficulty if problem.problem else 'Unknown'} - "
                context += f"{problem.problem.category if problem.problem else 'Unknown'})\n"
        
        return context
    
    def _generate_study_plan(self, context, user_query):
        """Generate a personalized study plan"""
        try:
            prompt = f"""Based on the following user profile and coding progress, create a personalized 4-week study plan.
            Focus on areas that need improvement and align with their goals.
            
            User Context:
            {context}
            
            Additional Requirements: {user_query}
            
            Please provide a detailed study plan in JSON format with the following structure:
            {{
                "week_1": {{
                    "focus": "main topic to focus on",
                    "daily_tasks": ["task1", "task2", "task3"],
                    "recommended_problems": ["problem1", "problem2"],
                    "learning_resources": ["resource1", "resource2"]
                }},
                "week_2": {{ ... }},
                "week_3": {{ ... }},
                "week_4": {{ ... }},
                "tips": ["general study tip1", "tip2"]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
        except Exception as e:
            if "quota" in str(e).lower() or "429" in str(e):
                # Provide fallback study plan when quota exceeded
                return self._get_fallback_study_plan()
            return f"Error generating study plan: {str(e)}"
    
    def _recommend_problems(self, context, user_query):
        """Recommend specific problems to solve"""
        try:
            prompt = f"""Based on the user's coding progress, recommend 10 specific coding problems they should solve next.
            Consider their current skill level and areas that need improvement.
            
            User Context:
            {context}
            
            Specific Request: {user_query}
            
            Provide recommendations in JSON format:
            {{
                "recommended_problems": [
                    {{
                        "title": "Problem Title",
                        "platform": "LeetCode/GeeksforGeeks/HackerRank",
                        "difficulty": "Easy/Medium/Hard",
                        "topic": "Data Structures/Algorithms/etc",
                        "reason": "Why this problem is recommended",
                        "estimated_time": "30 minutes"
                    }}
                ],
                "focus_areas": ["area1", "area2"],
                "study_order": "suggested order explanation"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error recommending problems: {str(e)}"
    
    def _recommend_topics(self, context, user_query):
        """Recommend topics to study"""
        try:
            prompt = f"""Based on the user's progress, recommend computer science topics they should study next.
            Prioritize topics that will help them achieve their goals.
            
            User Context:
            {context}
            
            Specific Request: {user_query}
            
            Provide topic recommendations in JSON format:
            {{
                "priority_topics": [
                    {{
                        "topic": "Topic Name",
                        "importance": "High/Medium/Low",
                        "reason": "Why this topic is important",
                        "learning_resources": ["resource1", "resource2"],
                        "practice_problems": ["problem type1", "problem type2"],
                        "estimated_study_time": "2 weeks"
                    }}
                ],
                "learning_path": "suggested order of topics",
                "quick_wins": ["topics that can be learned quickly"]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error recommending topics: {str(e)}"
    
    def _identify_weaknesses(self, context, user_query):
        """Identify weak areas and suggest improvements"""
        try:
            prompt = f"""Analyze the user's coding progress and identify their weak areas.
            Provide specific suggestions for improvement.
            
            User Context:
            {context}
            
            Additional Information: {user_query}
            
            Provide analysis in JSON format:
            {{
                "identified_weaknesses": [
                    {{
                        "area": "Weakness area",
                        "evidence": "What indicates this weakness",
                        "impact": "How this affects their progress",
                        "improvement_plan": "Specific steps to improve"
                    }}
                ],
                "strengths": ["area1", "area2"],
                "improvement_priority": "which weakness to tackle first",
                "timeline": "expected improvement timeline"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
        except Exception as e:
            if "quota" in str(e).lower() or "429" in str(e):
                return self._get_fallback_weakness_analysis()
            return f"Error identifying weaknesses: {str(e)}"
    
    def _general_recommendation(self, context, user_query):
        """Provide general coding advice"""
        try:
            prompt = f"""Provide personalized coding advice and recommendations based on the user's profile.
            
            User Context:
            {context}
            
            User Question: {user_query}
            
            Provide advice in JSON format:
            {{
                "advice": "main advice or answer to their question",
                "action_items": ["specific action1", "action2", "action3"],
                "resources": ["helpful resource1", "resource2"],
                "next_steps": "what they should do next",
                "motivation": "encouraging message"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
        except Exception as e:
            if "quota" in str(e).lower() or "429" in str(e):
                return self._get_fallback_general_advice()
            return f"Error generating recommendation: {str(e)}"
    
    def chat_with_tutor(self, user_id, message):
        """Interactive chat with AI tutor"""
        user = User.query.get(user_id)
        if not user:
            return "User not found"
        
        try:
            # Get recent context
            platform_stats = PlatformStats.query.filter_by(user_id=user_id).all()
            context = self._build_user_context(user, platform_stats, [])
            
            prompt = f"""You are an AI coding tutor helping a student with their programming journey.
            Here's their profile:
            {context}
            
            Student Question: {message}
            
            Provide a helpful, encouraging, and educational response. Include specific examples or code snippets when appropriate.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            if "quota" in str(e).lower() or "429" in str(e):
                return "I'm currently experiencing high demand. Please try asking your question again later, or check out our study resources and flashcards for continued learning!"
            return f"I'm sorry, I encountered an error while processing your question: {str(e)}"
    
    # Fallback methods when API quota exceeded
    def _get_fallback_study_plan(self):
        """Provide a sample study plan when API quota exceeded"""
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
    
    def _get_fallback_problems(self):
        """Provide sample problem recommendations when API quota exceeded"""
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
                    "title": "Merge Two Sorted Lists",
                    "platform": "LeetCode",
                    "difficulty": "Easy",
                    "topic": "Linked Lists",
                    "reason": "Core linked list manipulation practice",
                    "estimated_time": "30 minutes"
                },
                {
                    "title": "Binary Search",
                    "platform": "LeetCode",
                    "difficulty": "Easy",
                    "topic": "Binary Search",
                    "reason": "Foundation for all binary search problems",
                    "estimated_time": "25 minutes"
                },
                {
                    "title": "Maximum Subarray",
                    "platform": "LeetCode",
                    "difficulty": "Medium",
                    "topic": "Dynamic Programming",
                    "reason": "Introduction to dynamic programming concepts",
                    "estimated_time": "40 minutes"
                }
            ],
            "focus_areas": ["Data Structures", "Basic Algorithms", "Problem-solving patterns"],
            "study_order": "Start with easy problems to build confidence, then gradually move to medium difficulty. Focus on understanding the underlying patterns."
        })
    
    def _get_fallback_weakness_analysis(self):
        """Provide sample weakness analysis when API quota exceeded"""
        return json.dumps({
            "identified_weaknesses": [
                {
                    "area": "Dynamic Programming",
                    "evidence": "Limited practice with optimization problems",
                    "impact": "May struggle with complex algorithmic challenges",
                    "improvement_plan": "Start with simple DP problems, practice memoization, study common patterns"
                },
                {
                    "area": "System Design",
                    "evidence": "Need more exposure to scalability concepts",
                    "impact": "Important for technical interviews and real-world applications",
                    "improvement_plan": "Study distributed systems basics, practice design questions, review case studies"
                }
            ],
            "strengths": ["Problem-solving persistence", "Basic data structure knowledge"],
            "improvement_priority": "Focus on Dynamic Programming first as it builds algorithmic thinking",
            "timeline": "2-3 months of consistent practice should show significant improvement"
        })
    
    def _get_fallback_general_advice(self):
        """Provide general advice when API quota exceeded"""
        return json.dumps({
            "advice": "Focus on consistent daily practice and understanding fundamentals rather than trying to solve as many problems as possible",
            "action_items": [
                "Set aside 1-2 hours daily for coding practice",
                "Choose quality problems over quantity", 
                "Review and optimize your solutions",
                "Join coding communities for support"
            ],
            "resources": [
                "LeetCode for algorithm practice",
                "System Design Primer for architecture",
                "GeeksforGeeks for concept explanations",
                "YouTube coding channels for tutorials"
            ],
            "next_steps": "Start with easy problems in your weak areas and gradually increase difficulty",
            "motivation": "Every expert was once a beginner. Consistent practice and patience will lead to mastery!"
        })
