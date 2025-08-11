import json
import os
from datetime import datetime, timedelta
from models import db, Flashcard
from ai_providers import MultiAIProvider

class EnhancedAIFlashcardGenerator:
    def __init__(self):
        self.multi_ai = MultiAIProvider()  # Free AI providers with unlimited quota

    def generate_flashcards_for_topic(self, topic, user_id, difficulty_level="intermediate"):
        """Generate flashcards using free AI providers with fallback"""
        try:
            # Create a prompt for generating flashcards
            prompt = f"""
            Create educational flashcards for the topic: "{topic}"
            
            Requirements:
            - Generate 5-15 flashcards based on topic complexity
            - Include fundamental concepts, key terms, practical examples, and problem-solving questions
            - Make questions clear and concise
            - Provide comprehensive but not overwhelming answers
            - Difficulty level: {difficulty_level}
            - Include a mix of: definitions, explanations, examples, and application questions
            
            Return a JSON object with this structure:
            {{
                "flashcards": [
                    {{
                        "question": "Clear, specific question",
                        "answer": "Comprehensive answer with examples if needed",
                        "difficulty": "easy|medium|hard",
                        "revision_frequency": "weekly|biweekly|monthly"
                    }}
                ],
                "total_cards": number,
                "suggested_study_schedule": "weekly|biweekly|monthly"
            }}
            
            Make sure each flashcard is educational and helps with understanding the topic.
            """

            # Use multi-provider AI system
            response_content = self.multi_ai.generate_completion(prompt, "json")
            
            if not response_content:
                raise Exception("Empty response from AI")
            
            # Clean the response content to handle potential formatting issues
            response_content = response_content.strip()
            
            # Try to extract JSON if it's wrapped in markdown code blocks
            if response_content.startswith('```json'):
                response_content = response_content.replace('```json', '').replace('```', '').strip()
            elif response_content.startswith('```'):
                response_content = response_content.replace('```', '').strip()
            
            try:
                ai_response = json.loads(response_content)
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                print(f"Raw response: {response_content}")
                # Try to create a fallback response
                raise Exception(f"Failed to parse AI response as JSON: {str(e)}")
            
            # Save flashcards to database
            saved_flashcards = []
            for card_data in ai_response['flashcards']:
                flashcard = Flashcard()
                flashcard.user_id = user_id
                flashcard.topic = topic
                flashcard.question = card_data['question']
                flashcard.answer = card_data['answer']
                flashcard.category = topic
                flashcard.difficulty = card_data.get('difficulty', 'medium')
                flashcard.next_review = self._calculate_next_review(card_data.get('revision_frequency', 'weekly'))
                flashcard.is_ai_generated = True
                db.session.add(flashcard)
                saved_flashcards.append(flashcard)
            
            db.session.commit()
            
            return {
                'success': True,
                'flashcards': saved_flashcards,
                'total_generated': len(saved_flashcards),
                'suggested_schedule': ai_response.get('suggested_study_schedule', 'weekly'),
                'provider_used': 'multi_ai'
            }

        except Exception as e:
            print(f"Error generating flashcards: {str(e)}")
            
            # Fallback to creating sample flashcards for the topic
            try:
                fallback_flashcards = self._create_fallback_flashcards(topic, user_id, difficulty_level)
                if fallback_flashcards:
                    return {
                        'success': True,
                        'flashcards': fallback_flashcards,
                        'total_generated': len(fallback_flashcards),
                        'suggested_schedule': 'weekly',
                        'provider_used': 'fallback',
                        'note': 'Used fallback flashcards due to AI generation error'
                    }
            except Exception as fallback_error:
                print(f"Fallback also failed: {fallback_error}")
            
            return {
                'success': False,
                'error': str(e),
                'flashcards': [],
                'total_generated': 0
            }

    def _calculate_next_review(self, frequency):
        """Calculate next review date based on frequency"""
        now = datetime.utcnow()
        if frequency == 'weekly':
            return now + timedelta(weeks=1)
        elif frequency == 'biweekly':
            return now + timedelta(weeks=2)
        elif frequency == 'monthly':
            return now + timedelta(weeks=4)
        else:
            return now + timedelta(weeks=1)  # Default to weekly
    
    def _create_fallback_flashcards(self, topic, user_id, difficulty_level):
        """Create fallback flashcards when AI generation fails"""
        # Sample flashcard templates based on common programming topics
        fallback_templates = {
            'python': [
                {
                    'question': f'What is the basic syntax of a for loop in Python?',
                    'answer': 'for item in iterable:\n    # code block\nExample: for i in range(5):\n    print(i)',
                    'difficulty': 'easy'
                },
                {
                    'question': f'How do you define a function in Python?',
                    'answer': 'def function_name(parameters):\n    # function body\n    return value',
                    'difficulty': 'easy'
                },
                {
                    'question': f'What are Python lists and how do you create them?',
                    'answer': 'Lists are ordered, mutable collections. Create with: my_list = [1, 2, 3] or my_list = list()',
                    'difficulty': 'easy'
                }
            ],
            'javascript': [
                {
                    'question': f'What is the difference between let, const, and var in JavaScript?',
                    'answer': 'let: block-scoped, reassignable; const: block-scoped, not reassignable; var: function-scoped, reassignable',
                    'difficulty': 'medium'
                },
                {
                    'question': f'How do you define a function in JavaScript?',
                    'answer': 'function myFunction(params) { return value; } or const myFunction = (params) => { return value; }',
                    'difficulty': 'easy'
                }
            ],
            'default': [
                {
                    'question': f'What is {topic}?',
                    'answer': f'{topic} is a fundamental concept in programming that involves understanding key principles and practical applications.',
                    'difficulty': 'medium'
                },
                {
                    'question': f'How is {topic} commonly used?',
                    'answer': f'{topic} is commonly used to solve specific programming problems and implement efficient solutions.',
                    'difficulty': 'medium'
                },
                {
                    'question': f'What are the key benefits of understanding {topic}?',
                    'answer': f'Understanding {topic} helps improve coding skills, problem-solving abilities, and software development efficiency.',
                    'difficulty': 'easy'
                }
            ]
        }
        
        # Select appropriate templates
        topic_lower = topic.lower()
        if 'python' in topic_lower:
            templates = fallback_templates['python']
        elif 'javascript' in topic_lower or 'js' in topic_lower:
            templates = fallback_templates['javascript']
        else:
            templates = fallback_templates['default']
        
        # Create flashcards from templates
        fallback_flashcards = []
        for template in templates:
            flashcard = Flashcard()
            flashcard.user_id = user_id
            flashcard.topic = topic
            flashcard.question = template['question']
            flashcard.answer = template['answer']
            flashcard.category = topic
            flashcard.difficulty = template['difficulty']
            flashcard.next_review = self._calculate_next_review('weekly')
            flashcard.is_ai_generated = True
            db.session.add(flashcard)
            fallback_flashcards.append(flashcard)
        
        db.session.commit()
        return fallback_flashcards

    def suggest_revision_schedule(self, topic, difficulty_level):
        """Get AI suggestion for revision schedule using free providers"""
        prompt = f"""
        For the topic "{topic}" with difficulty level "{difficulty_level}", 
        suggest an optimal revision schedule. Consider:
        - Topic complexity
        - Typical retention patterns
        - Spaced repetition principles
        
        Return JSON with:
        {{
            "recommended_frequency": "weekly|biweekly|monthly",
            "reasoning": "Brief explanation",
            "initial_review": "1-3 days",
            "subsequent_reviews": "schedule pattern"
        }}
        """

        try:
            response_content = self.multi_ai.generate_completion(prompt, "json")
            if response_content:
                return json.loads(response_content)
            else:
                raise Exception("Empty response from AI")
        except Exception as e:
            print(f"Error getting revision schedule: {str(e)}")
            return {
                "recommended_frequency": "weekly",
                "reasoning": "Default weekly schedule for consistent learning",
                "initial_review": "2-3 days",
                "subsequent_reviews": "Weekly intervals"
            }

    def get_topics_by_user(self, user_id):
        """Get all unique topics for a user"""
        from sqlalchemy import text
        topics = db.session.execute(
            text("SELECT DISTINCT topic FROM flashcard WHERE user_id = :user_id"),
            {"user_id": user_id}
        ).fetchall()
        return [topic[0] for topic in topics]

    def get_flashcards_by_topic(self, user_id, topic):
        """Get all flashcards for a specific topic"""
        return Flashcard.query.filter_by(user_id=user_id, topic=topic).all()
    
    def enhance_flashcard_content(self, flashcard_id, user_feedback=""):
        """Enhance existing flashcard content using AI"""
        flashcard = Flashcard.query.get(flashcard_id)
        if not flashcard:
            return {"success": False, "error": "Flashcard not found"}
        
        prompt = f"""
        Enhance this flashcard content based on user feedback:
        
        Current Question: {flashcard.question}
        Current Answer: {flashcard.answer}
        Topic: {flashcard.topic}
        User Feedback: {user_feedback}
        
        Provide improved content in JSON format:
        {{
            "improved_question": "Enhanced question",
            "improved_answer": "Enhanced answer with better explanations",
            "suggested_difficulty": "easy|medium|hard"
        }}
        """
        
        try:
            response_content = self.multi_ai.generate_completion(prompt, "json")
            if response_content:
                result = json.loads(response_content)
                return {
                    "success": True,
                    "suggestions": result
                }
        except Exception as e:
            print(f"Error enhancing flashcard: {str(e)}")
        
        return {"success": False, "error": "Could not enhance flashcard"}
    
    def test_ai_providers(self):
        """Test available AI providers"""
        return self.multi_ai.test_providers()
    
    def get_available_providers(self):
        """Get list of available AI providers"""
        return self.multi_ai.get_available_providers()