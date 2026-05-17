"""
Smart Study Assistant Quiz Generator
Auto-generates quizzes based on learning content
"""
import json
import random
from typing import Dict, List, Any, Optional
from .ai_summarizer import AISummarizer

class QuizGenerator:
    """Generates various types of quizzes automatically"""
    
    def __init__(self):
        self.ai_summarizer = AISummarizer()
    
    def generate_quiz(self, content: str, subject: str, quiz_type: str = "mixed", 
                     num_questions: int = 5, difficulty: str = "medium") -> Dict[str, Any]:
        """
        Generate quiz questions based on content
        
        Args:
            content: Learning content to base quiz on
            subject: Subject area
            quiz_type: Type of quiz (multiple_choice, true_false, short_answer, mixed)
            num_questions: Number of questions to generate
            difficulty: Difficulty level (easy, medium, hard)
            
        Returns:
            Dictionary with quiz questions and metadata
        """
        try:
            prompt = self._create_quiz_prompt(content, subject, quiz_type, num_questions, difficulty)
            
            # Use AI to generate quiz
            response = self.ai_summarizer.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert educational content creator. Generate high-quality quiz questions based on the provided content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            quiz_content = response.choices[0].message.content.strip()
            
            # Parse the quiz content
            quiz_data = self._parse_quiz_content(quiz_content, quiz_type)
            
            return {
                'success': True,
                'quiz_type': quiz_type,
                'subject': subject,
                'difficulty': difficulty,
                'num_questions': len(quiz_data['questions']),
                'questions': quiz_data['questions'],
                'total_points': quiz_data['total_points'],
                'estimated_time': self._estimate_time(quiz_data['questions'])
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Quiz generation failed: {str(e)}",
                'questions': []
            }
    
    def _create_quiz_prompt(self, content: str, subject: str, quiz_type: str, 
                           num_questions: int, difficulty: str) -> str:
        """Create prompt for quiz generation"""
        
        difficulty_instructions = {
            "easy": "focus on basic definitions and simple concepts",
            "medium": "include both conceptual understanding and application",
            "hard": "focus on complex analysis, synthesis, and evaluation"
        }
        
        type_instructions = {
            "multiple_choice": "Generate multiple choice questions with 4 options (A, B, C, D) where only one is correct",
            "true_false": "Generate true/false questions with clear answers",
            "short_answer": "Generate questions that require brief written responses (1-2 sentences)",
            "fill_blank": "Generate fill-in-the-blank questions with missing key terms",
            "mixed": "Generate a mix of different question types"
        }
        
        prompt = f"""
Generate a {num_questions}-question quiz for {subject} based on the following content.

Content:
{content[:2000]}  # Limit content to avoid token limits

Requirements:
- Difficulty level: {difficulty} ({difficulty_instructions.get(difficulty, '')})
- Question type: {quiz_type} ({type_instructions.get(quiz_type, '')})
- Each question should test important concepts from the content
- Provide clear, unambiguous questions

Format your response as JSON:
{{
    "questions": [
        {{
            "id": 1,
            "type": "multiple_choice|true_false|short_answer|fill_blank",
            "question": "The question text",
            "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],  // for multiple choice
            "correct_answer": "A",  // for multiple choice, or "true"/"false", or the answer text
            "points": 1,
            "explanation": "Brief explanation of why this is correct"
        }}
    ]
}}

Make sure all questions are directly answerable from the provided content.
"""
        return prompt
    
    def _parse_quiz_content(self, quiz_content: str, expected_type: str) -> Dict:
        """Parse AI-generated quiz content"""
        try:
            # Try to extract JSON from the response
            if "```json" in quiz_content:
                json_start = quiz_content.find("```json") + 7
                json_end = quiz_content.find("```", json_start)
                json_content = quiz_content[json_start:json_end].strip()
            elif "{" in quiz_content and "}" in quiz_content:
                json_start = quiz_content.find("{")
                json_end = quiz_content.rfind("}") + 1
                json_content = quiz_content[json_start:json_end].strip()
            else:
                raise ValueError("No JSON found in response")
            
            quiz_data = json.loads(json_content)
            
            # Validate and clean the data
            questions = []
            total_points = 0
            
            for i, q in enumerate(quiz_data.get('questions', []), 1):
                question = {
                    'id': q.get('id', i),
                    'type': q.get('type', expected_type),
                    'question': q.get('question', ''),
                    'points': q.get('points', 1),
                    'explanation': q.get('explanation', ''),
                    'correct_answer': q.get('correct_answer', '')
                }
                
                # Add options if multiple choice
                if question['type'] == 'multiple_choice' and 'options' in q:
                    question['options'] = q['options']
                
                questions.append(question)
                total_points += question['points']
            
            return {
                'questions': questions,
                'total_points': total_points
            }
            
        except Exception as e:
            # Fallback: create basic questions if parsing fails
            return self._create_fallback_quiz(expected_type)
    
    def _create_fallback_quiz(self, quiz_type: str) -> Dict:
        """Create basic fallback quiz if AI generation fails"""
        fallback_questions = [
            {
                'id': 1,
                'type': quiz_type,
                'question': 'What is the main topic of this content?',
                'correct_answer': 'Refer to the content material',
                'points': 1,
                'explanation': 'Review the main concepts covered'
            }
        ]
        
        if quiz_type == 'multiple_choice':
            fallback_questions[0]['options'] = [
                'A. First option',
                'B. Second option', 
                'C. Third option',
                'D. Fourth option'
            ]
            fallback_questions[0]['correct_answer'] = 'A'
        
        return {
            'questions': fallback_questions,
            'total_points': 1
        }
    
    def _estimate_time(self, questions: List[Dict]) -> int:
        """Estimate time needed to complete quiz (in minutes)"""
        time_per_question = {
            'multiple_choice': 1,
            'true_false': 0.5,
            'short_answer': 2,
            'fill_blank': 1
        }
        
        total_time = 0
        for q in questions:
            q_type = q.get('type', 'multiple_choice')
            total_time += time_per_question.get(q_type, 1) * q.get('points', 1)
        
        return max(1, total_time)
    
    def evaluate_quiz(self, questions: List[Dict], user_answers: List[str]) -> Dict:
        """
        Evaluate quiz answers and calculate score
        
        Args:
            questions: List of quiz questions
            user_answers: List of user answers
            
        Returns:
            Dictionary with evaluation results
        """
        if len(questions) != len(user_answers):
            return {
                'success': False,
                'error': 'Number of answers does not match number of questions'
            }
        
        results = []
        correct_count = 0
        total_points = 0
        earned_points = 0
        
        for i, (question, user_answer) in enumerate(zip(questions, user_answers)):
            correct_answer = question['correct_answer']
            is_correct = self._check_answer(question, user_answer, correct_answer)
            
            if is_correct:
                correct_count += 1
                earned_points += question['points']
            
            total_points += question['points']
            
            results.append({
                'question_id': question['id'],
                'question': question['question'],
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'points': question['points'],
                'earned_points': earned_points if is_correct else 0,
                'explanation': question['explanation']
            })
        
        score = (earned_points / total_points) * 100 if total_points > 0 else 0
        
        return {
            'success': True,
            'score': score,
            'correct_count': correct_count,
            'total_questions': len(questions),
            'total_points': total_points,
            'earned_points': earned_points,
            'results': results,
            'grade': self._calculate_grade(score)
        }
    
    def _check_answer(self, question: Dict, user_answer: str, correct_answer: str) -> bool:
        """Check if user answer is correct"""
        user_clean = user_answer.strip().lower()
        correct_clean = correct_answer.strip().lower()
        
        if question['type'] == 'multiple_choice':
            return user_clean == correct_clean
        elif question['type'] == 'true_false':
            return user_clean in ['true', 't', 'yes'] and correct_clean in ['true', 't', 'yes'] or \
                   user_clean in ['false', 'f', 'no'] and correct_clean in ['false', 'f', 'no']
        else:
            # For short answer and fill blank, be more lenient
            return correct_clean in user_clean or user_clean in correct_clean
    
    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade based on percentage score"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def generate_adaptive_quiz(self, session_progress: Dict, subject: str) -> Dict:
        """
        Generate adaptive quiz based on user's progress
        
        Args:
            session_progress: User's learning progress data
            subject: Subject area
            
        Returns:
            Adaptive quiz configuration
        """
        # Analyze weak areas from progress
        weak_topics = []
        for progress in session_progress.get('learning_progress', []):
            if progress['subject'] == subject and progress['mastery_level'] < 0.7:
                weak_topics.append(progress['topic'])
        
        # Determine difficulty based on average performance
        avg_score = 0
        quiz_count = 0
        for stat in session_progress.get('quiz_statistics', []):
            if stat['subject'] == subject:
                avg_score += stat['average_score']
                quiz_count += 1
        
        if quiz_count > 0:
            avg_score /= quiz_count
            difficulty = "hard" if avg_score > 80 else "medium" if avg_score > 60 else "easy"
        else:
            difficulty = "medium"
        
        # Focus on weak areas
        if weak_topics:
            quiz_type = "mixed"  # Use mixed types for comprehensive review
            num_questions = min(8, len(weak_topics) * 2)
        else:
            quiz_type = "multiple_choice"  # Quick review if no weak areas
            num_questions = 5
        
        return {
            'difficulty': difficulty,
            'quiz_type': quiz_type,
            'num_questions': num_questions,
            'focus_topics': weak_topics,
            'adaptive_reasoning': f"Based on your average score of {avg_score:.1f}% and {len(weak_topics)} areas needing improvement"
        }
