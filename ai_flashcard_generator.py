import json
import os
from datetime import datetime, timedelta
from openai import OpenAI
from models import db, Flashcard

class AIFlashcardGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def generate_flashcards_for_topic(self, topic, user_id, difficulty_level="intermediate"):
        """
        Generate flashcards for a given topic using AI
        """
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

            response = self.client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert educational content creator specializing in creating effective flashcards for learning. Always respond with valid JSON."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )

            # Parse the AI response
            response_content = response.choices[0].message.content
            if response_content:
                ai_response = json.loads(response_content)
            else:
                raise Exception("Empty response from AI")
            
            # Save flashcards to database
            saved_flashcards = []
            for card_data in ai_response['flashcards']:
                flashcard = Flashcard()
                flashcard.user_id = user_id
                flashcard.topic = topic
                flashcard.question = card_data['question']
                flashcard.answer = card_data['answer']
                flashcard.category = topic  # Use topic as category
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
                'suggested_schedule': ai_response.get('suggested_study_schedule', 'weekly')
            }

        except Exception as e:
            print(f"Error generating flashcards: {str(e)}")
            
            # Fallback: Generate sample flashcards when API is unavailable
            if "quota" in str(e).lower() or "429" in str(e):
                return self._generate_sample_flashcards(topic, user_id, difficulty_level)
            
            return {
                'success': False,
                'error': str(e),
                'flashcards': [],
                'total_generated': 0
            }

    def _generate_sample_flashcards(self, topic, user_id, difficulty_level):
        """Generate sample flashcards when AI API is unavailable"""
        try:
            # Topic-specific sample flashcards
            sample_cards = self._get_topic_samples(topic, difficulty_level)
            
            saved_flashcards = []
            for card_data in sample_cards:
                flashcard = Flashcard()
                flashcard.user_id = user_id
                flashcard.topic = topic
                flashcard.question = card_data['question']
                flashcard.answer = card_data['answer']
                flashcard.category = topic
                flashcard.difficulty = card_data.get('difficulty', 'medium')
                flashcard.next_review = self._calculate_next_review('weekly')
                flashcard.is_ai_generated = False  # Mark as sample, not AI generated
                db.session.add(flashcard)
                saved_flashcards.append(flashcard)
            
            db.session.commit()
            
            return {
                'success': True,
                'flashcards': saved_flashcards,
                'total_generated': len(saved_flashcards),
                'suggested_schedule': 'weekly',
                'is_sample': True
            }
            
        except Exception as e:
            print(f"Error generating sample flashcards: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'flashcards': [],
                'total_generated': 0
            }

    def _get_topic_samples(self, topic, difficulty_level):
        """Get sample flashcards based on topic"""
        topic_lower = topic.lower()
        
        # Programming concepts samples
        if any(word in topic_lower for word in ['binary', 'tree', 'bst']):
            return [
                {
                    'question': 'What is a Binary Search Tree?',
                    'answer': 'A Binary Search Tree (BST) is a binary tree where for each node, all values in the left subtree are less than the node\'s value, and all values in the right subtree are greater than the node\'s value.',
                    'difficulty': 'easy'
                },
                {
                    'question': 'What is the time complexity of search operation in a balanced BST?',
                    'answer': 'O(log n) - In a balanced BST, we can eliminate half of the search space at each level, leading to logarithmic time complexity.',
                    'difficulty': 'medium'
                },
                {
                    'question': 'How do you perform an in-order traversal of a binary tree?',
                    'answer': 'In-order traversal: Visit left subtree, visit root, visit right subtree. For BST, this gives nodes in sorted order.',
                    'difficulty': 'medium'
                },
                {
                    'question': 'What happens to BST operations when the tree becomes unbalanced?',
                    'answer': 'In worst case (completely unbalanced), BST degenerates to a linked list, making operations O(n) instead of O(log n).',
                    'difficulty': 'hard'
                }
            ]
        
        elif any(word in topic_lower for word in ['react', 'hooks']):
            return [
                {
                    'question': 'What is useState hook in React?',
                    'answer': 'useState is a React Hook that allows you to add state to functional components. It returns an array with current state value and a function to update it.',
                    'difficulty': 'easy'
                },
                {
                    'question': 'What is useEffect hook used for?',
                    'answer': 'useEffect is used for side effects in functional components - data fetching, subscriptions, manual DOM changes. It runs after render and can clean up.',
                    'difficulty': 'medium'
                },
                {
                    'question': 'How do you prevent infinite re-renders with useEffect?',
                    'answer': 'Use dependency array as second argument to useEffect. Empty array [] runs once, specific dependencies run when they change.',
                    'difficulty': 'hard'
                }
            ]
        
        elif any(word in topic_lower for word in ['python', 'oop', 'object']):
            return [
                {
                    'question': 'What are the four pillars of Object-Oriented Programming?',
                    'answer': 'Encapsulation (bundling data and methods), Inheritance (deriving classes), Polymorphism (same interface, different implementations), Abstraction (hiding complexity).',
                    'difficulty': 'easy'
                },
                {
                    'question': 'What is the difference between @classmethod and @staticmethod in Python?',
                    'answer': '@classmethod receives class as first argument (cls), can access class attributes. @staticmethod doesn\'t receive class/instance, behaves like regular function.',
                    'difficulty': 'medium'
                },
                {
                    'question': 'Explain Python\'s Method Resolution Order (MRO)',
                    'answer': 'MRO determines order in which base classes are searched when executing a method. Python uses C3 linearization algorithm to ensure consistent inheritance.',
                    'difficulty': 'hard'
                }
            ]
        
        else:
            # Generic programming flashcards
            return [
                {
                    'question': f'What are the key concepts to understand in {topic}?',
                    'answer': f'The fundamental concepts in {topic} include understanding the core principles, practical applications, common patterns, and best practices.',
                    'difficulty': 'easy'
                },
                {
                    'question': f'How would you explain {topic} to a beginner?',
                    'answer': f'{topic} is an important concept in programming that helps solve specific problems efficiently. Start with basic examples and gradually build complexity.',
                    'difficulty': 'medium'
                },
                {
                    'question': f'What are common pitfalls when working with {topic}?',
                    'answer': f'Common mistakes include not understanding the fundamentals, skipping edge cases, and not following best practices. Always test thoroughly.',
                    'difficulty': 'medium'
                }
            ]

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

    def suggest_revision_schedule(self, topic, difficulty_level):
        """Get AI suggestion for revision schedule"""
        try:
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

            response = self.client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in learning science and spaced repetition. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )

            response_content = response.choices[0].message.content
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

    def get_due_flashcards(self, user_id):
        """Get flashcards that are due for review"""
        now = datetime.utcnow()
        return Flashcard.query.filter(
            Flashcard.user_id == user_id,
            Flashcard.next_review <= now
        ).all()

    def update_flashcard_after_review(self, flashcard_id, quality_rating):
        """Update flashcard after review based on quality (1-5 scale)"""
        flashcard = Flashcard.query.get(flashcard_id)
        if not flashcard:
            return False

        # Update review stats
        flashcard.review_count += 1
        flashcard.last_reviewed = datetime.utcnow()

        # Calculate next review based on quality and current ease factor
        if quality_rating >= 4:  # Good recall
            if flashcard.ease_factor:
                flashcard.ease_factor += 0.1
            else:
                flashcard.ease_factor = 2.5
            interval_multiplier = flashcard.ease_factor
        elif quality_rating >= 3:  # OK recall
            interval_multiplier = 1.0
        else:  # Poor recall
            if flashcard.ease_factor:
                flashcard.ease_factor = max(1.3, flashcard.ease_factor - 0.2)
            else:
                flashcard.ease_factor = 1.3
            interval_multiplier = 0.5

        # Calculate next review date
        current_interval = 7  # Start with 1 week
        if flashcard.review_count > 1:
            current_interval = int(current_interval * interval_multiplier)

        flashcard.next_review = datetime.utcnow() + timedelta(days=current_interval)
        
        db.session.commit()
        return True